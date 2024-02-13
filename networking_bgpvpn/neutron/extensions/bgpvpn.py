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
from neutron.api.v2 import resource_helper
from neutron.common import config as common_config

from neutron_lib.api.definitions import bgpvpn as bgpvpn_api_def
from neutron_lib.api import extensions as api_extensions
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import directory
from neutron_lib.services import base as libbase

from oslo_log import log

from networking_bgpvpn._i18n import _
from networking_bgpvpn.neutron import extensions as bgpvpn_extensions

LOG = log.getLogger(__name__)


common_config.register_common_config_options()
extensions.append_api_extensions_path(bgpvpn_extensions.__path__)


class BGPVPNNotFound(n_exc.NotFound):
    message = _("BGPVPN %(id)s could not be found")


class BGPVPNNetAssocNotFound(n_exc.NotFound):
    message = _("BGPVPN network association %(id)s could not be found "
                "for BGPVPN %(bgpvpn_id)s")


class BGPVPNRouterAssocNotFound(n_exc.NotFound):
    message = _("BGPVPN router association %(id)s could not be found "
                "for BGPVPN %(bgpvpn_id)s")


class BGPVPNTypeNotSupported(n_exc.BadRequest):
    message = _("BGPVPN %(driver)s driver does not support %(type)s type")


class BGPVPNRDNotSupported(n_exc.BadRequest):
    message = _("BGPVPN %(driver)s driver does not support to manually set "
                "route distinguisher")


class BGPVPNFindFromNetNotSupported(n_exc.BadRequest):
    message = _("BGPVPN %(driver)s driver does not support to fetch BGPVPNs "
                "associated to network id %(net_id)")


class BGPVPNNetAssocAlreadyExists(n_exc.BadRequest):
    message = _("network %(net_id)s is already associated to "
                "BGPVPN %(bgpvpn_id)s")


class BGPVPNRouterAssociationNotSupported(n_exc.BadRequest):
    message = _("BGPVPN %(driver)s driver does not support router "
                "associations")


class BGPVPNRouterAssocAlreadyExists(n_exc.BadRequest):
    message = _("router %(router_id)s is already associated to "
                "BGPVPN %(bgpvpn_id)s")


class BGPVPNMultipleRouterAssocNotSupported(n_exc.BadRequest):
    message = _("BGPVPN %(driver)s driver does not support multiple "
                "router association with a bgpvpn")


class BGPVPNNetworkAssocExistsAnotherBgpvpn(n_exc.BadRequest):
    message = _("Network %(network)s already associated with %(bgpvpn)s. "
                "BGPVPN %(driver)s driver does not support same network"
                " associated to multiple bgpvpns")


class BGPVPNDriverError(n_exc.NeutronException):
    message = _("%(method)s failed.")


class Bgpvpn(api_extensions.APIExtensionDescriptor):

    api_definition = bgpvpn_api_def

    @classmethod
    def get_resources(cls):
        plural_mappings = resource_helper.build_plural_mappings(
            {}, bgpvpn_api_def.RESOURCE_ATTRIBUTE_MAP)
        resources = resource_helper.build_resource_info(
            plural_mappings,
            bgpvpn_api_def.RESOURCE_ATTRIBUTE_MAP,
            bgpvpn_api_def.ALIAS,
            register_quota=True,
            translate_name=True)
        plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)
        sub_res_attrs = bgpvpn_api_def.SUB_RESOURCE_ATTRIBUTE_MAP
        for collection_name in sub_res_attrs:
            # Special handling needed for sub-resources with 'y' ending
            # (e.g. proxies -> proxy)
            resource_name = collection_name[:-1]
            parent = bgpvpn_api_def.SUB_RESOURCE_ATTRIBUTE_MAP[
                collection_name].get('parent')
            params = bgpvpn_api_def.SUB_RESOURCE_ATTRIBUTE_MAP[
                collection_name].get('parameters')

            controller = base.create_resource(collection_name, resource_name,
                                              plugin, params,
                                              allow_bulk=True,
                                              parent=parent,
                                              allow_pagination=True,
                                              allow_sorting=True)

            resource = extensions.ResourceExtension(
                collection_name,
                controller, parent,
                path_prefix=bgpvpn_api_def.ALIAS,
                attr_map=params)
            resources.append(resource)
        return resources

    @classmethod
    def get_plugin_interface(cls):
        return BGPVPNPluginBase


class BGPVPNPluginBase(libbase.ServicePluginBase, metaclass=abc.ABCMeta):

    path_prefix = "/" + bgpvpn_api_def.ALIAS
    supported_extension_aliases = [bgpvpn_api_def.ALIAS]

    def get_plugin_type(self):
        return bgpvpn_api_def.ALIAS

    def get_plugin_description(self):
        return 'BGP VPN Interconnection service plugin'

    @abc.abstractmethod
    def create_bgpvpn(self, context, bgpvpn):
        pass

    @abc.abstractmethod
    def get_bgpvpns(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn(self, context, id, bgpvpn):
        pass

    @abc.abstractmethod
    def delete_bgpvpn(self, context, id):
        pass

    @abc.abstractmethod
    def create_bgpvpn_network_association(self, context, bgpvpn_id,
                                          network_association):
        pass

    @abc.abstractmethod
    def get_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id,
                                       fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn_network_associations(self, context, bgpvpn_id,
                                        filters=None, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id,
                                          network_association):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_network_association(self, context, assoc_id, bgpvpn_id):
        pass

    @abc.abstractmethod
    def create_bgpvpn_router_association(self, context, bgpvpn_id,
                                         router_association):
        pass

    @abc.abstractmethod
    def get_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id,
                                      fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn_router_associations(self, context, bgpvpn_id, filters=None,
                                       fields=None):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_router_association(self, context, assoc_id, bgpvpn_id):
        pass
