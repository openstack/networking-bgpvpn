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

from neutron.api import extensions
from neutron.tests.unit.api.v2 import test_base
from neutron.tests.unit.extensions import base as test_extensions_base
from neutron_lib.api.definitions import bgpvpn as bgpvpn_api_def
from webob import exc

from networking_bgpvpn.neutron import extensions as bgpvpn_extensions
from networking_bgpvpn.neutron.extensions import bgpvpn

_uuid = uuidutils.generate_uuid
_get_path = test_base._get_path
BGPVPN_PREFIX = 'bgpvpn'
BGPVPN_URI = BGPVPN_PREFIX + '/' + 'bgpvpns'


class BgpvpnExtensionTestCaseBase(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        # NOTE(tmorin): this is already done in
        # networking_bgpvpn.neutron.extensions.bgpvpn at module loading time,
        # but for some reason I don't understand this is overridden later,
        # which is why we re-force this here:
        extensions.append_api_extensions_path(bgpvpn_extensions.__path__)

        super(BgpvpnExtensionTestCaseBase, self).setUp()
        plural_mappings = {'bgpvpn': 'bgpvpns'}
        self.setup_extension(
            '%s.%s' % (bgpvpn.BGPVPNPluginBase.__module__,
                       bgpvpn.BGPVPNPluginBase.__name__),
            bgpvpn_api_def.ALIAS,
            bgpvpn.Bgpvpn,
            BGPVPN_PREFIX,
            plural_mappings=plural_mappings,
            translate_resource_name=True)
        self.instance = self.plugin.return_value
        self.bgpvpn_id = _uuid()
        self.net_id = _uuid()
        self.router_id = _uuid()
        self.net_assoc_id = _uuid()
        self.router_assoc_id = _uuid()
        self.NET_ASSOC_URI = BGPVPN_URI + '/' + self.bgpvpn_id + \
            '/network_associations'
        self.ROUTER_ASSOC_URI = BGPVPN_URI + '/' + self.bgpvpn_id + \
            '/router_associations'


class BgpvpnExtensionTestCase(BgpvpnExtensionTestCaseBase):

    def test_bgpvpn_create(self):
        bgpvpn_id = _uuid()
        data = {
            'bgpvpn': {'name': 'bgpvpn1',
                       'type': 'l3',
                       'route_targets': ['1234:56'],
                       'tenant_id': _uuid()}
        }
        expected_ret_val = copy.copy(data['bgpvpn'])
        expected_ret_val['import_targets'] = []
        expected_ret_val['export_targets'] = []
        expected_ret_val['route_distinguishers'] = []
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

    def test_bgpvpn_create_with_malformatted_route_target(self):
        data = {
            'bgpvpn': {'name': 'bgpvpn1',
                       'type': 'l3',
                       'route_targets': ['ASN:NN'],
                       'tenant_id': _uuid()}
        }

        res = self.api.post(_get_path(BGPVPN_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def _data_for_invalid_rtdt(self, field):
        values = [[':1'],
                  ['1:'],
                  ['42'],
                  ['65536:123456'],
                  ['123.456.789.123:65535'],
                  ['4294967296:65535'],
                  ['1.1.1.1:655351'],
                  ['4294967295:65536'],
                  [''],
                  ]
        for value in values:
            yield {'bgpvpn': {'name': 'bgpvpn1',
                              'type': 'l3',
                              field: value,
                              'tenant_id': _uuid()}
                   }

    def _data_for_valid_rtdt(self, field):
        values = [['1:1'],
                  ['1:4294967295'],
                  ['65535:0'],
                  ['65535:4294967295'],
                  ['1.1.1.1:1'],
                  ['1.1.1.1:65535'],
                  ['4294967295:0'],
                  ['65536:65535'],
                  ['4294967295:65535'],
                  ]
        for value in values:
            yield {'bgpvpn': {'name': 'bgpvpn1',
                              'type': 'l3',
                              field: value,
                              'tenant_id': _uuid()}
                   }

    def _test_invalid_field(self, field):
        for data in self._data_for_invalid_rtdt(field):
            res = self.api.post(_get_path(BGPVPN_URI, fmt=self.fmt),
                                self.serialize(data),
                                content_type='application/%s' % self.fmt,
                                expect_errors=True)

            self.assertEqual(res.status_int, exc.HTTPBadRequest.code,
                             "test failed for %s" % data)

    def _test_valid_field(self, field):
        for data in self._data_for_valid_rtdt(field):
            res = self.api.post(_get_path(BGPVPN_URI, fmt=self.fmt),
                                self.serialize(data),
                                content_type='application/%s' % self.fmt,
                                expect_errors=False)

            self.assertEqual(res.status_int, exc.HTTPCreated.code,
                             "test failed for %s" % data)

    def test_bgpvpn_create_with_invalid_route_targets(self):
        self._test_invalid_field('route_targets')

    def test_bgpvpn_create_with_valid_route_targets(self):
        self._test_valid_field('route_targets')

    def test_bgpvpn_create_with_invalid_import_rts(self):
        self._test_invalid_field('import_targets')

    def test_bgpvpn_create_with_valid_import_rts(self):
        self._test_valid_field('import_targets')

    def test_bgpvpn_create_with_invalid_export_rts(self):
        self._test_invalid_field('export_targets')

    def test_bgpvpn_create_with_valid_export_rts(self):
        self._test_valid_field('export_targets')

    def test_bgpvpn_create_with_invalid_route_distinguishers(self):
        self._test_invalid_field('route_distinguishers')

    def test_bgpvpn_create_with_valid_route_distinguishers(self):
        self._test_valid_field('route_distinguishers')

    def test_bgpvpn_list(self):
        bgpvpn_id = _uuid()
        return_value = [{'name': 'bgpvpn1',
                         'type': 'l3',
                         'route_targets': ['1234:56'],
                         'id': bgpvpn_id}]

        self.instance.get_bgpvpns.return_value = return_value

        res = self.api.get(
            _get_path(BGPVPN_URI, fmt=self.fmt))

        self.instance.get_bgpvpns.assert_called_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)

    def test_bgpvpn_update(self):
        bgpvpn_id = _uuid()
        update_data = {'bgpvpn': {'name': 'bgpvpn_updated'}}
        return_value = {'name': 'bgpvpn1',
                        'type': 'l3',
                        'route_targets': ['1234:56'],
                        'tenant_id': _uuid(),
                        'id': bgpvpn_id}

        self.instance.update_bgpvpn.return_value = return_value

        res = self.api.put(_get_path(BGPVPN_URI,
                                     id=bgpvpn_id,
                                     fmt=self.fmt),
                           self.serialize(update_data),
                           content_type='application/%s' % self.fmt)

        self.instance.update_bgpvpn.assert_called_with(
            mock.ANY, bgpvpn_id, bgpvpn=update_data
        )

        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('bgpvpn', res)
        self.assertEqual(res['bgpvpn'], return_value)

    def test_bgpvpn_get(self):
        bgpvpn_id = _uuid()
        return_value = {'name': 'bgpvpn1',
                        'type': 'l3',
                        'route_targets': ['1234:56'],
                        'tenant_id': _uuid(),
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

    def test_bgpvpn_net_create(self):
        data = {'network_association': {'network_id': self.net_id,
                                        'tenant_id': _uuid()}}
        return_value = copy.copy(data['network_association'])
        return_value.update({'id': self.net_assoc_id})
        self.instance.create_bgpvpn_network_association.return_value = \
            return_value
        res = self.api.post(_get_path(self.NET_ASSOC_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertTrue(self.instance.create_bgpvpn_network_association.called)
        self.assertEqual(self.bgpvpn_id,
                         self.instance.create_bgpvpn_network_association.
                         call_args[1]['bgpvpn_id'])
        self.assertDictSupersetOf(
            data['network_association'],
            self.instance.create_bgpvpn_network_association.
            call_args[1]['network_association']['network_association'])

        self.assertIn('network_association', res)
        res = self.deserialize(res)
        self.assertDictSupersetOf(return_value,
                                  res['network_association'])

    def _invalid_data_for_creation(self, target):
        return [None, {}, {target: None}, {target: {}}]

    def test_bgpvpn_net_create_with_invalid_data(self):
        for data in self._invalid_data_for_creation('network_association'):
            res = self.api.post(_get_path(self.NET_ASSOC_URI, fmt=self.fmt),
                                self.serialize(data),
                                content_type='application/%s' % self.fmt,
                                expect_errors=True)
            self.assertFalse(
                self.instance.create_bgpvpn_network_association.called)
            self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def test_bgpvpn_net_get(self):
        return_value = {'id': self.net_assoc_id,
                        'network_id': self.net_id}

        self.instance.get_bgpvpn_network_association.return_value = \
            return_value

        res = self.api.get(_get_path(self.NET_ASSOC_URI,
                                     id=self.net_assoc_id,
                                     fmt=self.fmt))

        self.instance.get_bgpvpn_network_association.assert_called_with(
            mock.ANY, self.net_assoc_id, self.bgpvpn_id, fields=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('network_association', res)
        self.assertEqual(return_value, res['network_association'])

    def test_bgpvpn_net_update(self):
        pass

    def test_bgpvpn_net_delete(self):
        res = self.api.delete(_get_path(self.NET_ASSOC_URI,
                                        id=self.net_assoc_id,
                                        fmt=self.fmt))
        self.instance.delete_bgpvpn_network_association.assert_called_with(
            mock.ANY, self.net_assoc_id, self.bgpvpn_id)
        self.assertEqual(res.status_int, exc.HTTPNoContent.code)

    def test_bgpvpn_router_create(self):
        data = {
            'router_association': {
                'router_id': self.router_id,
                'tenant_id': _uuid()
            }
        }
        return_value = copy.copy(data['router_association'])
        return_value.update({'id': self.router_assoc_id})
        self.instance.create_bgpvpn_router_association.return_value = \
            return_value
        res = self.api.post(_get_path(self.ROUTER_ASSOC_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertTrue(self.instance.create_bgpvpn_router_association.called)
        self.assertEqual(self.bgpvpn_id,
                         self.instance.create_bgpvpn_router_association.
                         call_args[1]['bgpvpn_id'])
        self.assertDictSupersetOf(
            data['router_association'],
            self.instance.create_bgpvpn_router_association.
            call_args[1]['router_association']['router_association'])

        self.assertIn('router_association', res)
        res = self.deserialize(res)
        self.assertDictSupersetOf(return_value,
                                  res['router_association'])

    def test_bgpvpn_router_create_with_invalid_data(self):
        for data in self._invalid_data_for_creation('router_association'):
            res = self.api.post(_get_path(self.ROUTER_ASSOC_URI, fmt=self.fmt),
                                self.serialize(data),
                                content_type='application/%s' % self.fmt,
                                expect_errors=True)
            self.assertFalse(
                self.instance.create_bgpvpn_router_association.called)
            self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def test_bgpvpn_router_get(self):
        return_value = {'id': self.router_assoc_id,
                        'router_id': self.router_id}

        self.instance.get_bgpvpn_router_association.return_value = \
            return_value

        res = self.api.get(_get_path(self.ROUTER_ASSOC_URI,
                                     id=self.router_assoc_id,
                                     fmt=self.fmt))

        self.instance.get_bgpvpn_router_association.assert_called_with(
            mock.ANY, self.router_assoc_id, self.bgpvpn_id, fields=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('router_association', res)
        self.assertEqual(return_value, res['router_association'])

    def test_bgpvpn_router_update(self):
        pass

    def test_bgpvpn_router_delete(self):
        res = self.api.delete(_get_path(self.ROUTER_ASSOC_URI,
                                        id=self.router_assoc_id,
                                        fmt=self.fmt))
        self.instance.delete_bgpvpn_router_association.assert_called_with(
            mock.ANY, self.router_assoc_id, self.bgpvpn_id)
        self.assertEqual(res.status_int, exc.HTTPNoContent.code)
