# Copyright (c) 2015 Orange.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from sqlalchemy.orm import exc
from sqlalchemy import sql

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.common import constants as const
from neutron import context as n_context
from neutron.db import models_v2
from neutron.extensions import portbindings
from neutron.i18n import _LE
from neutron import manager

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_bagpipe.agent.bgpvpn import rpc_client

from networking_bgpvpn.neutron.services.common import utils
from networking_bgpvpn.neutron.services.service_drivers import driver_api

LOG = logging.getLogger(__name__)


def get_network_info_for_port(context, port_id):
    """Get MAC, IP and Gateway IP addresses informations for a specific port"""

    LOG.debug("get_network_info_for_port() called for port %s" % port_id)
    try:
        with context.session.begin(subtransactions=True):
            net_info = (context.session.
                        query(models_v2.Port.mac_address,
                              models_v2.IPAllocation.ip_address,
                              models_v2.Subnet.cidr,
                              models_v2.Subnet.gateway_ip).
                        join(models_v2.IPAllocation).
                        join(models_v2.Subnet,
                             models_v2.IPAllocation.subnet_id ==
                             models_v2.Subnet.id).
                        filter(models_v2.Port.id == port_id).one())

            (mac_address, ip_address, cidr, gateway_ip) = net_info

            return {'mac_address': mac_address,
                    'ip_address': ip_address + cidr[cidr.index('/'):],
                    'gateway_ip': gateway_ip}
    except exc.NoResultFound:
        return


def get_network_ports(context, network_id):
    try:
        return (context.session.query(models_v2.Port).
                filter(models_v2.Port.network_id == network_id,
                       models_v2.Port.admin_state_up == sql.true()).all())
    except exc.NoResultFound:
        return


