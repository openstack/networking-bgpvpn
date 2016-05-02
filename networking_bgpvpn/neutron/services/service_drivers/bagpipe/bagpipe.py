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
from neutron.common import exceptions as n_exc
from neutron import context as n_context
from neutron.db import external_net_db
from neutron.db import l3_db
from neutron.db import models_v2
from neutron.debug import debug_agent
from neutron.extensions import portbindings
from neutron.i18n import _LE
from neutron import manager

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_bagpipe.agent.bgpvpn import rpc_client

from networking_bgpvpn.neutron.db import bgpvpn_db
from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import constants
from networking_bgpvpn.neutron.services.common import utils
from networking_bgpvpn.neutron.services.service_drivers import driver_api

LOG = logging.getLogger(__name__)


BAGPIPE_DRIVER_NAME = "bagpipe"


class BGPVPNExternalNetAssociation(n_exc.NeutronException):
    message = _("driver does not support associating an external"
                "network to a BGPVPN")


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
                        filter(models_v2.Subnet.ip_version == 4).
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


def get_router_ports(context, router_id):
    try:
        return (
            context.session.query(models_v2.Port).
            filter(
                models_v2.Port.device_id == router_id,
                models_v2.Port.device_owner == const.DEVICE_OWNER_ROUTER_INTF
            ).all()
        )
    except exc.NoResultFound:
        return


def get_router_bgpvpn_assocs(context, router_id):
    try:
        return (
            context.session.query(bgpvpn_db.BGPVPNRouterAssociation).
            filter(
                bgpvpn_db.BGPVPNRouterAssociation.router_id == router_id
            ).all()
        )
    except exc.NoResultFound:
        return []


def get_network_bgpvpn_assocs(context, net_id):
    try:
        return (
            context.session.query(bgpvpn_db.BGPVPNNetAssociation).
            filter(
                bgpvpn_db.BGPVPNNetAssociation.network_id == net_id
            ).all()
        )
    except exc.NoResultFound:
        return


def get_bgpvpns_of_router_assocs_by_network(context, net_id):
    try:
        return (
            context.session.query(bgpvpn_db.BGPVPN).
            join(bgpvpn_db.BGPVPN.router_associations).
            join(bgpvpn_db.BGPVPNRouterAssociation.router).
            join(l3_db.Router.attached_ports).
            join(l3_db.RouterPort.port).
            filter(
                models_v2.Port.network_id == net_id
            ).all()
        )
    except exc.NoResultFound:
        return


