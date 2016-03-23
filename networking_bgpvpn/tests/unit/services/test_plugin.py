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
import copy
import mock
import webob.exc

from oslo_utils import uuidutils

from neutron import manager

from neutron.api import extensions as api_extensions
from neutron.db import servicetype_db as sdb
from neutron import extensions as n_extensions
from neutron.tests.unit.db import test_db_base_plugin_v2
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions.test_l3 import TestL3NatServicePlugin

from networking_bgpvpn.neutron.db import bgpvpn_db
from networking_bgpvpn.neutron import extensions
from networking_bgpvpn.neutron.services.common import constants
from networking_bgpvpn.neutron.services import plugin
from networking_bgpvpn.neutron.services.service_drivers import driver_api

_uuid = uuidutils.generate_uuid


class BgpvpnTestCaseMixin(test_db_base_plugin_v2.NeutronDbPluginV2TestCase,
                          test_l3.L3NatTestCaseMixin):

    def setUp(self, service_provider=None, core_plugin=None):
        if not service_provider:
            provider = (constants.BGPVPN +
                        ':dummy:networking_bgpvpn.neutron.services.'
                        'service_drivers.driver_api.BGPVPNDriver:default')
        else:
            provider = (constants.BGPVPN + ':test:' + service_provider +
                        ':default')

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
        l3_plugin_str = ('neutron.tests.unit.extensions.test_l3.'
                         'TestL3NatServicePlugin')
        service_plugins = {'bgpvpn_plugin': bgpvpn_plugin_str,
                           'l3_plugin_name': l3_plugin_str}

        extensions_path = ':'.join(extensions.__path__ + n_extensions.__path__)

        # we need to provide a plugin instance, although
        # the extension manager will create a new instance
        # of the plugin
        ext_mgr = api_extensions.PluginAwareExtensionManager(
            extensions_path,
            {constants.BGPVPN: plugin.BGPVPNPlugin(),
             'l3_plugin_name': TestL3NatServicePlugin()})

        super(BgpvpnTestCaseMixin, self).setUp(
            plugin=core_plugin,
            service_plugins=service_plugins,
            ext_mgr=ext_mgr)

        # find the BGPVPN plugin that was instantiated by the
        # extension manager:
        self.bgpvpn_plugin = (manager.NeutronManager.get_service_plugins()
                              [constants.BGPVPN])

        self.bgpvpn_data = {'bgpvpn': {'name': 'bgpvpn1',
                                       'type': 'l3',
                                       'route_targets': ['1234:56'],
                                       'tenant_id': self._tenant_id}}
        self.converted_data = copy.copy(self.bgpvpn_data)
        self.converted_data['bgpvpn'].update({'export_targets': [],
                                              'import_targets': [],
                                              'route_distinguishers': []})

    @contextlib.contextmanager
    def bgpvpn(self, do_delete=True, **kwargs):
        fmt = 'json'
        if kwargs.get('data'):
            bgpvpn_data = kwargs.get('data')
        else:
            bgpvpn_data = copy.copy(self.bgpvpn_data)
            bgpvpn_data['bgpvpn'].update(kwargs)
        bgpvpn_req = self.new_create_request(
            'bgpvpn/bgpvpns', bgpvpn_data, fmt=fmt)
        res = bgpvpn_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)
        bgpvpn = self.deserialize('json', res)
        yield bgpvpn
        if do_delete:
            self._delete('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'])

    @contextlib.contextmanager
    def assoc_net(self, bgpvpn_id, net_id, do_disassociate=True):
        fmt = 'json'
        data = {'network_association': {'network_id': net_id,
                                        'tenant_id': self._tenant_id}}
        bgpvpn_net_req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=fmt,
            id=bgpvpn_id,
            subresource='network_associations')
        res = bgpvpn_net_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)
        assoc = self.deserialize('json', res)
        yield assoc
        if do_disassociate:
            del_req = self.new_delete_request(
                'bgpvpn/bgpvpns',
                bgpvpn_id,
                fmt=self.fmt,
                subresource='network_associations',
                sub_id=assoc['network_association']['id'])
            res = del_req.get_response(self.ext_api)
            if res.status_int >= 400:
                raise webob.exc.HTTPClientError(code=res.status_int)

    @contextlib.contextmanager
    def assoc_router(self, bgpvpn_id, router_id, do_disassociate=True):
        fmt = 'json'
        data = {'router_association': {'router_id': router_id,
                                       'tenant_id': self._tenant_id}}
        bgpvpn_router_req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=fmt,
            id=bgpvpn_id,
            subresource='router_associations')
        res = bgpvpn_router_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)
        assoc = self.deserialize('json', res)
        yield assoc
        if do_disassociate:
            del_req = self.new_delete_request(
                'bgpvpn/bgpvpns',
                bgpvpn_id,
                fmt=self.fmt,
                subresource='router_associations',
                sub_id=assoc['router_association']['id'])
            res = del_req.get_response(self.ext_api)
            if res.status_int >= 400:
                raise webob.exc.HTTPClientError(code=res.status_int)