class BaGPipeBGPVPNDriver(driver_api.BGPVPNDriver):

    """BGPVPN Service Driver class for BaGPipe"""

    def __init__(self, service_plugin):
        super(BaGPipeBGPVPNDriver, self).__init__(service_plugin)

        self.agent_rpc = rpc_client.BGPVPNAgentNotifyApi()

        registry.subscribe(self.registry_port_updated, resources.PORT,
                           events.AFTER_UPDATE)

        # we need to subscribe to before_delete events, because
        # on after_delete events the port is already removed from the db
        # and we can't retrieve the binding:host_id information (which
        # is not passed in the event either)
        registry.subscribe(self.registry_port_deleted, resources.PORT,
                           events.BEFORE_DELETE)

        # REVISIT(tmorin): if/when port ABORT_DELETE events are implemented
        #  we will have to revisit the issue, so that the action done after
        #  BEFORE_DELETE is reverted if needed (or a different solution)

    def _format_bgpvpn(self, bgpvpn, network_id):
        """JSON-format BGPVPN

        BGPVPN, network identifiers, and route targets.
        """
        formatted_bgpvpn = {'id': bgpvpn['id'],
                            'network_id': network_id}
        formatted_bgpvpn.update(
            self._format_bgpvpn_network_route_targets([bgpvpn]))

        return formatted_bgpvpn

    def _format_bgpvpn_network_route_targets(self, bgpvpns):
        """Format BGPVPN network informations (VPN type and route targets)

        {
            'type': 'l3',
            'route_targets': ['12345:1', '12345:2'],
            'import_targets': ['12345:3'],
            'export_targets': ['12345:4']
        }

        to

        {
            'l3vpn' : {
                'import_rt': ['12345:1', '12345:2', '12345:3'],
                'export_rt': ['12345:1', '12345:2', '12345:4']
            }
        }

        """
        bgpvpn_rts = {}
        for bgpvpn in bgpvpns:
            # Add necessary keys to BGP VPN route targets dictionary
            if bgpvpn['type'] + 'vpn' not in bgpvpn_rts:
                bgpvpn_rts.update(
                    {bgpvpn['type'] + 'vpn': {'import_rt': [],
                                              'export_rt': []}}
                )

            if 'route_targets' in bgpvpn:
                bgpvpn_rts[bgpvpn['type'] + 'vpn']['import_rt'] += (
                    bgpvpn['route_targets']
                )
                bgpvpn_rts[bgpvpn['type'] + 'vpn']['export_rt'] += (
                    bgpvpn['route_targets']
                )

            if 'import_targets' in bgpvpn:
                bgpvpn_rts[bgpvpn['type'] + 'vpn']['import_rt'] += (
                    bgpvpn['import_targets']
                )

            if 'export_targets' in bgpvpn:
                bgpvpn_rts[bgpvpn['type'] + 'vpn']['export_rt'] += (
                    bgpvpn['export_targets']
                )

        # FIXME: Only returning l3vpn route targets. Must be modified to also
        # return l2vpn ones in the future
        if 'l2vpn' in bgpvpn_rts:
            bgpvpn_rts.pop('l2vpn')

        return bgpvpn_rts

    def _retrieve_bgpvpn_network_info_for_port(self, context, port):
        """Retrieve BGP VPN network informations for a specific port

        {
            'network_id': <UUID>,
            'mac_address': '00:00:de:ad:be:ef',
            'ip_address': '10.0.0.2',
            'gateway_ip': '10.0.0.1',
            'l3vpn' : {
                'import_rt': ['12345:1', '12345:2', '12345:3'],
                'export_rt': ['12345:1', '12345:2', '12345:4']
            }
        }
        """
        port_id = port['id']
        network_id = port['network_id']

        bgpvpn_network_info = {}

        # Check if port is connected on a BGP VPN network
        bgpvpns = (
            self.bgpvpn_db.find_bgpvpns_for_network(context, network_id)
        )

        if not bgpvpns:
            return

        bgpvpn_rts = self._format_bgpvpn_network_route_targets(bgpvpns)

        LOG.debug("Port connected on BGPVPN network %s with route targets "
                  "%s" % (network_id, bgpvpn_rts))

        bgpvpn_network_info.update(bgpvpn_rts)

        LOG.debug("Getting port %s network details" % port_id)
        network_info = get_network_info_for_port(context, port_id)

        if not network_info:
            return

        bgpvpn_network_info.update(network_info)

        return bgpvpn_network_info

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        for net_id in bgpvpn['networks']:
            if get_network_ports(context, net_id):
                # Format BGPVPN before sending notification
                self.agent_rpc.delete_bgpvpn(
                    context,
                    self._format_bgpvpn(bgpvpn, net_id))

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        (added_keys, removed_keys, changed_keys) = (
            utils.get_bgpvpn_differences(bgpvpn, old_bgpvpn))
        for net_id in bgpvpn['networks']:
            if (get_network_ports(context, net_id)):
                if ((key in added_keys for key in ('route_targets',
                                                   'import_targets',
                                                   'export_targets')) or
                    (key in removed_keys for key in ('route_targets',
                                                     'import_targets',
                                                     'export_targets')) or
                    (key in changed_keys for key in ('route_targets',
                                                     'import_targets',
                                                     'export_targets'))):
                    self.agent_rpc.update_bgpvpn(
                        context,
                        self._format_bgpvpn(bgpvpn, net_id)
                    )

    def create_net_assoc_postcommit(self, context, net_assoc):
        if get_network_ports(context, net_assoc['network_id']):
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
            formated_bgpvpn = self._format_bgpvpn(bgpvpn,
                                                  net_assoc['network_id'])
            self.agent_rpc.update_bgpvpn(
                context,
                formated_bgpvpn)

    def delete_net_assoc_postcommit(self, context, net_assoc):
        if get_network_ports(context, net_assoc['network_id']):
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
            formated_bgpvpn = self._format_bgpvpn(bgpvpn,
                                                  net_assoc['network_id'])
            self.agent_rpc.delete_bgpvpn(context, formated_bgpvpn)

    def _get_port(self, context, port_id):
        # we need to look in the db for two reasons:
        # - the port dict, as provided by the registry callback has no
        #   port binding information
        # - for some notifications, the current port is not included

        _core_plugin = manager.NeutronManager.get_plugin()
        # TODO(tmorin): should not need an admin context
        return _core_plugin.get_port(n_context.get_admin_context(), port_id)

    def _get_port_host(self, context, port):
        if portbindings.HOST_ID not in port:
            raise Exception("cannot determine host_id for port %s, "
                            "aborting BGPVPN update", port['id'])

        return port.get(portbindings.HOST_ID)

    def notify_port_updated(self, context, port_id):
        LOG.info("notify_port_updated on port %s", port_id)

        port = self._get_port(context, port_id)

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == const.DEVICE_OWNER_DHCP:
            LOG.info("Port %s is DHCP, ignoring", port['id'])
            return

        agent_host = self._get_port_host(context, port)

        if port['status'] == const.PORT_STATUS_ACTIVE:
            LOG.info("notify_port_updated, active")
            bgpvpn_network_info = (
                self._retrieve_bgpvpn_network_info_for_port(context, port)
            )

            if bgpvpn_network_info:
                port_bgpvpn_info.update(bgpvpn_network_info)

                self.agent_rpc.attach_port_on_bgpvpn(context,
                                                     port_bgpvpn_info,
                                                     agent_host)
        elif port['status'] == const.PORT_STATUS_DOWN:
            LOG.info("notify_port_updated, down")
            self.agent_rpc.detach_port_from_bgpvpn(context,
                                                   port_bgpvpn_info,
                                                   agent_host)
        else:
            LOG.info("new port status is %s, no action", port['status'])

    def notify_port_deleted(self, context, port_id):
        LOG.info("notify_port_deleted on port %s ", port_id)

        port = self._get_port(context, port_id)

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == const.DEVICE_OWNER_DHCP:
            LOG.info("Port %s is DHCP, ignoring", port['id'])
            return

        agent_host = self._get_port_host(context, port)

        self.agent_rpc.detach_port_from_bgpvpn(context,
                                               port_bgpvpn_info,
                                               agent_host)

    @log_helpers.log_method_call
    def registry_port_updated(self, resource, event, trigger, **kwargs):
        try:
            context = kwargs.get('context')
            port = kwargs.get('port')
            origin_port = kwargs.get('origin_port')
            # In notifications coming from ml2/plugin.py update_port
            # it is possible that 'port' may be None, in this
            # case we will use origin_port
            if port is None:
                port = origin_port
            self.notify_port_updated(context, port['id'])
        except Exception as e:
            LOG.exception(_LE("Error during notification processing "
                              "%(resource)s %(event)s, %(trigger)s, "
                              "%(kwargs)s: %(exc)s"),
                          {'trigger': trigger,
                           'resource': resource,
                           'event': event,
                           'kwargs': kwargs,
                           'exc': e})

    @log_helpers.log_method_call
    def registry_port_deleted(self, resource, event, trigger, **kwargs):
        try:
            context = kwargs.get('context')
            port_id = kwargs.get('port_id')
            self.notify_port_deleted(context, port_id)
        except Exception as e:
            LOG.exception(_LE("Error during notification processing "
                              "%(resource)s %(event)s, %(trigger)s, "
                              "%(kwargs)s: %(exc)s"),
                          {'trigger': trigger,
                           'resource': resource,
                           'event': event,
                           'kwargs': kwargs,
                           'exc': e})
