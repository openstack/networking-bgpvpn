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

from neutron import context as n_context
from neutron import manager

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.common import constants as const
from neutron.db import models_v2
from oslo_log import log as logging

from networking_bgpvpn.neutron.services.service_drivers import driver_api

from networking_bagpipe.agent.bgpvpn import rpc_client

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

        registry.subscribe(self.registry_port_deleted, resources.PORT,
                           events.AFTER_DELETE)

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

    def _get_bgpvpn_differences(self, current_dict, old_dict):
        """Compare 2 BGPVPNs

        - added elements (route_targets, import_targets or export_targets)
        - removed elements (route_targets, import_targets or export_targets)
        - changed values for keys in both dictionaries  (network_id,
          route_targets, import_targets or export_targets)
        """
        set_current = set(current_dict.keys())
        set_old = set(old_dict.keys())
        intersect = set_current.intersection(set_old)

        added = set_current - intersect
        removed = set_old - intersect
        changed = set(
            key for key in intersect if old_dict[key] != current_dict[key]
        )

        return (added, removed, changed)

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        for net_id in bgpvpn['networks']:
            if get_network_ports(context, net_id):
                # Format BGPVPN before sending notification
                self.agent_rpc.delete_bgpvpn(
                    context,
                    self._format_bgpvpn(bgpvpn, net_id))

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        (added_keys, removed_keys, changed_keys) = (
            self._get_bgpvpn_differences(bgpvpn, old_bgpvpn))
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
        if get_network_ports(context,
                             net_assoc['network_id']):
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
            formated_bgpvpn = self._format_bgpvpn(bgpvpn,
                                                  net_assoc['network_id'])
            self.agent_rpc.update_bgpvpn(
                context,
                formated_bgpvpn)

    def delete_net_assoc_postcommit(self, context, net_assoc):
        if get_network_ports(context,
                             net_assoc['network_id']):
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
            formated_bgpvpn = self._format_bgpvpn(bgpvpn,
                                                  net_assoc['network_id'])
            self.agent_rpc.delete_bgpvpn(context, formated_bgpvpn)

    def _get_port_host(self, port_id):
        # the port dict, as provided by the registry callback
        # has no binding:host_id information, it seems the reason is
        # because the context is not admin
        # let's switch to an admin context and retrieve full port info
        _core_plugin = manager.NeutronManager.get_plugin()
        full_port = _core_plugin.get_port(n_context.get_admin_context(),
                                          port_id)

        if 'binding:host_id' not in full_port:
            raise Exception("cannot determine host_id for port %s, "
                            "aborting BGPVPN update", port_id)

        return full_port.get('binding:host_id')

    def notify_port_updated(self, context, port):
        LOG.info("notify_port_updated on port %s status %s",
                 port['id'],
                 port['status'])

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == const.DEVICE_OWNER_DHCP:
            LOG.info("Port %s is DHCP, ignoring", port['id'])
            return

        agent_host = self._get_port_host(port['id'])

        if port['status'] == const.PORT_STATUS_ACTIVE:
            bgpvpn_network_info = (
                self._retrieve_bgpvpn_network_info_for_port(context, port)
            )

            if bgpvpn_network_info:
                port_bgpvpn_info.update(bgpvpn_network_info)

                self.agent_rpc.attach_port_on_bgpvpn(context,
                                                     port_bgpvpn_info,
                                                     agent_host)
        elif port['status'] == const.PORT_STATUS_DOWN:
            self.agent_rpc.detach_port_from_bgpvpn(context,
                                                   port_bgpvpn_info,
                                                   agent_host)
        else:
            LOG.info("no action since new port status is %s", port['status'])

    def remove_port_from_bgpvpn_agent(self, context, port):
        LOG.info("remove_port_from_bgpvpn_agent port updated on port %s "
                 "status %s",
                 port['id'],
                 port['status'])

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == const.DEVICE_OWNER_DHCP:
            LOG.info("Port %s is DHCP, ignoring", port['id'])
            return

        agent_host = self._get_port_host(port['id'])

        self.agent_rpc.detach_port_from_bgpvpn(context,
                                               port_bgpvpn_info,
                                               agent_host)

    def registry_port_updated(self, resource, event, trigger, **kwargs):
        context = kwargs.get('context')
        port_dict = kwargs.get('port')
        self.notify_port_updated(context, port_dict)

    def registry_port_deleted(self, resource, event, trigger, **kwargs):
        context = kwargs.get('context')
        port_dict = kwargs.get('port')
        self.remove_port_from_bgpvpn_agent(context, port_dict)
