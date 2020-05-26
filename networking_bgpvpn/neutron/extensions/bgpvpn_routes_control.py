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

import abc

from neutron.api import extensions
from neutron.api.v2 import base

from neutron_lib.api.definitions import bgpvpn as bgpvpn_api
from neutron_lib.api.definitions import bgpvpn_routes_control as api_def
from neutron_lib.api import extensions as api_extensions
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import directory
from neutron_lib.services import base as libbase

from oslo_log import log

from networking_bgpvpn._i18n import _


LOG = log.getLogger(__name__)


class BGPVPNPortAssocNotFound(n_exc.NotFound):
    message = _("BGPVPN port association %(id)s could not be found "
                "for BGPVPN %(bgpvpn_id)s")


class BGPVPNPortAssocAlreadyExists(n_exc.BadRequest):
    message = _("port %(port_id)s is already associated to "
                "BGPVPN %(bgpvpn_id)s")


class BGPVPNPortAssocRouteNoSuchBGPVPN(n_exc.BadRequest):
    message = _("bgpvpn specified in route does not exist (%(bgpvpn_id)s)")


class BGPVPNPortAssocRouteWrongBGPVPNTenant(n_exc.BadRequest):
    message = _("bgpvpn specified in route does not belong to the tenant "
                "(%(bgpvpn_id)s)")


class BGPVPNPortAssocRouteBGPVPNTypeDiffer(n_exc.BadRequest):
    message = _("bgpvpn specified in route is of type %(route_bgpvpn_type)s, "
                "differing from type of associated BGPVPN %(bgpvpn_type)s)")


class Bgpvpn_routes_control(api_extensions.APIExtensionDescriptor):

    api_definition = api_def

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        # the plugin we link this extension with is the 'bgpvpn' plugin:
        plugin = directory.get_plugin(bgpvpn_api.ALIAS)

        # The port association is the only new (sub-)resource
        # introduced by the bgpvpn-routes-control extension
        collection_name = api_def.PORT_ASSOCIATIONS

        resource_name = collection_name[:-1]
        parent = api_def.SUB_RESOURCE_ATTRIBUTE_MAP[
            collection_name].get('parent')
        params = api_def.SUB_RESOURCE_ATTRIBUTE_MAP[
            collection_name].get('parameters')

        controller = base.create_resource(collection_name, resource_name,
                                          plugin, params,
                                          allow_bulk=True,
                                          parent=parent,
                                          allow_pagination=True,
                                          allow_sorting=True)

        port_association_resource = extensions.ResourceExtension(
            collection_name,
            controller, parent,
            path_prefix='bgpvpn',
            attr_map=params)

        return [port_association_resource]

    @classmethod
    def get_plugin_interface(cls):
        return BGPVPNRoutesControlPluginBase


class BGPVPNRoutesControlPluginBase(libbase.ServicePluginBase,
                                    metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def update_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id,
                                         router_association):
        pass

    @abc.abstractmethod
    def create_bgpvpn_port_association(self, context, bgpvpn_id,
                                       port_association):
        pass

    @abc.abstractmethod
    def get_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id,
                                    fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn_port_associations(self, context, bgpvpn_id,
                                     filters=None, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id,
                                       port_association):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_port_association(self, context, assoc_id, bgpvpn_id):
        pass
