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

import contextlib
import mock
import webob.exc

from oslo_utils import uuidutils

from neutron.api import extensions as api_extensions
from neutron.db import servicetype_db as sdb
from neutron.tests.unit.db import test_db_base_plugin_v2

from networking_bgpvpn.neutron import extensions
from networking_bgpvpn.neutron.services.common import constants
from networking_bgpvpn.neutron.services import plugin
from networking_bgpvpn.neutron.services.service_drivers import dummy

_uuid = uuidutils.generate_uuid


class BgpvpnTestCaseMixin(test_db_base_plugin_v2.NeutronDbPluginV2TestCase):

    def setUp(self):
        provider = (constants.BGPVPN +
                    ':dummy:networking_bgpvpn.neutron.services.'
                    'service_drivers.dummy.dummyBGPVPNDriverDB:default')

        bits = provider.split(':')
        provider = {
            'service_type': bits[0],
            'name': bits[1],
            'driver': bits[2]
        }
        if len(bits) == 4:
            provider['default'] = True
        # override the default service provider
        self.service_providers = (
            mock.patch.object(sdb.ServiceTypeManager,
                              'get_service_providers').start())
        self.service_providers.return_value = [provider]

        bgpvpn_plugin_str = ('networking_bgpvpn.neutron.services.plugin.'
                             'BGPVPNPlugin')
        service_plugins = {'bgpvpn_plugin': bgpvpn_plugin_str}

        bgpvpn_plugin = plugin.BGPVPNPlugin()
        extensions_path = ':'.join(extensions.__path__)
        ext_mgr = api_extensions.PluginAwareExtensionManager(
            extensions_path,
            {constants.BGPVPN: bgpvpn_plugin})

        super(BgpvpnTestCaseMixin, self).setUp(
            service_plugins=service_plugins,
            ext_mgr=ext_mgr)

    @contextlib.contextmanager
    def bgpvpn_conn(self, do_delete=True):
        network_id = _uuid()
        fmt = 'json'
        data = {
            'bgpvpn_connection': {'name': 'bgpvpn-connection1',
                                  'type': 'l3',
                                  'route_targets': ['1234:56'],
                                  'network_id': network_id,
                                  'auto_aggregate': False,
                                  'tenant_id': _uuid()}
        }
        bgpvpn_connection_req = self.new_create_request(
            'bgpvpn/bgpvpn-connections', data, fmt=fmt
        )
        res = bgpvpn_connection_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)
        bgpvpn_conn = self.deserialize('json', res)
        yield bgpvpn_conn
        if do_delete:
            self._delete('bgpvpn/bgpvpn-connections',
                         bgpvpn_conn['bgpvpn_connection']['id'])


class TestBGPVPNPlugin(BgpvpnTestCaseMixin):

    def setUp(self):
        super(TestBGPVPNPlugin, self).setUp()

    def test_create_bgpvpn_conn(self):
        with mock.patch.object(dummy.dummyBGPVPNDriverDB,
                               '_create_bgpvpn_connection') as mock_create:
            with self.bgpvpn_conn():
                mock_create.assert_called_once_with(
                    mock.ANY, mock.ANY)

    def test_delete_bgpvpn_conn(self):
        with mock.patch.object(dummy.dummyBGPVPNDriverDB,
                               '_delete_bgpvpn_connection') as mock_delete:
            with self.bgpvpn_conn(do_delete=False) as bgpvpn_conn:
                self._delete('bgpvpn/bgpvpn-connections',
                             bgpvpn_conn['bgpvpn_connection']['id'])
                mock_delete.assert_called_once_with(mock.ANY, mock.ANY)

    def test_update_bgpvpn_conn(self):
        with mock.patch.object(dummy.dummyBGPVPNDriverDB,
                               '_update_bgpvpn_connection') as mock_update:
            with self.bgpvpn_conn() as bgpvpn_conn:
                new_data = {"bgpvpn_connection": {"name": "foo"}}
                self._update('bgpvpn/bgpvpn-connections',
                             bgpvpn_conn['bgpvpn_connection']['id'],
                             new_data)
                mock_update.assert_called_once_with(
                    mock.ANY, mock.ANY, mock.ANY)
