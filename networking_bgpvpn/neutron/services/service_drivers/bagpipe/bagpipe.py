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

from networking_bgpvpn.neutron.services import service_drivers

from networking_bagpipe_l2.agent.bgpvpn import rpc_client

LOG = logging.getLogger(__name__)

BAGPIPE_BGPVPN = 'bagpipe-bgpvpn'


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


class BaGPipeBGPVPNDriver(service_drivers.BGPVPNDriverDB):

    """BGP VPN connection Service Driver class for BaGPipe"""

    def __init__(self, service_plugin):
        super(BaGPipeBGPVPNDriver, self).__init__(service_plugin)

        self.agent_rpc = rpc_client.BGPVPNAgentNotifyApi()

        registry.subscribe(self.registry_port_updated, resources.PORT,
                           events.AFTER_UPDATE)

        registry.subscribe(self.registry_port_deleted, resources.PORT,
                           events.AFTER_DELETE)

    @property
    def service_type(self):
        return BAGPIPE_BGPVPN

    def _format_bgpvpn_connection(self, bgpvpn_connection):
        """JSON-format BGP VPN connection

        BGP VPN connection,network identifiers, and route targets.
        """
        formated_bgpvpn_conn = {'id': bgpvpn_connection['id'],
                                'network_id': bgpvpn_connection['network_id']}
        formated_bgpvpn_conn.update(
            self._format_bgpvpn_network_route_targets([bgpvpn_connection])
        )

        return formated_bgpvpn_conn

    def _format_bgpvpn_network_route_targets(self, bgpvpn_connections):
        """Format BGP VPN network informations (VPN type and route targets)

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
        LOG.debug('BGP VPN connection to format %s' % bgpvpn_connections)
        for bgpvpn_conn in bgpvpn_connections:
            # Add necessary keys to BGP VPN route targets dictionary
            if bgpvpn_conn['type'] + 'vpn' not in bgpvpn_rts:
                bgpvpn_rts.update(
                    {bgpvpn_conn['type'] + 'vpn': {'import_rt': [],
                                                   'export_rt': []}}
                )

            if 'route_targets' in bgpvpn_conn:
                bgpvpn_rts[bgpvpn_conn['type'] + 'vpn']['import_rt'] += (
                    bgpvpn_conn['route_targets']
                )
                bgpvpn_rts[bgpvpn_conn['type'] + 'vpn']['export_rt'] += (
                    bgpvpn_conn['route_targets']
                )

            if 'import_targets' in bgpvpn_conn:
                bgpvpn_rts[bgpvpn_conn['type'] + 'vpn']['import_rt'] += (
                    bgpvpn_conn['import_targets']
                )

            if 'export_targets' in bgpvpn_conn:
                bgpvpn_rts[bgpvpn_conn['type'] + 'vpn']['export_rt'] += (
                    bgpvpn_conn['export_targets']
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
        bgpvpn_connections = (
            self.bgpvpn_db.find_bgpvpn_connections_for_network(context,
                                                               network_id)
        )

        if not bgpvpn_connections:
            return

        bgpvpn_rts = (
            self._format_bgpvpn_network_route_targets(bgpvpn_connections)
        )
        LOG.debug("Port connected on BGP VPN network %s with route targets "
                  "%s" % (network_id, bgpvpn_rts))

        bgpvpn_network_info.update(bgpvpn_rts)

        LOG.debug("Getting port %s network details" % port_id)
        network_info = get_network_info_for_port(context, port_id)

        if not network_info:
            return

        bgpvpn_network_info.update(network_info)

        return bgpvpn_network_info

    def _get_bgpvpn_connection_differences(self, current_dict, old_dict):
        """Compare 2 BGP VPN connections

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

    def _create_bgpvpn_connection(self, context, bgpvpn_connection):
        # Notify only if BGP VPN connection associated to a network
        # and network has already plugged ports
        if (bgpvpn_connection['network_id'] is not None and
                get_network_ports(context, bgpvpn_connection['network_id'])):
            # Format BGP VPN connection before sending notification
            self.agent_rpc.create_bgpvpn_connection(
                context,
                self._format_bgpvpn_connection(bgpvpn_connection)
            )

    def _delete_bgpvpn_connection(self, context, bgpvpn_connection):
        # Notify only if BGP VPN connection associated to a network
        # and network has already plugged ports
        # In the case it was dissociated before delete, update notification
        # will do the job (all ports are detached)
        if (bgpvpn_connection['network_id'] is not None and
                get_network_ports(context, bgpvpn_connection['network_id'])):
            # Format BGP VPN connection before sending notification
            self.agent_rpc.delete_bgpvpn_connection(
                context,
                self._format_bgpvpn_connection(bgpvpn_connection)
            )

    def _update_bgpvpn_connection(self, context, old_bgpvpn_connection,
                                  bgpvpn_connection):
        (added_keys, removed_keys, changed_keys) = (
            self._get_bgpvpn_connection_differences(bgpvpn_connection,
                                                    old_bgpvpn_connection)
            )

        if 'network_id' in changed_keys:
            formated_bgpvpn_conn = (
                self._format_bgpvpn_connection(bgpvpn_connection)
            )
            formated_bgpvpn_conn.update(
                {'old_network_id': old_bgpvpn_connection['network_id']}
            )

            # BGP VPN connection is dissociated from a network
            if bgpvpn_connection['network_id'] is None:
                # Check if dissociated network has already plugged ports
                if get_network_ports(context,
                                     old_bgpvpn_connection['network_id']):
                    self.agent_rpc.update_bgpvpn_connection(
                        context,
                        formated_bgpvpn_conn
                    )
            else:
                # Network association to BGP VPN connection
                if old_bgpvpn_connection['network_id'] is None:
                    # Check if associated network has already plugged ports
                    if get_network_ports(context,
                                         bgpvpn_connection['network_id']):
                        self.agent_rpc.update_bgpvpn_connection(
                            context,
                            formated_bgpvpn_conn
                        )
                else:
                    # Association to a different network
                    # Check if one of the 2 networks has already plugged ports
                    if (get_network_ports(context,
                                          old_bgpvpn_connection['network_id'])
                        or get_network_ports(context,
                                             bgpvpn_connection['network_id'])):
                        self.agent_rpc.update_bgpvpn_connection(
                            context,
                            formated_bgpvpn_conn
                        )
        else:
            if (bgpvpn_connection['network_id'] is not None and
                    get_network_ports(context,
                                      bgpvpn_connection['network_id'])):
                if ((key in added_keys for key in ('route_targets',
                                                   'import_targets',
                                                   'export_targets')) or
                    (key in removed_keys for key in ('route_targets',
                                                     'import_targets',
                                                     'export_targets')) or
                    (key in changed_keys for key in ('route_targets',
                                                     'import_targets',
                                                     'export_targets'))):
                    self.agent_rpc.update_bgpvpn_connection(
                        context,
                        self._format_bgpvpn_connection(bgpvpn_connection)
                    )

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
        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == 'network:dhcp':
            LOG.info("Owner of port %s is network:dhcp, ignoring")

        agent_host = self._get_port_host(port['id'])

        if port['status'] == const.PORT_STATUS_ACTIVE:
            bgpvpn_network_info = (
                self._retrieve_bgpvpn_network_info_for_port(context, port)
            )

            if bgpvpn_network_info:
                port_bgpvpn_info.update(bgpvpn_network_info)

                self.agent_rpc.attach_port_on_bgpvpn_network(context,
                                                             port_bgpvpn_info,
                                                             agent_host)
        elif port['status'] == const.PORT_STATUS_DOWN:
            self.agent_rpc.detach_port_from_bgpvpn_network(context,
                                                           port_bgpvpn_info,
                                                           agent_host)
        else:
            LOG.debug("no action since new port status is %", port['status'])

    def remove_port_from_bgpvpn_agent(self, context, port):
        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if port['device_owner'] == 'network:dhcp':
            LOG.info("Owner of port %s is network:dhcp, ignoring")

        agent_host = self._get_port_host(port['id'])

        self.agent_rpc.detach_port_from_bgpvpn_network(context,
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
