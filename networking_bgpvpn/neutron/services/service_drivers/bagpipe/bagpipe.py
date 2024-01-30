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

from sqlalchemy import orm
from sqlalchemy import sql

from neutron.db.models import l3
from neutron.db import models_v2

from neutron_lib.api.definitions import portbindings
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as const
from neutron_lib.db import api as db_api

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_bagpipe.agent.bgpvpn import rpc_client

from networking_bgpvpn.neutron.db import bgpvpn_db
from networking_bgpvpn.neutron.services.common import utils
from networking_bgpvpn.neutron.services.service_drivers.bagpipe \
    import bagpipe_v2 as v2


LOG = logging.getLogger(__name__)


@log_helpers.log_method_call
@db_api.CONTEXT_READER
def get_network_info_for_port(context, port_id, network_id):
    """Get MAC, IP and Gateway IP addresses informations for a specific port"""
    try:
        net_info = (context.session.
                    query(models_v2.Port.mac_address,
                          models_v2.IPAllocation.ip_address,
                          models_v2.Subnet.cidr,
                          models_v2.Subnet.gateway_ip).
                    join(models_v2.IPAllocation,
                         models_v2.IPAllocation.port_id ==
                         models_v2.Port.id).
                    join(models_v2.Subnet,
                         models_v2.IPAllocation.subnet_id ==
                         models_v2.Subnet.id).
                    filter(models_v2.Subnet.ip_version == 4).
                    filter(models_v2.Port.id == port_id).one())

        (mac_address, ip_address, cidr, gateway_ip) = net_info
    except orm.exc.NoResultFound:
        return

    gateway_mac = (
        context.session.
        query(models_v2.Port.mac_address).
        filter(
            models_v2.Port.network_id == network_id,
            (models_v2.Port.device_owner ==
             const.DEVICE_OWNER_ROUTER_INTF)
        ).
        one_or_none()
    )

    return {'mac_address': mac_address,
            'ip_address': ip_address + cidr[cidr.index('/'):],
            'gateway_ip': gateway_ip,
            'gateway_mac': gateway_mac[0] if gateway_mac else None}


@db_api.CONTEXT_READER
def get_gateway_mac(context, network_id):
    gateway_mac = (
        context.session.
        query(models_v2.Port.mac_address).
        filter(
            models_v2.Port.network_id == network_id,
            (models_v2.Port.device_owner ==
             const.DEVICE_OWNER_ROUTER_INTF)
        ).
        one_or_none()
    )

    return gateway_mac[0] if gateway_mac else None


@db_api.CONTEXT_READER
def get_network_ports(context, network_id):
    # NOTE(tmorin): currents callers don't look at detailed results
    # but only test if at least one result exist => can be optimized
    # by returning a count, rather than all port information
    return (context.session.query(models_v2.Port).
            filter(models_v2.Port.network_id == network_id,
                   models_v2.Port.admin_state_up == sql.true()).all())


@db_api.CONTEXT_READER
def get_router_ports(context, router_id):
    return (
        context.session.query(models_v2.Port).
        filter(
            models_v2.Port.device_id == router_id,
            models_v2.Port.device_owner == const.DEVICE_OWNER_ROUTER_INTF
        ).all()
    )


@db_api.CONTEXT_READER
def get_router_bgpvpn_assocs(context, router_id):
    return (
        context.session.query(bgpvpn_db.BGPVPNRouterAssociation).
        filter(
            bgpvpn_db.BGPVPNRouterAssociation.router_id == router_id
        ).all()
    )


@db_api.CONTEXT_READER
def get_network_bgpvpn_assocs(context, net_id):
    return (
        context.session.query(bgpvpn_db.BGPVPNNetAssociation).
        filter(
            bgpvpn_db.BGPVPNNetAssociation.network_id == net_id
        ).all()
    )


@db_api.CONTEXT_READER
def get_bgpvpns_of_router_assocs_by_network(context, net_id):
    return (
        context.session.query(bgpvpn_db.BGPVPN).
        join(bgpvpn_db.BGPVPN.router_associations).
        join(bgpvpn_db.BGPVPNRouterAssociation.router).
        join(l3.Router.attached_ports).
        join(l3.RouterPort.port).
        filter(
            models_v2.Port.network_id == net_id
        ).all()
    )


