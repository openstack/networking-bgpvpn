#
# Copyright 2017 Ericsson India Global Services Pvt Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import copy
from unittest import mock

from oslo_utils import uuidutils

from neutron.tests.unit.api.v2 import test_base
from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib.api.definitions import bgpvpn as bgpvpn_def
from neutron_lib.api.definitions import bgpvpn_vni as bgpvpn_vni_def
from webob import exc

from networking_bgpvpn.neutron.extensions import bgpvpn

_uuid = uuidutils.generate_uuid
_get_path = test_base._get_path
BGPVPN_PREFIX = 'bgpvpn'
BGPVPN_URI = BGPVPN_PREFIX + '/' + 'bgpvpns'
BGPVPN_PLUGIN_BASE_NAME = (bgpvpn.BGPVPNPluginBase.__module__ +
                           '.' +
                           bgpvpn.BGPVPNPluginBase.__name__)


class BgpvpnVniTestExtensionManager(object):

    def get_resources(self):
        bgpvpn_def.RESOURCE_ATTRIBUTE_MAP[bgpvpn_def.COLLECTION_NAME].update(
            bgpvpn_vni_def.RESOURCE_ATTRIBUTE_MAP[bgpvpn_def.COLLECTION_NAME])
        return bgpvpn.Bgpvpn.get_resources()

    def get_actions(self):
        return []

    def get_request_extensions(self):
        return []


class BgpvpnVniExtensionTestCase(test_extensions_base.ExtensionTestCase):
    fmt = 'json'

    def setUp(self):
        super(BgpvpnVniExtensionTestCase, self).setUp()
        plural_mappings = {'bgpvpn': 'bgpvpns'}
        self.setup_extension(
            BGPVPN_PLUGIN_BASE_NAME,
            bgpvpn_def.ALIAS,
            BgpvpnVniTestExtensionManager(),
            BGPVPN_PREFIX,
            plural_mappings=plural_mappings,
            translate_resource_name=True)
        self.instance = self.plugin.return_value

    def test_bgpvpn_create(self):
        bgpvpn_id = _uuid()
        data = {
            'bgpvpn': {'name': 'bgpvpn1',
                       'type': 'l3',
                       'route_targets': ['1234:56'],
                       'vni': 1000,
                       'tenant_id': _uuid()}
        }
        expected_ret_val = copy.copy(data['bgpvpn'])
        expected_ret_val['import_targets'] = []
        expected_ret_val['export_targets'] = []
        expected_ret_val['route_distinguishers'] = []
        expected_ret_val['vni'] = 1000
        expected_call_args = copy.copy(expected_ret_val)
        expected_ret_val.update({'id': bgpvpn_id})

        self.instance.create_bgpvpn.return_value = expected_ret_val
        res = self.api.post(_get_path(BGPVPN_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.assertTrue(self.instance.create_bgpvpn.called)
        self.assertDictSupersetOf(
            expected_call_args,
            self.instance.create_bgpvpn.call_args[1]['bgpvpn']['bgpvpn'])
        self.assertEqual(res.status_int, exc.HTTPCreated.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn', res)
        self.assertDictSupersetOf(expected_ret_val, res['bgpvpn'])

    def test_bgpvpn_get(self):
        bgpvpn_id = _uuid()
        return_value = {'name': 'bgpvpn1',
                        'type': 'l3',
                        'route_targets': ['1234:56'],
                        'tenant_id': _uuid(),
                        'vni': 1000,
                        'id': bgpvpn_id}

        self.instance.get_bgpvpn.return_value = return_value

        res = self.api.get(_get_path(BGPVPN_URI,
                                     id=bgpvpn_id,
                                     fmt=self.fmt))

        self.instance.get_bgpvpn.assert_called_with(
            mock.ANY, bgpvpn_id, fields=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn', res)
        self.assertEqual(res['bgpvpn'], return_value)

    def test_bgpvpn_delete(self):
        self._test_entity_delete('bgpvpn')