class TestBGPVPNServicePlugin(BgpvpnTestCaseMixin):

    def setUp(self):
        super(TestBGPVPNServicePlugin, self).setUp()

    @mock.patch.object(plugin.BGPVPNPlugin, '_validate_network')
    def test_bgpvpn_net_assoc_create(self, mock_validate):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                mock_validate.return_value = net['network']
                with self.assoc_net(id, net_id):
                    net_body = {'network_id': net['network']['id'],
                                'tenant_id': self._tenant_id}
                    mock_validate.assert_called_once_with(mock.ANY,
                                                          net_body)

    def test_associate_empty_network(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            data = {}
            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='network_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_associate_unknown_network(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            net_id = _uuid()
            data = {'network_association': {'network_id': net_id,
                                            'tenant_id': self._tenant_id}}
            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='network_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNotFound.code)

    def test_associate_unauthorized_net(self):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn(tenant_id='another_tenant') as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'network_association': {'network_id': net_id,
                                                'tenant_id': self._tenant_id}}
                bgpvpn_net_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='network_associations')
                res = bgpvpn_net_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    def test_net_assoc_belong_to_diff_tenant(self):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'network_association': {'network_id': net_id,
                                                'tenant_id': 'another_tenant'}}
                bgpvpn_net_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='network_associations')
                res = bgpvpn_net_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    @mock.patch.object(plugin.BGPVPNPlugin, '_validate_router')
    def test_bgpvpn_router_assoc_create(self, mock_validate):
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                mock_validate.return_value = router['router']
                with self.assoc_router(id, router_id):
                    router_body = {'router_id': router['router']['id'],
                                   'tenant_id': self._tenant_id}
                    mock_validate.assert_called_once_with(mock.ANY,
                                                          router_body)

    def test_associate_empty_router(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            data = {}
            bgpvpn_router_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='router_associations')
            res = bgpvpn_router_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_associate_unknown_router(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            router_id = _uuid()
            data = {'router_association': {'router_id': router_id,
                                           'tenant_id': self._tenant_id}}
            bgpvpn_router_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='router_associations')
            res = bgpvpn_router_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNotFound.code)

    def test_associate_unauthorized_router(self):
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn(tenant_id='another_tenant') as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'router_association': {'router_id': router_id,
                                               'tenant_id': self._tenant_id}}
                bgpvpn_router_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='router_associations')
                res = bgpvpn_router_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    def test_associate_router_incorrect_bgpvpn_type(self):
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn(tenant_id='another_tenant',
                             type=constants.BGPVPN_L2) as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'router_association': {'router_id': router_id,
                                               'tenant_id': self._tenant_id}}
                bgpvpn_router_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='router_associations')
                res = bgpvpn_router_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def test_router_assoc_belong_to_diff_tenant(self):
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'router_association': {'router_id': router_id,
                                               'tenant_id': 'another_tenant'}}
                bgpvpn_router_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='router_associations')
                res = bgpvpn_router_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    def test_router_net_combination(self):
        with self.network() as net:
            with self.bgpvpn() as bgpvpn:
                with self.router(tenant_id=self._tenant_id) as router:
                    self._test_router_net_combination_validation(
                        net['network'],
                        router['router'],
                        bgpvpn['bgpvpn'])
        with self.network() as net:
            with self.bgpvpn() as bgpvpn:
                with self.router(tenant_id=self._tenant_id) as router:
                    self._test_net_router_combination_validation(
                        net['network'],
                        router['router'],
                        bgpvpn['bgpvpn'])

    def _test_router_net_combination_validation(self, network, router, bgpvpn):
        net_id = network['id']
        bgpvpn_id = bgpvpn['id']
        router_id = router['id']
        data = {'router_association': {'router_id': router_id,
                                       'tenant_id': self._tenant_id}}
        bgpvpn_router_req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=self.fmt,
            id=bgpvpn_id,
            subresource='router_associations')
        res = bgpvpn_router_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)

        with self.subnet(network={'network': network}) as subnet:
            data = {"subnet_id": subnet['subnet']['id']}
            bgpvpn_rtr_intf_req = self.new_update_request(
                'routers',
                data=data,
                fmt=self.fmt,
                id=router['id'],
                subresource='add_router_interface')
            res = bgpvpn_rtr_intf_req.get_response(self.ext_api)
            if res.status_int >= 400:
                raise webob.exc.HTTPClientError(code=res.status_int)

            data = {'network_association': {'network_id': net_id,
                                            'tenant_id': self._tenant_id}}
            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=bgpvpn_id,
                subresource='network_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)

    def _test_net_router_combination_validation(self, network, router, bgpvpn):
        net_id = network['id']
        bgpvpn_id = bgpvpn['id']
        router_id = router['id']

        data = {'network_association': {'network_id': net_id,
                                        'tenant_id': self._tenant_id}}
        bgpvpn_net_req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=self.fmt,
            id=bgpvpn_id,
            subresource='network_associations')
        res = bgpvpn_net_req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise webob.exc.HTTPClientError(code=res.status_int)

        with self.subnet(network={'network': network}) as subnet:
            data = {"subnet_id": subnet['subnet']['id']}
            bgpvpn_rtr_intf_req = self.new_update_request(
                'routers',
                data=data,
                fmt=self.fmt,
                id=router['id'],
                subresource='add_router_interface')
            res = bgpvpn_rtr_intf_req.get_response(self.ext_api)
            if res.status_int >= 400:
                raise webob.exc.HTTPClientError(code=res.status_int)

            data = {'router_association': {'router_id': router_id,
                                           'tenant_id': self._tenant_id}}
            bgpvpn_router_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=bgpvpn_id,
                subresource='router_associations')
            res = bgpvpn_router_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)


