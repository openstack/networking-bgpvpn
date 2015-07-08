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
import mock

from oslo_utils import uuidutils

from neutron.tests.unit.api.v2 import test_base
from neutron.tests.unit.extensions import base as test_extensions_base
from webob import exc

from networking_bgpvpn.neutron.extensions import bgpvpn
from networking_bgpvpn.neutron.services.common import constants

_uuid = uuidutils.generate_uuid
_get_path = test_base._get_path
BGPVPN_URI = 'bgpvpn'
BGPVPN_CONN_URI = BGPVPN_URI + '/' + 'bgpvpn-connections'
BGPVPN_PLUGIN_BASE_NAME = (
    bgpvpn.BGPVPNPluginBase.__module__ + '.' +
    bgpvpn.BGPVPNPluginBase.__name__)


class BgpvpnExtensionTestCase(test_extensions_base.ExtensionTestCase):
    fmt = 'json'

    def setUp(self):
        super(BgpvpnExtensionTestCase, self).setUp()
        plural_mappings = {'bgpvpn_connection': 'bgpvpn_connections'}
        self._setUpExtension(
            BGPVPN_PLUGIN_BASE_NAME,
            constants.BGPVPN,
            bgpvpn.RESOURCE_ATTRIBUTE_MAP,
            bgpvpn.Bgpvpn,
            BGPVPN_URI,
            plural_mappings=plural_mappings,
            translate_resource_name=True)
        self.instance = self.plugin.return_value

    def test_bgpvpn_connection_create(self):
        bgpvpn_conn_id = _uuid()
        network_id = _uuid()
        data = {
            'bgpvpn_connection': {'name': 'bgpvpn-connection1',
                                  'type': 'l3',
                                  'route_targets': ['1234:56'],
                                  'network_id': network_id,
                                  'auto_aggregate': False,
                                  'tenant_id': _uuid()}
        }
        expected_ret_val = copy.copy(data['bgpvpn_connection'])
        expected_ret_val['import_targets'] = []
        expected_ret_val['export_targets'] = []
        expected_call_args = copy.copy(expected_ret_val)
        expected_ret_val.update({'id': bgpvpn_conn_id})

        self.instance.create_bgpvpn_connection.return_value = expected_ret_val
        res = self.api.post(_get_path(BGPVPN_CONN_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt)
        self.instance.create_bgpvpn_connection.assert_called_with(
            mock.ANY,
            bgpvpn_connection={'bgpvpn_connection': expected_call_args}
        )
        self.assertEqual(res.status_int, exc.HTTPCreated.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn_connection', res)
        self.assertEqual(res['bgpvpn_connection'], expected_ret_val)

    def test_bgpvpn_connection_create_with_malformatted_route_target(self):
        network_id = _uuid()
        data = {
            'bgpvpn_connection': {'name': 'bgpvpn-connection1',
                                  'type': 'l3',
                                  'route_targets': ['ASN:NN'],
                                  'network_id': network_id,
                                  'auto_aggregate': False,
                                  'tenant_id': _uuid()}
        }

        res = self.api.post(_get_path(BGPVPN_CONN_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def test_bgpvpn_connection_create_with_invalid_route_target(self):
        network_id = _uuid()
        data = {
            'bgpvpn_connection': {'name': 'bgpvpn-connection1',
                                  'type': 'l3',
                                  'route_targets': ['65536:0'],
                                  'network_id': network_id,
                                  'auto_aggregate': False,
                                  'tenant_id': _uuid()}
        }

        res = self.api.post(_get_path(BGPVPN_CONN_URI,
                                      fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

        data['bgpvpn_connection']['route_targets'] = ['0:65536']

        res = self.api.post(_get_path(BGPVPN_CONN_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def test_bgpvpn_connection_list(self):
        bgpvpn_conn_id = _uuid()
        return_value = [{'name': 'bgpvpn-connection1',
                         'type': 'l3',
                         'route_targets': ['1234:56'],
                         'auto_aggregate': False,
                         'id': bgpvpn_conn_id}]

        self.instance.get_bgpvpn_connections.return_value = return_value

        res = self.api.get(
            _get_path(BGPVPN_CONN_URI, fmt=self.fmt))

        self.instance.get_bgpvpn_connections.assert_called_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)

    def test_bgpvpn_connection_update(self):
        bgpvpn_conn_id = _uuid()
        network_id = _uuid()
        update_data = {'bgpvpn_connection': {'network_id': network_id}}
        return_value = {'name': 'bgpvpn-connection1',
                        'type': 'l3',
                        'route_targets': ['1234:56'],
                        'network_id': network_id,
                        'auto_aggregate': False,
                        'tenant_id': _uuid(),
                        'id': bgpvpn_conn_id}

        self.instance.update_bgpvpn_connection.return_value = return_value

        res = self.api.put(_get_path(BGPVPN_CONN_URI,
                                     id=bgpvpn_conn_id,
                                     fmt=self.fmt),
                           self.serialize(update_data),
                           content_type='application/%s' % self.fmt)

        self.instance.update_bgpvpn_connection.assert_called_with(
            mock.ANY, bgpvpn_conn_id, bgpvpn_connection=update_data
        )

        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn_connection', res)
        self.assertEqual(res['bgpvpn_connection'], return_value)

    def test_bgpvpn_connection_get(self):
        bgpvpn_conn_id = _uuid()
        return_value = {'name': 'bgpvpn-connection1',
                        'type': 'l3',
                        'route_targets': ['1234:56'],
                        'network_id': _uuid(),
                        'auto_aggregate': False,
                        'tenant_id': _uuid(),
                        'id': bgpvpn_conn_id}

        self.instance.get_bgpvpn_connection.return_value = return_value

        res = self.api.get(_get_path(BGPVPN_CONN_URI,
                                     id=bgpvpn_conn_id,
                                     fmt=self.fmt))

        self.instance.get_bgpvpn_connection.assert_called_with(
            mock.ANY, bgpvpn_conn_id, fields=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn_connection', res)
        self.assertEqual(res['bgpvpn_connection'], return_value)

    def test_bgpvpn_connection_delete(self):
        self._test_entity_delete('bgpvpn_connection')
