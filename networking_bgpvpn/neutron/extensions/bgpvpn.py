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

from networking_bgpvpn.neutron import extensions as bgpvpn_ext
from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import resource_helper
from neutron.plugins.common import constants as n_const
from neutron.services.service_base import ServicePluginBase
from oslo_log import log

from networking_bgpvpn.neutron.services.common import constants

LOG = log.getLogger(__name__)


# Regular expression to validate Route Target list format
# ["<asn1>:<nn1>","<asn2>:<nn2>", ...] with asn and nn in range 0-65535
RT_REGEX = ('^((?:0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]'
            '\d|6553[0-5]):(?:0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d'
            '{2}|655[0-2]\d|6553[0-5]))$')

extensions.append_api_extensions_path(bgpvpn_ext.__path__)
n_const.EXT_TO_SERVICE_MAPPING['bgpvpn'] = constants.BGPVPN


def _validate_rt_list(data, valid_values=None):
    if not isinstance(data, list):
        msg = _("'%s' is not a list") % data
        LOG.debug(msg)
        return msg

    for item in data:
        msg = attr._validate_regex(item, RT_REGEX)
        if msg:
            LOG.debug(msg)
            return msg

    if len(set(data)) != len(data):
        msg = _("Duplicate items in the list: '%s'") % ', '.join(data)
        LOG.debug(msg)
        return msg


def _validate_rt_list_or_none(data, valid_values=None):
    if not data:
        return _validate_rt_list(data, valid_values=valid_values)

validators = {'type:route_target_list': _validate_rt_list,
              'type:route_target_list_or_none': _validate_rt_list_or_none}
attr.validators.update(validators)

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
                          'convert_to': attr.convert_to_list,
                          'validate': {'type:route_target_list': None},
                          'is_visible': True,
                          'enforce_policy': True},
        'import_targets': {'allow_post': True, 'allow_put': True,
                           'default': [],
                           'convert_to': attr.convert_to_list,
                           'validate': {'type:route_target_list_or_none':
                                        None},
                           'is_visible': True,
                           'enforce_policy': True},
        'export_targets': {'allow_post': True, 'allow_put': True,
                           'default': [],
                           'convert_to': attr.convert_to_list,
                           'validate': {'type:route_target_list_or_none':
                                        None},
                           'is_visible': True,
                           'enforce_policy': True},
        'route_distinguishers': {'allow_post': True, 'allow_put': True,
                                 'default': [],
                                 'convert_to': attr.convert_to_list,
                                 'validate': {'type:route_target_list_or_none':
                                              None},
                                 'is_visible': True,
                                 'enforce_policy': True},
        'auto_aggregate': {'allow_post': True, 'allow_put': True,
                           'default': False,
                           'validate': {'type:boolean': None},
                           'convert_to': attr.convert_to_boolean,
                           'is_visible': True,
                           'enforce_policy': True},
        'networks': {'allow_post': False, 'allow_put': False,
                     'is_visible': True,
                     'enforce_policy': True}
    },
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
        plural_mappings['route_targets'] = 'route_target'
        plural_mappings['import_targets'] = 'import_target'
        plural_mappings['export_targets'] = 'export_target'
        plural_mappings['route_distinguishers'] = 'route_distinguishers'
        attr.PLURALS.update(plural_mappings)
        action_map = {'bgpvpn':
                      {'associate_network': 'PUT',
                       'disassociate_network': 'PUT'}}
        return resource_helper.build_resource_info(plural_mappings,
                                                   RESOURCE_ATTRIBUTE_MAP,
                                                   constants.BGPVPN,
                                                   action_map=action_map,
                                                   register_quota=True,
                                                   translate_name=True)

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
    def associate_network(self, context, id, network_body):
        pass

    @abc.abstractmethod
    def disassociate_network(self, context, id, network_body):
        pass
