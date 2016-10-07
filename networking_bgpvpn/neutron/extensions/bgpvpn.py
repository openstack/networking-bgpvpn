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

import six

from neutron.api import extensions
from neutron.api.v2 import base
from neutron.api.v2 import resource_helper
from neutron import manager
from neutron.plugins.common import constants as n_const
from neutron.services.service_base import ServicePluginBase

from neutron_lib import api
from neutron_lib import exceptions as n_exc

from oslo_log import log

from networking_bgpvpn._i18n import _

from networking_bgpvpn.neutron import extensions as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import constants

LOG = log.getLogger(__name__)


extensions.append_api_extensions_path(bgpvpn_ext.__path__)
n_const.EXT_TO_SERVICE_MAPPING['bgpvpn'] = constants.BGPVPN


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


def _validate_rt_list(data, valid_values=None):
    if data is None or data is "":
        return

    if not isinstance(data, list):
        msg = _("'%s' is not a list") % data
        LOG.debug(msg)
        return msg

    for item in data:
        msg = api.validators.validate_regex(item, constants.RT_REGEX)
        if msg:
            LOG.debug(msg)
            return msg

    if len(set(data)) != len(data):
        msg = _("Duplicate items in the list: '%s'") % ', '.join(data)
        LOG.debug(msg)
        return msg

api.validators.add_validator('type:route_target_list', _validate_rt_list)

RESOURCE_ATTRIBUTE_MAP = {
    constants.BGPVPN_RES: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True,
               'enforce_policy': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True,
                      'is_visible': True,
                      'enforce_policy': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'default': '',
                 'validate': {'type:string': None},
                 'is_visible': True,
                 'enforce_policy': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'default': constants.BGPVPN_L3,
                 'validate': {'type:values': constants.BGPVPN_TYPES},
                 'is_visible': True,
                 'enforce_policy': True},
        'route_targets': {'allow_post': True, 'allow_put': True,
                          'default': [],
                          'convert_to': api.converters.convert_to_list,
                          'validate': {'type:route_target_list': None},
                          'is_visible': True,
                          'enforce_policy': True},
        'import_targets': {'allow_post': True, 'allow_put': True,
                           'default': [],
                           'convert_to': api.converters.convert_to_list,
                           'validate': {'type:route_target_list': None},
                           'is_visible': True,
                           'enforce_policy': True},
        'export_targets': {'allow_post': True, 'allow_put': True,
                           'default': [],
                           'convert_to': api.converters.convert_to_list,
                           'validate': {'type:route_target_list': None},
                           'is_visible': True,
                           'enforce_policy': True},
        'route_distinguishers': {'allow_post': True, 'allow_put': True,
                                 'default': [],
                                 'convert_to': api.converters.convert_to_list,
                                 'validate': {'type:route_target_list': None},
                                 'is_visible': True,
                                 'enforce_policy': True},
        'networks': {'allow_post': False, 'allow_put': False,
                     'is_visible': True,
                     'enforce_policy': True},
        'routers': {'allow_post': False, 'allow_put': False,
                    'is_visible': True,
                    'enforce_policy': True}
    },
}

SUB_RESOURCE_ATTRIBUTE_MAP = {
    'network_associations': {
        'parent': {'collection_name': 'bgpvpns',
                   'member_name': 'bgpvpn'},
        'parameters': {
            'id': {'allow_post': False, 'allow_put': False,
                   'validate': {'type:uuid': None},
                   'is_visible': True,
                   'primary_key': True},
            'tenant_id': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:string': None},
                          'required_by_policy': True,
                          'is_visible': True,
                          'enforce_policy': True},
            'network_id': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:uuid': None},
                           'is_visible': True,
                           'enforce_policy': True}
        }
    },
    'router_associations': {
        'parent': {'collection_name': 'bgpvpns',
                   'member_name': 'bgpvpn'},
        'parameters': {
            'id': {'allow_post': False, 'allow_put': False,
                   'validate': {'type:uuid': None},
                   'is_visible': True,
                   'primary_key': True},
            'tenant_id': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:string': None},
                          'required_by_policy': True,
                          'is_visible': True,
                          'enforce_policy': True},
            'router_id': {'allow_post': True, 'allow_put': False,
                          'validate': {'type:uuid': None},
                          'is_visible': True,
                          'enforce_policy': True}
        }
    }
}


class Bgpvpn(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "BGPVPN extension"

    @classmethod
    def get_alias(cls):
        return "bgpvpn"

    @classmethod
    def get_description(cls):
        return "Extension for BGPVPN service"

    @classmethod
    def get_updated(cls):
        return "2014-06-10T17:00:00-00:00"

    @classmethod
    def get_resources(cls):
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        resources = resource_helper.build_resource_info(plural_mappings,
                                                        RESOURCE_ATTRIBUTE_MAP,
                                                        constants.BGPVPN,
                                                        register_quota=True,
                                                        translate_name=True)
        plugin = manager.NeutronManager.get_service_plugins()[constants.BGPVPN]
        for collection_name in SUB_RESOURCE_ATTRIBUTE_MAP:
            # Special handling needed for sub-resources with 'y' ending
            # (e.g. proxies -> proxy)
            resource_name = collection_name[:-1]
            parent = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get('parent')
            params = SUB_RESOURCE_ATTRIBUTE_MAP[collection_name].get(
                'parameters')

            controller = base.create_resource(collection_name, resource_name,
                                              plugin, params,
                                              allow_bulk=True,
                                              parent=parent,
                                              allow_pagination=True,
                                              allow_sorting=True)

            resource = extensions.ResourceExtension(
                collection_name,
                controller, parent,
                path_prefix='bgpvpn',
                attr_map=params)
            resources.append(resource)
        return resources

    @classmethod
    def get_plugin_interface(cls):
        return BGPVPNPluginBase

    def update_attributes_map(self, attributes):
        super(Bgpvpn, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class BGPVPNPluginBase(ServicePluginBase):

    def get_plugin_name(self):
        return constants.BGPVPN

    def get_plugin_type(self):
        return constants.BGPVPN

    def get_plugin_description(self):
        return 'BGP VPN service plugin'

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