def network_is_external(context, net_id):
    try:
        context.session.query(external_net_db.ExternalNetwork).filter_by(
            network_id=net_id).one()
        return True
    except exc.NoResultFound:
        return False


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

        registry.subscribe(self.registry_port_created, resources.PORT,
                           events.AFTER_CREATE)

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
            or self.retrieve_bgpvpns_of_router_assocs_by_network(context,
                                                                 network_id)
        )

        # NOTE(tmorin): We currently need to send 'network_id', 'mac_address',
        #   'ip_address', 'gateway_ip' to the agent, even in the absence of
        #   a BGPVPN bound to the port.  If we don't this information will
        #   lack on an update_bgpvpn RPC. When the agent will have the ability
        #   to retrieve this info by itself, we'll change this method
        #   to return {} if there is no bound bgpvpn.

        bgpvpn_rts = self._format_bgpvpn_network_route_targets(bgpvpns)

        LOG.debug("Port connected on BGPVPN network %s with route targets "
                  "%s" % (network_id, bgpvpn_rts))

        bgpvpn_network_info.update(bgpvpn_rts)

        LOG.debug("Getting port %s network details" % port_id)
        network_info = get_network_info_for_port(context, port_id)

        if not network_info:
            LOG.warning("No network information for net %s", network_id)
            return

        bgpvpn_network_info.update(network_info)

        return bgpvpn_network_info

    def retrieve_bgpvpns_of_router_assocs_by_network(self, context,
                                                     network_id):
        return [self.bgpvpn_db._make_bgpvpn_dict(bgpvpn) for bgpvpn in
                get_bgpvpns_of_router_assocs_by_network(context, network_id)]

    def _common_precommit_checks(self, bgpvpn):
        # No support yet for specifying route distinguishers
        if bgpvpn.get('route_distinguishers', None):
            raise bgpvpn_ext.BGPVPNRDNotSupported(driver=BAGPIPE_DRIVER_NAME)

    def create_bgpvpn_precommit(self, context, bgpvpn):
        # Only l3 type is supported
        if bgpvpn['type'] != constants.BGPVPN_L3:
            raise bgpvpn_ext.BGPVPNTypeNotSupported(driver=BAGPIPE_DRIVER_NAME,
                                                    type=bgpvpn['type'])

        self._common_precommit_checks(bgpvpn)

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        for net_id in bgpvpn['networks']:
            if get_network_ports(context, net_id):
                # Format BGPVPN before sending notification
                self.agent_rpc.delete_bgpvpn(
                    context,
                    self._format_bgpvpn(bgpvpn, net_id))

    def update_bgpvpn_precommit(self, context, old_bgpvpn, bgpvpn):
        self._common_precommit_checks(bgpvpn)

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

    def create_net_assoc_precommit(self, context, net_assoc):
        if network_is_external(context, net_assoc['network_id']):
            raise BGPVPNExternalNetAssociation()

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

    def _ignore_port(self, context, port):
        if (port['device_owner'].startswith(const.DEVICE_OWNER_NETWORK_PREFIX)
                and not port['device_owner'] in
                (debug_agent.DEVICE_OWNER_COMPUTE_PROBE,
                 debug_agent.DEVICE_OWNER_NETWORK_PROBE)):
            LOG.info("Port %s owner is network:*, we'll do nothing",
                     port['id'])
            return True

        if network_is_external(context, port['network_id']):
            LOG.info("Port %s is on an external network, we'll do nothing",
                     port['id'])
            return True

        return False

    def notify_port_updated(self, context, port_id, original_port):
        LOG.info("notify_port_updated on port %s", port_id)

        port = self._get_port(context, port_id)

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if self._ignore_port(context, port):
            return

        agent_host = self._get_port_host(context, port)

        original_port_status = "not present in notification"
        if original_port:
            original_port_status = original_port['status']

        if (port['status'] == const.PORT_STATUS_ACTIVE and
                original_port_status != const.PORT_STATUS_ACTIVE):
            LOG.info("notify_port_updated, port became ACTIVE")
            bgpvpn_network_info = (
                self._retrieve_bgpvpn_network_info_for_port(context, port)
            )

            if bgpvpn_network_info:
                port_bgpvpn_info.update(bgpvpn_network_info)

                self.agent_rpc.attach_port_on_bgpvpn(context,
                                                     port_bgpvpn_info,
                                                     agent_host)
            else:
                # currently not reached, because we need
                # _retrieve_bgpvpn_network_info_for_port to always
                # return network information, even in the absence
                # of any BGPVPN port bound.
                pass

        elif (port['status'] == const.PORT_STATUS_DOWN and
                original_port_status != const.PORT_STATUS_DOWN):
            LOG.info("notify_port_updated, port became DOWN")
            self.agent_rpc.detach_port_from_bgpvpn(context,
                                                   port_bgpvpn_info,
                                                   agent_host)
        else:
            LOG.debug("new port status is %s, origin status was %s,"
                      " => no action", port['status'], original_port_status)

    def notify_port_deleted(self, context, port_id):
        LOG.info("notify_port_deleted on port %s ", port_id)

        port = self._get_port(context, port_id)

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if self._ignore_port(context, port):
            return

        agent_host = self._get_port_host(context, port)

        self.agent_rpc.detach_port_from_bgpvpn(context,
                                               port_bgpvpn_info,
                                               agent_host)

    def create_router_assoc_postcommit(self, context, router_assoc):
        ports = get_router_ports(context, router_assoc['router_id'])
        if ports:
            net_ids = set([port['network_id'] for port in ports])
            for net_id in net_ids:
                net_assoc = {'network_id': net_id,
                             'bgpvpn_id': router_assoc['bgpvpn_id']}
                self.create_net_assoc_postcommit(context, net_assoc)

    def delete_router_assoc_postcommit(self, context, router_assoc):
        ports = get_router_ports(context, router_assoc['router_id'])
        if ports:
            net_ids = set([port['network_id'] for port in ports])
            for net_id in net_ids:
                net_assoc = {'network_id': net_id,
                             'bgpvpn_id': router_assoc['bgpvpn_id']}
                self.delete_net_assoc_postcommit(context, net_assoc)

    def router_interface_added(self, context, port):
        net_assocs = get_network_bgpvpn_assocs(context, port['network_id'])
        router_assocs = get_router_bgpvpn_assocs(context, port['device_id'])
        if net_assocs and router_assocs:
            msg = 'Can not add router interface because both router %(rtr)s ' \
                  'and network %(net)s have bgpvpn association(s)'
            LOG.error(msg % {'rtr': port['device_id'],
                             'net': port['network_id']})
            return
        for router_assoc in router_assocs:
            net_assoc = {'network_id': port['network_id'],
                         'bgpvpn_id': router_assoc['bgpvpn_id']}
            self.create_net_assoc_postcommit(context, net_assoc)

    def router_interface_removed(self, context, port):
        for router_assoc in get_router_bgpvpn_assocs(context,
                                                     port['device_id']):
            net_assoc = {'network_id': port['network_id'],
                         'bgpvpn_id': router_assoc['bgpvpn_id']}
            self.delete_net_assoc_postcommit(context, net_assoc)

    @log_helpers.log_method_call
    def registry_port_updated(self, resource, event, trigger, **kwargs):
        try:
            context = kwargs.get('context')
            port = kwargs.get('port')
            original_port = kwargs.get('original_port')
            # In notifications coming from ml2/plugin.py update_port
            # it is possible that 'port' may be None, in this
            # case we will use original_port
            if port is None:
                port = original_port

            rtr_itf_added = self._is_router_intf_added(original_port, port)
            rtr_itf_removed = self._is_router_intf_added(port, original_port)

            if rtr_itf_added:
                self.router_interface_added(context, port)
            elif rtr_itf_removed:
                self.router_interface_removed(context, original_port)
            else:
                self.notify_port_updated(context, port['id'], original_port)
        except Exception as e:
            LOG.exception(_LE("Error during notification processing "
                              "%(resource)s %(event)s, %(trigger)s, "
                              "%(kwargs)s: %(exc)s"),
                          {'trigger': trigger,
                           'resource': resource,
                           'event': event,
                           'kwargs': kwargs,
                           'exc': e})

    def _is_router_intf_added(self, original_port, port):
        if not (original_port and port):
            # This happens when the ml2 rpc.py sends a port update
            # notification. original port will be None. However, this rpc
            # notification will never be from a port device_id/device_owner
            # update, so return False
            return False
        return (original_port['device_owner']
                != const.DEVICE_OWNER_ROUTER_INTF
                == port['device_owner'])

    @log_helpers.log_method_call
    def registry_port_deleted(self, resource, event, trigger, **kwargs):
        try:
            context = kwargs.get('context')
            port_id = kwargs.get('port_id')
            port = self._get_port(context, port_id)

            if port['device_owner'] == const.DEVICE_OWNER_ROUTER_INTF:
                self.router_interface_removed(context, port)
            else:
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

    @log_helpers.log_method_call
    def registry_port_created(self, resource, event, trigger, **kwargs):
        try:
            context = kwargs.get('context')
            port = kwargs.get('port')
            if port and port['device_owner'] == const.DEVICE_OWNER_ROUTER_INTF:
                self.router_interface_added(context, port)
        except Exception as e:
            LOG.exception(_LE("Error during notification processing "
                              "%(resource)s %(event)s, %(trigger)s, "
                              "%(kwargs)s: %(exc)s"),
                          {'trigger': trigger,
                           'resource': resource,
                           'event': event,
                           'kwargs': kwargs,
                           'exc': e})
