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

from neutron.extensions import l3
from neutron.tests.unit.api.v2 import test_base
from neutron_lib.api.definitions import bgpvpn as bgpvpn_api_def
from neutron_lib.api.definitions import bgpvpn_routes_control as rc_api_def
from webob import exc

from networking_bgpvpn.neutron.extensions import bgpvpn
from networking_bgpvpn.neutron.extensions \
    import bgpvpn_routes_control as bgpvpn_rc
from networking_bgpvpn.tests.unit.extensions import test_bgpvpn_rc_base

_uuid = uuidutils.generate_uuid
_get_path = test_base._get_path
BGPVPN_PREFIX = 'bgpvpn'
BGPVPN_URI = BGPVPN_PREFIX + '/' + 'bgpvpns'


class TestPlugin(bgpvpn.BGPVPNPluginBase,
                 bgpvpn_rc.BGPVPNRoutesControlPluginBase):

    supported_exsupported_extension_aliases = [bgpvpn_api_def.ALIAS,
                                               rc_api_def.ALIAS]


TEST_PLUGIN_CLASS = '%s.%s' % (TestPlugin.__module__, TestPlugin.__name__)


class BgpvpnRoutesControlExtensionTestCase(
        test_bgpvpn_rc_base.BGPVPNRCExtensionTestCase):

    def setUp(self):
        super(BgpvpnRoutesControlExtensionTestCase, self).setUp()

        self._setUpExtensions(
            TEST_PLUGIN_CLASS,
            bgpvpn_api_def.ALIAS,
            [l3.L3, bgpvpn.Bgpvpn, bgpvpn_rc.Bgpvpn_routes_control],
            BGPVPN_PREFIX,
            translate_resource_name=True)
        self.instance = self.plugin.return_value

        self.bgpvpn_id = _uuid()
        self.net_id = _uuid()
        self.router_id = _uuid()
        self.net_assoc_id = _uuid()
        self.router_assoc_id = _uuid()
        self.port_id = _uuid()
        self.port_assoc_id = _uuid()

        self.NET_ASSOC_URI = BGPVPN_URI + '/' + self.bgpvpn_id + \
            '/network_associations'
        self.ROUTER_ASSOC_URI = BGPVPN_URI + '/' + self.bgpvpn_id + \
            '/router_associations'
        self.PORT_ASSOC_URI = BGPVPN_URI + '/' + self.bgpvpn_id + \
            '/port_associations'

    def _invalid_data_for_creation(self, target):
        return [None, {}, {target: None}, {target: {}}
                ]

    def test_router_association_update(self):
        data = {
            'router_association': {
                'router_id': self.router_id,
                'project_id': _uuid()
            }
        }

        self.api.post(_get_path(self.ROUTER_ASSOC_URI, fmt=self.fmt),
                      self.serialize(data),
                      content_type='application/%s' % self.fmt,
                      expect_errors=True)

        update_data = {'router_association': {
            'advertise_extra_routes': False,
            }}

        return_value = {
            'project_id': _uuid(),
            'advertise_extra_routes': False,
        }

        self.instance.update_bgpvpn_router_association.return_value = (
            return_value)

        res = self.api.put(_get_path(self.ROUTER_ASSOC_URI,
                                     id=self.router_assoc_id,
                                     fmt=self.fmt),
                           self.serialize(update_data),
                           content_type='application/%s' % self.fmt)

        self.instance.update_bgpvpn_router_association.assert_called_with(
            mock.ANY, self.router_assoc_id,
            bgpvpn_id=self.bgpvpn_id, router_association=update_data
        )

        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('router_association', res)
        self.assertEqual(return_value, res['router_association'])

    def _invalid_data_for_port_assoc(self):
        return [
            ({'advertise_fixed_ips': 'foo'},
             "cannot be converted to boolean"),
            ({'routes': 'bla'},
             "is not a list"),
            ({'routes': [{
                'type': 'flumox'}]},
             "No valid key specs"),
            ({'routes': [{
                'type': 'prefix',
                'something_else_than_prefix': 'foo'
                }]},
             "No valid key specs"),
            ({'routes': [{
                'type': 'prefix',
                'prefix': '1.1.1.352'
                }]},
             "No valid key specs"),
            ({'routes': [{
                'type': 'prefix',
                'something_else_than_bgpvpn_id': 'foo'
                }]},
             "No valid key specs"),
            ({'routes': [{
                'type': 'prefix',
                'prefix': '12.1.2.3',
                'local_pref': -1,
                }]},
             "No valid key specs"),
            ({'routes': [{
                'type': 'prefix',
                'prefix': '12.1.2.3/20',
                'local_pref': 2 ** 32,
                }]},
             "No valid key specs")
        ]

    def test_port_association_create(self):
        data = {
            'port_association': {
                'port_id': self.port_id,
                'tenant_id': _uuid()
            }
        }
        return_value = copy.copy(data['port_association'])
        return_value.update({'id': self.port_assoc_id})
        self.instance.create_bgpvpn_port_association.return_value = \
            return_value
        res = self.api.post(_get_path(self.PORT_ASSOC_URI, fmt=self.fmt),
                            self.serialize(data),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)

        self.assertTrue(self.instance.create_bgpvpn_port_association.called)
        self.assertEqual(self.bgpvpn_id,
                         self.instance.create_bgpvpn_port_association.
                         call_args[1]['bgpvpn_id'])
        self.assertDictSupersetOf(
            data['port_association'],
            self.instance.create_bgpvpn_port_association.
            call_args[1]['port_association']['port_association'])

        self.assertIn('port_association', res)
        res = self.deserialize(res)
        self.assertDictSupersetOf(return_value,
                                  res['port_association'])

    def _test_port_association_create_with_invalid_data(self, port_assoc, msg):
        res = self.api.post(_get_path(self.PORT_ASSOC_URI, fmt=self.fmt),
                            self.serialize(port_assoc),
                            content_type='application/%s' % self.fmt,
                            expect_errors=True)
        self.assertEqual(res.status_int, exc.HTTPBadRequest.code)
        self.assertFalse(
            self.instance.create_bgpvpn_port_association.called)
        self.assertIn(msg, str(res.body))

    def test_port_association_create_with_invalid_assoc(self):
        for data in self._invalid_data_for_creation('port_association'):
            res = self.api.post(_get_path(self.PORT_ASSOC_URI, fmt=self.fmt),
                                self.serialize(data),
                                content_type='application/%s' % self.fmt,
                                expect_errors=True)
            self.assertFalse(
                self.instance.create_bgpvpn_port_association.called)
            self.assertEqual(res.status_int, exc.HTTPBadRequest.code)

    def test_port_association_create_with_invalid_content(self):
        for port_assoc_attrs, msg in self._invalid_data_for_port_assoc():
            data = {'port_association': {
                'port_id': self.port_id,
                'project_id': _uuid()
                }
            }
            data['port_association'].update(port_assoc_attrs)
            self._test_port_association_create_with_invalid_data(data, msg)

    def test_port_association_get(self):
        return_value = {'id': self.port_assoc_id,
                        'port_id': self.port_id}

        self.instance.get_bgpvpn_port_association.return_value = \
            return_value

        res = self.api.get(_get_path(self.PORT_ASSOC_URI,
                                     id=self.port_assoc_id,
                                     fmt=self.fmt))

        self.instance.get_bgpvpn_port_association.assert_called_with(
            mock.ANY, self.port_assoc_id, self.bgpvpn_id, fields=mock.ANY
        )
        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('port_association', res)
        self.assertEqual(return_value, res['port_association'])

    def test_port_association_update(self):
        data = {
            'port_association': {
                'port_id': self.port_id,
                'project_id': _uuid()
            }
        }

        self.api.post(_get_path(self.PORT_ASSOC_URI, fmt=self.fmt),
                      self.serialize(data),
                      content_type='application/%s' % self.fmt,
                      expect_errors=True)

        update_data = {'port_association': {
            'advertise_fixed_ips': False,
            'routes': [
                {'type': 'prefix',
                 'prefix': '1.2.3.0/24',
                 'local_pref': 42},
                {'type': 'bgpvpn',
                 'bgpvpn_id': _uuid()},
                ]
            }}

        return_value = {
            'port_id': self.port_id,
            'project_id': _uuid(),
            'advertise_fixed_ips': False,
            'routes': [
                {'type': 'prefix',
                 'prefix': '1.2.3.0/24',
                 'local_pref': 42},
                {'type': 'bgpvpn',
                 'prefix': '1.2.3.0/24'},
            ]
        }

        self.instance.update_bgpvpn_port_association.return_value = (
            return_value)

        res = self.api.put(_get_path(self.PORT_ASSOC_URI,
                                     id=self.port_assoc_id,
                                     fmt=self.fmt),
                           self.serialize(update_data),
                           content_type='application/%s' % self.fmt)

        self.instance.update_bgpvpn_port_association.assert_called_with(
            mock.ANY, self.port_assoc_id,
            bgpvpn_id=self.bgpvpn_id, port_association=update_data
        )

        self.assertEqual(res.status_int, exc.HTTPOk.code)
        res = self.deserialize(res)
        self.assertIn('port_association', res)
        self.assertEqual(res['port_association'], return_value)

    def test_port_association_delete(self):
        res = self.api.delete(_get_path(self.PORT_ASSOC_URI,
                                        id=self.port_assoc_id,
                                        fmt=self.fmt))
        self.instance.delete_bgpvpn_port_association.assert_called_with(
            mock.ANY, self.port_assoc_id, self.bgpvpn_id)
        self.assertEqual(res.status_int, exc.HTTPNoContent.code)
