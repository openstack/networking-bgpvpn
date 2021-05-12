# Copyright 2014 Intel Corporation.
# Copyright 2014 Isaku Yamahata <isaku.yamahata at intel com>
#                               <isaku.yamahata at gmail com>
# All Rights Reserved.
#
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

from unittest import mock

from oslo_config import cfg
import webtest

from neutron_lib import fixture

from neutron.api import extensions
from neutron import manager
from neutron import quota
from neutron.tests.unit.api import test_extensions
from neutron.tests.unit.extensions import base as test_extensions_base


CORE_PLUGIN = 'neutron.db.db_base_plugin_v2.NeutronDbPluginV2'


class BGPVPNRCExtensionTestCase(test_extensions_base.ExtensionTestCase):

    # This is a modified copy of
    # n.t.u.extensions.base.ExtensionTestCase._setUpExtension
    # until the corresponding behavior, which consists in allowing
    # that more than one extension is setup, is pushed to neutron
    def _setUpExtension(self, plugin, service_type,
                        _unused__resource_attribute_map,
                        extension_class, *args, **kwargs):
        self._setUpExtensions(plugin, service_type,
                              [extension_class], *args, **kwargs)

    def _setUpExtensions(self, plugin, service_type,
                         extension_classes,
                         resource_prefix, plural_mappings=None,
                         translate_resource_name=False,
                         allow_pagination=False, allow_sorting=False,
                         supported_extension_aliases=None,
                         use_quota=False,
                         ):

        self._resource_prefix = resource_prefix
        self._plural_mappings = plural_mappings or {}
        self._translate_resource_name = translate_resource_name

        # Ensure existing ExtensionManager is not used
        extensions.PluginAwareExtensionManager._instance = None

        self.useFixture(fixture.APIDefinitionFixture())

        # Create the default configurations
        self.config_parse()

        core_plugin = CORE_PLUGIN if service_type else plugin
        self.setup_coreplugin(core_plugin, load_plugins=False)
        if service_type:
            cfg.CONF.set_override('service_plugins', [plugin])

        self._plugin_patcher = mock.patch(plugin, autospec=True)
        self.plugin = self._plugin_patcher.start()
        instance = self.plugin.return_value

        if service_type:
            instance.get_plugin_type.return_value = service_type
        manager.init()

        if supported_extension_aliases is not None:
            instance.supported_extension_aliases = supported_extension_aliases
        if allow_pagination:
            # instance.__native_pagination_support = True
            native_pagination_attr_name = ("_%s__native_pagination_support"
                                           % instance.__class__.__name__)
            setattr(instance, native_pagination_attr_name, True)
        if allow_sorting:
            # instance.__native_sorting_support = True
            native_sorting_attr_name = ("_%s__native_sorting_support"
                                        % instance.__class__.__name__)
            setattr(instance, native_sorting_attr_name, True)
        if use_quota:
            quota.QUOTAS._driver = None
            cfg.CONF.set_override(
                'quota_driver', 'neutron.db.quota.driver.DbQuotaDriver',
                group='QUOTAS')
        setattr(instance, 'path_prefix', resource_prefix)

        ####################################################################
        ext_mgr = extensions.ExtensionManager('')
        for extension_class in extension_classes:
            ext = extension_class()
            ext_mgr.add_extension(ext)
        ####################################################################

        self.ext_mdw = test_extensions.setup_extensions_middleware(ext_mgr)
        self.api = webtest.TestApp(self.ext_mdw)
