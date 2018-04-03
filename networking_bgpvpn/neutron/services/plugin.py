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

import copy

from neutron.db import servicetype_db as st_db
from neutron.services import provider_configuration as pconf
from neutron.services import service_base

from neutron_lib.api.definitions import bgpvpn as bgpvpn_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import constants as const
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import constants as plugin_constants
from neutron_lib.plugins import directory

from oslo_log import log

from networking_bgpvpn._i18n import _

from networking_bgpvpn.neutron.extensions import bgpvpn
from networking_bgpvpn.neutron.extensions \
    import bgpvpn_routes_control as bgpvpn_rc
from networking_bgpvpn.neutron.services.common import constants

LOG = log.getLogger(__name__)

# ("BGPVPN" is the string to match as the first part of the
# service_provider configuration: "BGPVPN:Dummy:networking_bgpvpn ...")
SERVICE_PROVIDER_TYPE = "BGPVPN"


@registry.has_registry_receivers
class BGPVPNPlugin(bgpvpn.BGPVPNPluginBase,
                   bgpvpn_rc.BGPVPNRoutesControlPluginBase):

    def __init__(self):
        super(BGPVPNPlugin, self).__init__()

        # Need to look into /etc/neutron/networking_bgpvpn.conf for
        # service_provider definitions:
        service_type_manager = st_db.ServiceTypeManager.get_instance()
        service_type_manager.add_provider_configuration(
            SERVICE_PROVIDER_TYPE,
            pconf.ProviderConfiguration('networking_bgpvpn'))

        # Load the default driver
        drivers, default_provider = service_base.load_drivers(
            SERVICE_PROVIDER_TYPE, self)
        LOG.info("BGP VPN Service Plugin using Service Driver: %s",
                 default_provider)
        self.driver = drivers[default_provider]

        if len(drivers) > 1:
            LOG.warning("Multiple drivers configured for BGPVPN, although"
                        "running multiple drivers in parallel is not yet"
                        "supported")

    @property
    def supported_extension_aliases(self):
        exts = copy.copy(super(BGPVPNPlugin, self).supported_extension_aliases)
        exts += self.driver.more_supported_extension_aliases
        return exts

    @registry.receives(resources.ROUTER_INTERFACE, [events.BEFORE_CREATE])
    def _notify_adding_interface_to_router(self, resource, event, trigger,
                                           **kwargs):
        context = kwargs.get('context')
        network_id = kwargs.get('network_id')
        router_id = kwargs.get('router_id')
        try:
            routers_bgpvpns = self.driver.get_bgpvpns(
                context,
                filters={
                    'routers': [router_id],
                },
            )
        except bgpvpn.BGPVPNRouterAssociationNotSupported:
            return
        nets_bgpvpns = self.driver.get_bgpvpns(
            context,
            filters={
                'networks': [network_id],
                'type': [constants.BGPVPN_L3],
            },
        )

        if routers_bgpvpns and nets_bgpvpns:
            msg = _('It is not allowed to add an interface to a router if '
                    'both the router and the network are bound to an '
                    'L3 BGPVPN.')
            raise n_exc.BadRequest(resource='bgpvpn', msg=msg)

    def _validate_network(self, context, net_id):
        plugin = directory.get_plugin()
        network = plugin.get_network(context, net_id)
        self._validate_network_has_router_assoc(context, network, plugin)
        return network

    def _validate_network_has_router_assoc(self, context, network, plugin):
        filter = {'network_id': [network['id']],
                  'device_owner': [const.DEVICE_OWNER_ROUTER_INTF]}
        router_port = plugin.get_ports(context, filters=filter)
        if router_port:
            router_id = router_port[0]['device_id']
            filter = {'tenant_id': [network['tenant_id']]}
            bgpvpns = self.driver.get_bgpvpns(context, filters=filter)
            bgpvpns = [str(bgpvpn['id']) for bgpvpn in bgpvpns
                       if router_id in bgpvpn['routers']]
            if bgpvpns:
                msg = ('Network %(net_id)s is linked to a router which is '
                       'already associated to bgpvpn(s) %(bgpvpns)s'
                       % {'net_id': network['id'],
                          'bgpvpns': bgpvpns}
                       )
                raise n_exc.BadRequest(resource='bgpvpn', msg=msg)

    def _validate_router(self, context, router_id):
        l3_plugin = directory.get_plugin(plugin_constants.L3)
        router = l3_plugin.get_router(context, router_id)
        plugin = directory.get_plugin()
        self._validate_router_has_net_assocs(context, router, plugin)
        return router

    def _validate_port(self, context, port_id):
        plugin = directory.get_plugin()
        port = plugin.get_port(context, port_id)
        return port

    def _validate_router_has_net_assocs(self, context, router, plugin):
        filter = {'device_id': [router['id']],
                  'device_owner': [const.DEVICE_OWNER_ROUTER_INTF]}
        router_ports = plugin.get_ports(context, filters=filter)
        if router_ports:
            filter = {'tenant_id': [router['tenant_id']]}
            bgpvpns = self.driver.get_bgpvpns(context, filters=filter)
            for port in router_ports:
                bgpvpns = [str(bgpvpn['id']) for bgpvpn in bgpvpns
                           if port['network_id'] in bgpvpn['networks']]
                if bgpvpns:
                    msg = ('router %(rtr_id)s has an attached network '
                           '%(net_id)s which is already associated to '
                           'bgpvpn(s) %(bgpvpns)s'
                           % {'rtr_id': router['id'],
                              'net_id': port['network_id'],
                              'bgpvpns': bgpvpns})
                    raise n_exc.BadRequest(resource='bgpvpn', msg=msg)

    def get_plugin_type(self):
        return bgpvpn_def.ALIAS

    def get_plugin_description(self):
        return "Neutron BGPVPN Service Plugin"

    def create_bgpvpn(self, context, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']
        return self.driver.create_bgpvpn(context, bgpvpn)

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self.driver.get_bgpvpns(context, filters, fields)

    def get_bgpvpn(self, context, id, fields=None):
        return self.driver.get_bgpvpn(context, id, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']
        return self.driver.update_bgpvpn(context, id, bgpvpn)

    def delete_bgpvpn(self, context, id):
        self.driver.delete_bgpvpn(context, id)

    def create_bgpvpn_network_association(self, context, bgpvpn_id,
                                          network_association):
        net_assoc = network_association['network_association']
        # check net exists
        net = self._validate_network(context, net_assoc['network_id'])
        # check every resource belong to the same tenant
        bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
        if net['tenant_id'] != bgpvpn['tenant_id']:
            msg = 'network doesn\'t belong to the bgpvpn owner'
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        if net_assoc['tenant_id'] != bgpvpn['tenant_id']:
            msg = 'network association and bgpvpn should belong to\
                the same tenant'
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        return self.driver.create_net_assoc(context, bgpvpn_id, net_assoc)

    def get_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id,
                                       fields=None):
        return self.driver.get_net_assoc(context, assoc_id, bgpvpn_id, fields)

    def get_bgpvpn_network_associations(self, context, bgpvpn_id,
                                        filters=None, fields=None):
        return self.driver.get_net_assocs(context, bgpvpn_id, filters, fields)

    def update_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id,
                                          network_association):
        # TODO(matrohon) : raise an unsuppported error
        pass

    def delete_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id):
        self.driver.delete_net_assoc(context, assoc_id, bgpvpn_id)

    def create_bgpvpn_router_association(self, context, bgpvpn_id,
                                         router_association):
        router_assoc = router_association['router_association']
        router = self._validate_router(context, router_assoc['router_id'])
        bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
        if not bgpvpn['type'] == constants.BGPVPN_L3:
            msg = ("Router associations require the bgpvpn to be of type %s"
                   % constants.BGPVPN_L3)
            raise n_exc.BadRequest(resource='bgpvpn', msg=msg)
        if not router['tenant_id'] == bgpvpn['tenant_id']:
            msg = "router doesn't belong to the bgpvpn owner"
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        if not (router_assoc['tenant_id'] == bgpvpn['tenant_id']):
            msg = "router association and bgpvpn should " \
                  "belong to the same tenant"
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        return self.driver.create_router_assoc(context, bgpvpn_id,
                                               router_assoc)

    def get_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id,
                                      fields=None):
        return self.driver.get_router_assoc(context, assoc_id, bgpvpn_id,
                                            fields)

    def get_bgpvpn_router_associations(self, context, bgpvpn_id, filters=None,
                                       fields=None):
        return self.driver.get_router_assocs(context, bgpvpn_id, filters,
                                             fields)

    def update_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id,
                                         router_association):
        router_association = router_association['router_association']
        return self.driver.update_router_assoc(context, assoc_id, bgpvpn_id,
                                               router_association)

    def delete_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id):
        self.driver.delete_router_assoc(context, assoc_id, bgpvpn_id)

    def _validate_port_association_routes_bgpvpn(self, context,
                                                 port_association,
                                                 bgpvpn_id, assoc_id=None):
        for route in [r for r in port_association.get('routes', []) if
                      r['type'] == bgpvpn_rc.api_def.BGPVPN_TYPE]:
            try:
                route_bgpvpn = self.get_bgpvpn(context, route['bgpvpn_id'])
            except bgpvpn.BGPVPNNotFound:
                raise bgpvpn_rc.BGPVPNPortAssocRouteNoSuchBGPVPN(
                    bgpvpn_id=route['bgpvpn_id'])

            assoc_bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
            if route_bgpvpn['type'] != assoc_bgpvpn['type']:
                raise bgpvpn_rc.BGPVPNPortAssocRouteBGPVPNTypeDiffer(
                    route_bgpvpn_type=route_bgpvpn['type'],
                    bgpvpn_type=assoc_bgpvpn['type']
                    )

            assoc_tenant_id = port_association.get('project_id')
            if assoc_tenant_id is None:
                # update, rather than create, we need to retrieve the tenant
                assoc = self.get_bgpvpn_port_association(context,
                                                         assoc_id, bgpvpn_id)
                assoc_tenant_id = assoc.get('project_id')

            if route_bgpvpn['project_id'] != assoc_tenant_id:
                raise bgpvpn_rc.BGPVPNPortAssocRouteWrongBGPVPNTenant(
                    bgpvpn_id=route['bgpvpn_id'])

    def create_bgpvpn_port_association(self, context, bgpvpn_id,
                                       port_association):
        port_association = port_association['port_association']
        port = self._validate_port(context, port_association['port_id'])
        bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
        if not port['tenant_id'] == bgpvpn['project_id']:
            msg = "port doesn't belong to the bgpvpn owner"
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        if not (port_association['project_id'] == bgpvpn['project_id']):
            msg = "port association and bgpvpn should " \
                  "belong to the same tenant"
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)
        self._validate_port_association_routes_bgpvpn(context,
                                                      port_association,
                                                      bgpvpn_id)
        return self.driver.create_port_assoc(context,
                                             bgpvpn_id, port_association)

    def get_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id,
                                    fields=None):
        return self.driver.get_port_assoc(context, assoc_id, bgpvpn_id, fields)

    def get_bgpvpn_port_associations(self, context, bgpvpn_id,
                                     filters=None, fields=None):
        return self.driver.get_port_assocs(context, bgpvpn_id, filters, fields)

    def update_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id,
                                       port_association):
        port_association = port_association['port_association']
        self._validate_port_association_routes_bgpvpn(context,
                                                      port_association,
                                                      bgpvpn_id, assoc_id)
        return self.driver.update_port_assoc(context, assoc_id, bgpvpn_id,
                                             port_association)

    def delete_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id):
        self.driver.delete_port_assoc(context, assoc_id, bgpvpn_id)