@db_api.CONTEXT_READER
def get_networks_for_router(context, router_id):
    ports = get_router_ports(context, router_id)
    if ports:
        return {port['network_id'] for port in ports}
    else:
        return []


def _log_callback_processing_exception(resource, event, trigger, kwargs, e):
    LOG.exception("Error during notification processing "
                  "%(resource)s %(event)s, %(trigger)s, "
                  "%(kwargs)s: %(exc)s",
                  {'trigger': trigger,
                   'resource': resource,
                   'event': event,
                   'kwargs': kwargs,
                   'exc': e})


@registry.has_registry_receivers
class BaGPipeBGPVPNDriver(v2.BaGPipeBGPVPNDriver):

    """BGPVPN Service Driver class for BaGPipe"""

    def __init__(self, service_plugin):
        super().__init__(service_plugin)

        self.agent_rpc = rpc_client.BGPVPNAgentNotifyApi()

    def _format_bgpvpn(self, context, bgpvpn, network_id):
        """JSON-format BGPVPN

        BGPVPN, network identifiers, and route targets.
        """
        formatted_bgpvpn = {'id': bgpvpn['id'],
                            'network_id': network_id,
                            'gateway_mac': get_gateway_mac(context,
                                                           network_id)}
        formatted_bgpvpn.update(
            self._format_bgpvpn_network_route_targets([bgpvpn]))

        return formatted_bgpvpn

    def _format_bgpvpn_network_route_targets(self, bgpvpns):
        """Format BGPVPN network informations (VPN type and route targets)

        [{
            'type': 'l3',
            'route_targets': ['12345:1', '12345:2'],
            'import_targets': ['12345:3'],
            'export_targets': ['12345:4']
        },
        {
            'type': 'l3',
            'route_targets': ['12346:1']
        },
        {
            'type': 'l2',
            'route_targets': ['12347:1']
        }
        ]

        to

        {
            'l3vpn' : {
                'import_rt': ['12345:1', '12345:2', '12345:3', '12346:1'],
                'export_rt': ['12345:1', '12345:2', '12345:4', '12346:1']
            },
            'l2vpn' : {
                'import_rt': ['12347:1'],
                'export_rt': ['12347:1']
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

            for attribute in ('import_rt', 'export_rt'):
                if bgpvpn_rts[bgpvpn['type'] + 'vpn'][attribute]:
                    bgpvpn_rts[bgpvpn['type'] + 'vpn'][attribute] = list(
                        set(bgpvpn_rts[bgpvpn['type'] + 'vpn'][attribute]))

        return bgpvpn_rts

    def _bgpvpns_for_network(self, context, network_id):
        return (
            self.bgpvpn_db.get_bgpvpns(
                context,
                filters={
                    'networks': [network_id],
                },
            ) or self.retrieve_bgpvpns_of_router_assocs_by_network(context,
                                                                   network_id)
        )

    def _networks_for_bgpvpn(self, context, bgpvpn):
        networks = []
        networks.extend(bgpvpn['networks'])
        for router_id in bgpvpn['routers']:
            networks.extend(get_networks_for_router(context, router_id))
        return list(set(networks))

    def _retrieve_bgpvpn_network_info_for_port(self, context, port):
        """Retrieve BGP VPN network informations for a specific port

        {
            'network_id': <UUID>,
            'mac_address': '00:00:de:ad:be:ef',
            'ip_address': '10.0.0.2',
            'gateway_ip': '10.0.0.1',
            'gateway_mac': 'aa:bb:cc:dd:ee:ff', # if a router interface exists
            'l3vpn' : {
                'import_rt': ['12345:1', '12345:2', '12345:3'],
                'export_rt': ['12345:1', '12345:2', '12345:4']
            }
        }
        """
        port_id = port['id']
        network_id = port['network_id']

        bgpvpn_network_info = {}

        bgpvpns = self._bgpvpns_for_network(context, network_id)

        # NOTE(tmorin): We currently need to send 'network_id', 'mac_address',
        #   'ip_address', 'gateway_ip' to the agent, even in the absence of
        #   a BGPVPN bound to the port.  If we don't this information will
        #   lack on an update_bgpvpn RPC. When the agent will have the ability
        #   to retrieve this info by itself, we'll change this method
        #   to return {} if there is no bound bgpvpn.

        bgpvpn_rts = self._format_bgpvpn_network_route_targets(bgpvpns)

        LOG.debug("Port connected on BGPVPN network %s with route targets "
                  "%s", (network_id, bgpvpn_rts))

        bgpvpn_network_info.update(bgpvpn_rts)

        LOG.debug("Getting port %s network details", port_id)
        network_info = get_network_info_for_port(context, port_id, network_id)

        if not network_info:
            LOG.warning("No network information for net %s", network_id)
            return

        bgpvpn_network_info.update(network_info)

        return bgpvpn_network_info

    @db_api.CONTEXT_READER
    def retrieve_bgpvpns_of_router_assocs_by_network(self, context,
                                                     network_id):
        return [self.bgpvpn_db._make_bgpvpn_dict(bgpvpn) for bgpvpn in
                get_bgpvpns_of_router_assocs_by_network(context, network_id)]

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        for net_id in self._networks_for_bgpvpn(context, bgpvpn):
            if get_network_ports(context, net_id):
                # Format BGPVPN before sending notification
                self.agent_rpc.delete_bgpvpn(
                    context,
                    self._format_bgpvpn(context, bgpvpn, net_id))

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, new_bgpvpn):
        super().update_bgpvpn_postcommit(
            context, old_bgpvpn, new_bgpvpn)

        (added_keys, removed_keys, changed_keys) = (
            utils.get_bgpvpn_differences(new_bgpvpn, old_bgpvpn))
        ATTRIBUTES_TO_IGNORE = set('name')
        moving_keys = added_keys | removed_keys | changed_keys
        if len(moving_keys ^ ATTRIBUTES_TO_IGNORE):
            for net_id in self._networks_for_bgpvpn(context, new_bgpvpn):
                if (get_network_ports(context, net_id)):
                    self._update_bgpvpn_for_network(context, net_id,
                                                    new_bgpvpn)

    def _update_bgpvpn_for_net_with_id(self, context, network_id, bgpvpn_id):
        if get_network_ports(context, network_id):
            bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
            self._update_bgpvpn_for_network(context, network_id, bgpvpn)

    def _update_bgpvpn_for_network(self, context, net_id, bgpvpn):
        formated_bgpvpn = self._format_bgpvpn(context, bgpvpn, net_id)
        self.agent_rpc.update_bgpvpn(context,
                                     formated_bgpvpn)

    def create_net_assoc_postcommit(self, context, net_assoc):
        super().create_net_assoc_postcommit(context, net_assoc)
        self._update_bgpvpn_for_net_with_id(context,
                                            net_assoc['network_id'],
                                            net_assoc['bgpvpn_id'])

    def delete_net_assoc_postcommit(self, context, net_assoc):
        if get_network_ports(context, net_assoc['network_id']):
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
            formated_bgpvpn = self._format_bgpvpn(context, bgpvpn,
                                                  net_assoc['network_id'])
            self.agent_rpc.delete_bgpvpn(context, formated_bgpvpn)

    def _ignore_port(self, context, port):
        if (port['device_owner'].startswith(
                const.DEVICE_OWNER_NETWORK_PREFIX)):
            LOG.info("Port %s owner is network:*, we'll do nothing",
                     port['id'])
            return True

        if v2.network_is_external(context, port['network_id']):
            LOG.info("Port %s is on an external network, we'll do nothing",
                     port['id'])
            return True

        return False

    @log_helpers.log_method_call
    def notify_port_updated(self, context, port, original_port):

        if self._ignore_port(context, port):
            return

        agent_host = port[portbindings.HOST_ID]

        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if (port['status'] == const.PORT_STATUS_ACTIVE and
                original_port['status'] != const.PORT_STATUS_ACTIVE):
            LOG.debug("notify_port_updated, port became ACTIVE")

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
              original_port['status'] != const.PORT_STATUS_DOWN):
            LOG.debug("notify_port_updated, port became DOWN")
            self.agent_rpc.detach_port_from_bgpvpn(context,
                                                   port_bgpvpn_info,
                                                   agent_host)
        else:
            LOG.debug("new port status is %s, origin status was %s,"
                      " => no action", port['status'], original_port['status'])

    @log_helpers.log_method_call
    def notify_port_deleted(self, context, port):
        port_bgpvpn_info = {'id': port['id'],
                            'network_id': port['network_id']}

        if self._ignore_port(context, port):
            return

        self.agent_rpc.detach_port_from_bgpvpn(context,
                                               port_bgpvpn_info,
                                               port[portbindings.HOST_ID])

    def create_router_assoc_postcommit(self, context, router_assoc):
        super().create_router_assoc_postcommit(
            context, router_assoc)
        for net_id in get_networks_for_router(context,
                                              router_assoc['router_id']):
            self._update_bgpvpn_for_net_with_id(context,
                                                net_id,
                                                router_assoc['bgpvpn_id'])

    def delete_router_assoc_postcommit(self, context, router_assoc):
        for net_id in get_networks_for_router(context,
                                              router_assoc['router_id']):
            net_assoc = {'network_id': net_id,
                         'bgpvpn_id': router_assoc['bgpvpn_id']}
            self.delete_net_assoc_postcommit(context, net_assoc)

    @log_helpers.log_method_call
    def notify_router_interface_created(self, context, router_id, net_id):
        super().notify_router_interface_created(
            context, router_id, net_id)

        net_assocs = get_network_bgpvpn_assocs(context, net_id)
        router_assocs = get_router_bgpvpn_assocs(context, router_id)

        # if this router_interface is on a network bound to a BGPVPN,
        # or if this router is bound to a BGPVPN,
        # then we need to send and update for this network, including
        # the gateway_mac
        if net_assocs or router_assocs:
            for bgpvpn in self._bgpvpns_for_network(context, net_id):
                self._update_bgpvpn_for_network(context, net_id, bgpvpn)

        for router_assoc in router_assocs:
            self._update_bgpvpn_for_net_with_id(context,
                                                net_id,
                                                router_assoc['bgpvpn_id'])

    @log_helpers.log_method_call
    def notify_router_interface_deleted(self, context, router_id, net_id):
        super().notify_router_interface_deleted(
            context, router_id, net_id)

        net_assocs = get_network_bgpvpn_assocs(context, net_id)
        router_assocs = get_router_bgpvpn_assocs(context, router_id)

        if net_assocs or router_assocs:
            for bgpvpn in self._bgpvpns_for_network(context, net_id):
                self._update_bgpvpn_for_network(context, net_id, bgpvpn)

        for router_assoc in router_assocs:
            net_assoc = {'network_id': net_id,
                         'bgpvpn_id': router_assoc['bgpvpn_id']}
            self.delete_net_assoc_postcommit(context, net_assoc)

    @registry.receives(resources.PORT, [events.AFTER_UPDATE])
    @log_helpers.log_method_call
    def registry_port_updated(self, resource, event, trigger, payload):
        try:
            context = payload.context
            port = payload.latest_state
            original_port = payload.states[0]

            self.notify_port_updated(context, port, original_port)
        except Exception as e:
            _log_callback_processing_exception(resource, event, trigger,
                                               payload.metadata, e)

    @registry.receives(resources.PORT, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def registry_port_deleted(self, resource, event, trigger, payload):
        try:
            context = payload.context
            port = payload.latest_state

            self.notify_port_deleted(context, port)
        except Exception as e:
            _log_callback_processing_exception(resource, event, trigger,
                                               payload.metadata, e)

    # contrary to mother class, no need to subscribe to router interface
    # before-delete, because after delete, we still can generate RPCs
    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_DELETE])
    @log_helpers.log_method_call
    def registry_router_interface_deleted(self, resource, event, trigger,
                                          payload=None):
        try:
            context = payload.context
            # for router_interface after_delete, in stable/newton, the
            # callback does not include the router_id directly, but we find
            # it in the port device_id
            router_id = payload.metadata.get('port')['device_id']
            net_id = payload.metadata.get('port')['network_id']
            self.notify_router_interface_deleted(context, router_id, net_id)
        except Exception as e:
            _log_callback_processing_exception(resource, event, trigger,
                                               payload.metadata, e)