class TestBGPVPNServiceDriverDB(BgpvpnTestCaseMixin):

    def setUp(self):
        super(TestBGPVPNServiceDriverDB, self).setUp()

    def _raise_bgpvpn_driver_precommit_exc(self, *args, **kwargs):
            raise extensions.bgpvpn.BGPVPNDriverError(
                method='precommit method')

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_bgpvpn_postcommit')
    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_bgpvpn_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'create_bgpvpn')
    def test_create_bgpvpn(self, mock_create_db,
                           mock_create_precommit,
                           mock_create_postcommit):
        mock_create_db.return_value = self.converted_data['bgpvpn']
        with self.bgpvpn(do_delete=False):
            mock_create_db.assert_called_once_with(
                mock.ANY, self.converted_data['bgpvpn'])
            mock_create_precommit.assert_called_once_with(
                mock.ANY, self.converted_data['bgpvpn'])
            mock_create_postcommit.assert_called_once_with(
                mock.ANY, self.converted_data['bgpvpn'])

    def test_create_bgpvpn_precommit_fails(self):
        with mock.patch.object(driver_api.BGPVPNDriver,
                               'create_bgpvpn_precommit',
                               new=self._raise_bgpvpn_driver_precommit_exc):
            # Assert that an error is returned to the client
            bgpvpn_req = self.new_create_request(
                'bgpvpn/bgpvpns', self.bgpvpn_data)
            res = bgpvpn_req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPError.code,
                             res.status_int)

            # Assert that no bgpvpn has been created
            list = self._list('bgpvpn/bgpvpns', fmt='json')
            self.assertEqual([], list['bgpvpns'])

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'delete_bgpvpn_postcommit')
    def test_delete_bgpvpn(self, mock_delete_postcommit):
        with self.bgpvpn(do_delete=False) as bgpvpn:
            patcher = mock.patch.object(bgpvpn_db.BGPVPNPluginDb,
                                        'delete_bgpvpn',
                                        return_value=self.converted_data)
            mock_delete_db = patcher.start()

            self._delete('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'])
            mock_delete_db.assert_called_once_with(mock.ANY,
                                                   bgpvpn['bgpvpn']['id'])
            mock_delete_postcommit.assert_called_once_with(mock.ANY,
                                                           self.converted_data)
            patcher.stop()
            self._delete('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_bgpvpn')
    def test_get_bgpvpn(self, mock_get_db):
        with self.bgpvpn() as bgpvpn:
            self._show('bgpvpn/bgpvpns', bgpvpn['bgpvpn']['id'])
            mock_get_db.assert_called_once_with(mock.ANY,
                                                bgpvpn['bgpvpn']['id'],
                                                mock.ANY)

    def test_get_bgpvpn_with_net(self):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn() as bgpvpn:
                with self.assoc_net(bgpvpn['bgpvpn']['id'], net_id=net_id):
                    res = self._show('bgpvpn/bgpvpns', bgpvpn['bgpvpn']['id'])
                    self.assertIn('networks', res['bgpvpn'])
                    self.assertEqual(net_id,
                                     res['bgpvpn']['networks'][0])

    def test_get_bgpvpn_with_router(self):
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn() as bgpvpn:
                with self.assoc_router(bgpvpn['bgpvpn']['id'], router_id):
                    res = self._show('bgpvpn/bgpvpns', bgpvpn['bgpvpn']['id'])
                    self.assertIn('routers', res['bgpvpn'])
                    self.assertEqual(router_id, res['bgpvpn']['routers'][0])

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'update_bgpvpn_postcommit')
    @mock.patch.object(driver_api.BGPVPNDriver,
                       'update_bgpvpn_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb,
                       'update_bgpvpn')
    def test_update_bgpvpn(self, mock_update_db,
                           mock_update_precommit,
                           mock_update_postcommit):
        with self.bgpvpn() as bgpvpn:
            old_bgpvpn = copy.copy(self.bgpvpn_data['bgpvpn'])
            old_bgpvpn['id'] = bgpvpn['bgpvpn']['id']
            old_bgpvpn['networks'] = []
            old_bgpvpn['routers'] = []
            new_bgpvpn = copy.copy(old_bgpvpn)
            new_bgpvpn['name'] = 'foo'

            mock_update_db.return_value = new_bgpvpn

            new_data = {"bgpvpn": {"name": "foo"}}
            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         new_data)

            mock_update_db.assert_called_once_with(
                mock.ANY, bgpvpn['bgpvpn']['id'], new_data['bgpvpn'])
            mock_update_precommit.assert_called_once_with(
                mock.ANY, old_bgpvpn, new_bgpvpn)
            mock_update_postcommit.assert_called_once_with(
                mock.ANY, old_bgpvpn, new_bgpvpn)

    def test_update_bgpvpn_precommit_fails(self):
        with self.bgpvpn() as bgpvpn, \
            mock.patch.object(driver_api.BGPVPNDriver,
                              'update_bgpvpn_precommit',
                              new=self._raise_bgpvpn_driver_precommit_exc):
                new_data = {"bgpvpn": {"name": "foo"}}
                self._update('bgpvpn/bgpvpns',
                             bgpvpn['bgpvpn']['id'],
                             new_data,
                             expected_code=webob.exc.HTTPError.code)
                show_bgpvpn = self._show('bgpvpn/bgpvpns',
                                         bgpvpn['bgpvpn']['id'])
                self.assertEqual(self.bgpvpn_data['bgpvpn']['name'],
                                 show_bgpvpn['bgpvpn']['name'])

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_net_assoc_postcommit')
    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_net_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'create_net_assoc')
    def test_create_bgpvpn_net_assoc(self, mock_db_create_assoc,
                                     mock_pre_commit,
                                     mock_post_commit):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.network() as net:
                net_id = net['network']['id']
                assoc_id = _uuid()
                data = {'tenant_id': self._tenant_id,
                        'network_id': net_id}
                net_assoc_dict = copy.copy(data)
                net_assoc_dict.update({'id': assoc_id,
                                       'bgpvpn_id': bgpvpn_id})
                mock_db_create_assoc.return_value = net_assoc_dict
                with self.assoc_net(bgpvpn_id, net_id=net_id,
                                    do_disassociate=False):
                    mock_db_create_assoc.assert_called_once_with(
                        mock.ANY, bgpvpn_id, data)
                    mock_pre_commit.assert_called_once_with(mock.ANY,
                                                            net_assoc_dict)
                    mock_post_commit.assert_called_once_with(mock.ANY,
                                                             net_assoc_dict)

    def test_create_bgpvpn_net_assoc_precommit_fails(self):
        with self.bgpvpn() as bgpvpn, \
            self.network() as net, \
            mock.patch.object(driver_api.BGPVPNDriver,
                              'create_net_assoc_precommit',
                              new=self._raise_bgpvpn_driver_precommit_exc):
            fmt = 'json'
            data = {'network_association': {'network_id': net['network']['id'],
                                            'tenant_id': self._tenant_id}}
            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='network_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            # Assert that driver failure returns an error
            self.assertEqual(webob.exc.HTTPError.code,
                             res.status_int)
            # Assert that the bgpvpn is not associated to network
            bgpvpn_new = self._show('bgpvpn/bgpvpns',
                                    bgpvpn['bgpvpn']['id'])
            self.assertEqual([], bgpvpn_new['bgpvpn']['networks'])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_net_assoc')
    def test_get_bgpvpn_net_assoc(self, mock_get_db):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.network() as net:
                net_id = net['network']['id']
                with self.assoc_net(bgpvpn_id, net_id=net_id) as assoc:
                    assoc_id = assoc['network_association']['id']
                    res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                          '/network_associations'
                    self._show(res, assoc_id)
                    mock_get_db.assert_called_once_with(mock.ANY,
                                                        assoc_id,
                                                        bgpvpn_id,
                                                        [])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_net_assocs')
    def test_get_bgpvpn_net_assoc_list(self, mock_get_db):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.network() as net:
                net_id = net['network']['id']
                with self.assoc_net(bgpvpn_id, net_id=net_id):
                    res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                          '/network_associations'
                    self._list(res)
                    mock_get_db.assert_called_once_with(mock.ANY,
                                                        bgpvpn_id,
                                                        mock.ANY, mock.ANY)

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'delete_net_assoc_postcommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_net_assoc')
    def test_delete_bgpvpn_net_assoc(self, mock_db_del, mock_postcommit):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.network() as net:
                net_id = net['network']['id']
                with self.assoc_net(bgpvpn_id, net_id=net_id) as assoc:
                    assoc_id = assoc['network_association']['id']
                    net_assoc = {'id': assoc_id,
                                 'network_id': net_id,
                                 'bgpvpn_id': bgpvpn_id}
                    mock_db_del.return_value = net_assoc
            mock_db_del.assert_called_once_with(mock.ANY,
                                                assoc_id,
                                                bgpvpn_id)
            mock_postcommit.assert_called_once_with(mock.ANY,
                                                    net_assoc)

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_router_assoc_postcommit')
    @mock.patch.object(driver_api.BGPVPNDriver,
                       'create_router_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'create_router_assoc')
    def test_create_bgpvpn_router_assoc(self, mock_db_create_assoc,
                                        mock_pre_commit,
                                        mock_post_commit):
        with self.bgpvpn() as bgpvpn, \
            self.router(tenant_id=self._tenant_id) as router:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            router_id = router['router']['id']
            assoc_id = _uuid()
            data = {'tenant_id': self._tenant_id,
                    'router_id': router_id}
            router_assoc_dict = copy.copy(data)
            router_assoc_dict.update({'id': assoc_id,
                                      'bgpvpn_id': bgpvpn_id})
            mock_db_create_assoc.return_value = router_assoc_dict
            with self.assoc_router(bgpvpn_id, router_id=router_id,
                                   do_disassociate=False):
                mock_db_create_assoc.assert_called_once_with(
                    mock.ANY, bgpvpn_id, data)
                mock_pre_commit.assert_called_once_with(mock.ANY,
                                                        router_assoc_dict)
                mock_post_commit.assert_called_once_with(mock.ANY,
                                                         router_assoc_dict)

    def test_create_bgpvpn_router_assoc_precommit_fails(self):
        with self.bgpvpn() as bgpvpn, \
                self.router(tenant_id=self._tenant_id) as router, \
                mock.patch.object(driver_api.BGPVPNDriver,
                                  'create_router_assoc_precommit',
                                  new=self._raise_bgpvpn_driver_precommit_exc):
            fmt = 'json'
            data = {'router_association': {'router_id': router['router']['id'],
                                           'tenant_id': self._tenant_id}}
            bgpvpn_router_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='router_associations')
            res = bgpvpn_router_req.get_response(self.ext_api)
            # Assert that driver failure returns an error
            self.assertEqual(webob.exc.HTTPError.code,
                             res.status_int)
            # Assert that the bgpvpn is not associated to network
            bgpvpn_new = self._show('bgpvpn/bgpvpns',
                                    bgpvpn['bgpvpn']['id'])
            self.assertEqual([], bgpvpn_new['bgpvpn']['routers'])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_router_assoc')
    def test_get_bgpvpn_router_assoc(self, mock_get_db):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.router(tenant_id=self._tenant_id) as router:
                router_id = router['router']['id']
                with self.assoc_router(bgpvpn_id, router_id) as assoc:
                    assoc_id = assoc['router_association']['id']
                    res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                          '/router_associations'
                    self._show(res, assoc_id)
                    mock_get_db.assert_called_once_with(mock.ANY,
                                                        assoc_id,
                                                        bgpvpn_id,
                                                        [])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_router_assocs')
    def test_get_bgpvpn_router_assoc_list(self, mock_get_db):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.router(tenant_id=self._tenant_id) as router:
                router_id = router['router']['id']
                with self.assoc_router(bgpvpn_id, router_id):
                    res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                          '/router_associations'
                    self._list(res)
                    mock_get_db.assert_called_once_with(mock.ANY,
                                                        bgpvpn_id,
                                                        mock.ANY, mock.ANY)

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'delete_router_assoc_postcommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_router_assoc')
    def test_delete_bgpvpn_router_assoc(self, mock_db_del, mock_postcommit):
        with self.bgpvpn() as bgpvpn:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            with self.router(tenant_id=self._tenant_id) as router:
                router_id = router['router']['id']
                with self.assoc_router(bgpvpn_id, router_id) as assoc:
                    assoc_id = assoc['router_association']['id']
                    router_assoc = {'id': assoc_id,
                                    'router_id': router_id,
                                    'bgpvpn_id': bgpvpn_id}
                    mock_db_del.return_value = router_assoc
            mock_db_del.assert_called_once_with(mock.ANY,
                                                assoc_id,
                                                bgpvpn_id)
            mock_postcommit.assert_called_once_with(mock.ANY,
                                                    router_assoc)
