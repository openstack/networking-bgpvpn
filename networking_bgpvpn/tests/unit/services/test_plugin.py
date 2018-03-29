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

from neutron_lib.plugins import directory
from oslo_utils import uuidutils

from neutron.api import extensions as api_extensions
from neutron.db import servicetype_db as sdb
from neutron import extensions as n_extensions
from neutron.tests.unit.db import test_db_base_plugin_v2
from neutron.tests.unit.extensions import test_l3
from neutron.tests.unit.extensions.test_l3 import TestL3NatServicePlugin
from neutron_lib.api.definitions import bgpvpn as bgpvpn_def
from neutron_lib.api.definitions import bgpvpn_vni as bgpvpn_vni_def

from networking_bgpvpn.neutron.db import bgpvpn_db
from networking_bgpvpn.neutron import extensions
from networking_bgpvpn.neutron.services.common import constants
from networking_bgpvpn.neutron.services import plugin
from networking_bgpvpn.neutron.services.service_drivers import driver_api

_uuid = uuidutils.generate_uuid


def http_client_error(req, res):
    explanation = "Request '%s %s %s' failed: %s" % (req.method, req.url,
                                                     req.body, res.body)
    return webob.exc.HTTPClientError(code=res.status_int,
                                     explanation=explanation)


class TestBgpvpnDriverWithVni(driver_api.BGPVPNDriverRC):
    more_supported_extension_aliases = (
        driver_api.BGPVPNDriverRC.more_supported_extension_aliases +
        [bgpvpn_vni_def.ALIAS])

    def __init__(self, *args, **kwargs):
        super(TestBgpvpnDriverWithVni, self).__init__(*args, **kwargs)


class BgpvpnTestCaseMixin(test_db_base_plugin_v2.NeutronDbPluginV2TestCase,
                          test_l3.L3NatTestCaseMixin):

    def setUp(self, service_provider=None, core_plugin=None):
        if not service_provider:
            provider = (bgpvpn_def.ALIAS +
                        ':dummy:networking_bgpvpn.neutron.services.'
                        'service_drivers.driver_api.BGPVPNDriverRC:default')
        else:
            provider = (bgpvpn_def.ALIAS + ':test:' + service_provider +
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
            {bgpvpn_def.ALIAS: plugin.BGPVPNPlugin(),
             'l3_plugin_name': TestL3NatServicePlugin()})

        super(BgpvpnTestCaseMixin, self).setUp(
            plugin=core_plugin,
            service_plugins=service_plugins,
            ext_mgr=ext_mgr)

        # find the BGPVPN plugin that was instantiated by the
        # extension manager:
        self.bgpvpn_plugin = directory.get_plugin(bgpvpn_def.ALIAS)

        self.bgpvpn_data = {'bgpvpn': {'name': 'bgpvpn1',
                                       'type': 'l3',
                                       'route_targets': ['1234:56'],
                                       'tenant_id': self._tenant_id}}
        self.converted_data = copy.copy(self.bgpvpn_data)
        self.converted_data['bgpvpn'].update({'export_targets': [],
                                              'import_targets': [],
                                              'route_distinguishers': []})

    def add_tenant(self, data):
        data.update({
            "project_id": self._tenant_id,
            "tenant_id": self._tenant_id
        })

    @contextlib.contextmanager
    def bgpvpn(self, do_delete=True, **kwargs):
        req_data = copy.deepcopy(self.bgpvpn_data)

        fmt = 'json'
        if kwargs.get('data'):
            req_data = kwargs.get('data')
        else:
            req_data['bgpvpn'].update(kwargs)
        req = self.new_create_request(
            'bgpvpn/bgpvpns', req_data, fmt=fmt)
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)
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
        req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=fmt,
            id=bgpvpn_id,
            subresource='network_associations')
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)
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
                raise http_client_error(del_req, res)

    @contextlib.contextmanager
    def assoc_router(self, bgpvpn_id, router_id, do_disassociate=True):
        fmt = 'json'
        data = {'router_association': {'router_id': router_id,
                                       'tenant_id': self._tenant_id}}
        req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=fmt,
            id=bgpvpn_id,
            subresource='router_associations')
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)
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
                raise http_client_error(del_req, res)

    @contextlib.contextmanager
    def assoc_port(self, bgpvpn_id, port_id, do_disassociate=True, **kwargs):
        fmt = 'json'
        data = {'port_association': {'port_id': port_id,
                                     'tenant_id': self._tenant_id}}
        data['port_association'].update(kwargs)
        req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=fmt,
            id=bgpvpn_id,
            subresource='port_associations')
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)
        assoc = self.deserialize('json', res)
        yield assoc
        if do_disassociate:
            del_req = self.new_delete_request(
                'bgpvpn/bgpvpns',
                bgpvpn_id,
                fmt=self.fmt,
                subresource='port_associations',
                sub_id=assoc['port_association']['id'])
            res = del_req.get_response(self.ext_api)
            if res.status_int >= 400:
                raise http_client_error(del_req, res)

    def show_port_assoc(self, bgpvpn_id, port_assoc_id):
        req = self.new_show_request("bgpvpn/bgpvpns", bgpvpn_id,
                                    subresource="port_associations",
                                    sub_id=port_assoc_id)
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)
        return self.deserialize('json', res)


class TestBGPVPNServicePlugin(BgpvpnTestCaseMixin):

    def test_bgpvpn_net_assoc_create(self):
        with self.network() as net, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(
                    self.bgpvpn_plugin,
                    '_validate_network',
                    return_value=net['network']) as mock_validate, \
                self.assoc_net(bgpvpn['bgpvpn']['id'], net['network']['id']):
            mock_validate.assert_called_once_with(
                mock.ANY, net['network']['id'])

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

    def test_bgpvpn_router_assoc_create(self):
        with self.router(tenant_id=self._tenant_id) as router,\
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(
                    self.bgpvpn_plugin,
                    '_validate_router',
                    return_value=router['router']) as mock_validate, \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']):
            mock_validate.assert_called_once_with(
                mock.ANY, router['router']['id'])

    def test_bgpvpn_router_assoc_update(self):
        with self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(
                    self.bgpvpn_plugin,
                    '_validate_router',
                    return_value=router['router']), \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']) as router_assoc:

            bgpvpn_id = bgpvpn['bgpvpn']['id']

            updated = self._update('bgpvpn/bgpvpns/%s/router_associations' %
                                   bgpvpn_id,
                                   router_assoc['router_association']['id'],
                                   {'router_association':
                                       {'advertise_extra_routes': False}}
                                   )
            expected = {'router_association': {
                'id': router_assoc['router_association']['id'],
                'router_id': router['router']['id'],
                'advertise_extra_routes': False
            }}
            self.add_tenant(expected['router_association'])

            self.assertEqual(expected, updated)

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
        with self.network() as net,\
                self.bgpvpn() as bgpvpn, \
                self.router(tenant_id=self._tenant_id) as router:
            self._test_router_net_combination_validation(
                net['network'],
                router['router'],
                bgpvpn['bgpvpn'])
        with self.network() as net, \
                self.bgpvpn() as bgpvpn, \
                self.router(tenant_id=self._tenant_id) as router:
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
        req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=self.fmt,
            id=bgpvpn_id,
            subresource='router_associations')
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)

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
                raise http_client_error(bgpvpn_rtr_intf_req, res)

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
        req = self.new_create_request(
            'bgpvpn/bgpvpns',
            data=data,
            fmt=self.fmt,
            id=bgpvpn_id,
            subresource='network_associations')
        res = req.get_response(self.ext_api)
        if res.status_int >= 400:
            raise http_client_error(req, res)

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
                raise http_client_error(bgpvpn_rtr_intf_req, res)

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

    def test_attach_subnet_to_router_both_attached_to_bgpvpn(self):
        with self.network() as net,\
                self.bgpvpn() as bgpvpn,\
                self.router(tenant_id=self._tenant_id) as router,\
                self.subnet(network={'network': net['network']}) as subnet,\
                self.assoc_net(bgpvpn['bgpvpn']['id'], net['network']['id']),\
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']):
            # Attach subnet to router
            data = {"subnet_id": subnet['subnet']['id']}
            bgpvpn_rtr_intf_req = self.new_update_request(
                'routers',
                data=data,
                fmt=self.fmt,
                id=router['router']['id'],
                subresource='add_router_interface')
            res = bgpvpn_rtr_intf_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    def test_attach_port_to_router_both_attached_to_bgpvpn(self):
        with self.network() as net,\
                self.bgpvpn() as bgpvpn,\
                self.router(tenant_id=self._tenant_id) as router,\
                self.subnet(network={'network': net['network']}) as subnet,\
                self.port(subnet={'subnet': subnet['subnet']}) as port,\
                self.assoc_net(bgpvpn['bgpvpn']['id'], net['network']['id']),\
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']):
            # Attach subnet to router
            data = {"port_id": port['port']['id']}
            bgpvpn_rtr_intf_req = self.new_update_request(
                'routers',
                data=data,
                fmt=self.fmt,
                id=router['router']['id'],
                subresource='add_router_interface')
            res = bgpvpn_rtr_intf_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPConflict.code)

    @mock.patch.object(plugin.BGPVPNPlugin,
                       '_validate_port_association_routes_bgpvpn')
    def test_bgpvpn_port_assoc_create(self, mock_validate_port_assoc):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(
                    self.bgpvpn_plugin,
                    '_validate_port',
                    return_value=port['port']) as mock_validate, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id'],
                                advertise_fixed_ips=False,
                                routes=[{
                                    'type': 'prefix',
                                    'prefix': '12.1.3.0/24',
                                    }]):
            mock_validate.assert_called_once_with(
                mock.ANY, port['port']['id'])

            mock_validate_port_assoc.assert_called_once()

    def _test_bgpvpn_port_assoc_create_incorrect(self, **kwargs):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn:

            data = {'port_association': {'port_id': port['port']['id'],
                                         'tenant_id': self._tenant_id}}
            data['port_association'].update(kwargs)
            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='port_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            return res.body

    def test_bgpvpn_port_assoc_create_bgpvpn_route_non_existing(self):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn:

            data = {'port_association': {
                    'port_id': port['port']['id'],
                    'tenant_id': self._tenant_id,
                    'routes': [{
                        'type': 'bgpvpn',
                        'bgpvpn_id': '3aff9b6b-387b-4ffd-a9ff-a4bdffb349ff'
                        }]
                    }}

            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='port_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            self.assertIn("bgpvpn specified in route does not exist",
                          str(res.body))

    def test_bgpvpn_port_assoc_create_bgpvpn_route_wrong_tenant(self):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn, \
                self.bgpvpn(tenant_id="notus") as bgpvpn_other:

            data = {'port_association': {
                    'port_id': port['port']['id'],
                    'tenant_id': self._tenant_id,
                    'routes': [{
                        'type': 'bgpvpn',
                        'bgpvpn_id': bgpvpn_other['bgpvpn']['id']
                        }]
                    }}

            bgpvpn_net_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='port_associations')
            res = bgpvpn_net_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            self.assertIn("bgpvpn specified in route does not belong to "
                          "the tenant", str(res.body))

    def test_associate_empty_port(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            data = {}
            bgpvpn_port_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='port_associations')
            res = bgpvpn_port_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            self.assertIn("Resource body required", str(res.body))

    def test_associate_unknown_port(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            port_id = _uuid()
            data = {'port_association': {'port_id': port_id,
                                         'tenant_id': self._tenant_id}}
            bgpvpn_port_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=self.fmt,
                id=id,
                subresource='port_associations')
            res = bgpvpn_port_req.get_response(self.ext_api)
            self.assertEqual(res.status_int, webob.exc.HTTPNotFound.code)

    def test_associate_unauthorized_port(self):
        with self.port(tenant_id=self._tenant_id) as port:
            port_id = port['port']['id']
            with self.bgpvpn(tenant_id='another_tenant') as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'port_association': {'port_id': port_id,
                                             'tenant_id': self._tenant_id}}
                bgpvpn_port_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='port_associations')
                res = bgpvpn_port_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    def test_port_assoc_belong_to_diff_tenant(self):
        with self.port(tenant_id=self._tenant_id) as port:
            port_id = port['port']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                data = {'port_association': {'port_id': port_id,
                                             'tenant_id': 'another_tenant'}}
                bgpvpn_port_req = self.new_create_request(
                    'bgpvpn/bgpvpns',
                    data=data,
                    fmt=self.fmt,
                    id=id,
                    subresource='port_associations')
                res = bgpvpn_port_req.get_response(self.ext_api)
                self.assertEqual(res.status_int, webob.exc.HTTPForbidden.code)

    @mock.patch.object(plugin.BGPVPNPlugin,
                       '_validate_port_association_routes_bgpvpn')
    def test_bgpvpn_port_assoc_update(
            self,
            mock_validate):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as port_assoc:
            bgpvpn_id = bgpvpn['bgpvpn']['id']

            self._update('bgpvpn/bgpvpns/%s/port_associations' % bgpvpn_id,
                         port_assoc['port_association']['id'],
                         {'port_association': {'advertise_fixed_ips': False}}
                         )

            # one call for create, one call for update
            self.assertEqual(2, mock_validate.call_count)

    def test_bgpvpn_port_assoc_update_bgpvpn_route_wrong_tenant(self):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn() as bgpvpn, \
                self.bgpvpn(tenant_id="not-us") as bgpvpn_other, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as port_assoc:

            bgpvpn_id = bgpvpn['bgpvpn']['id']

            req = self.new_update_request(
                'bgpvpn/bgpvpns/%s/port_associations' % bgpvpn_id,
                {'port_association': {
                    'routes': [{
                        'type': 'bgpvpn',
                        'bgpvpn_id': bgpvpn_other['bgpvpn']['id']
                        }]
                    }
                 },
                port_assoc['port_association']['id']
            )

            res = req.get_response(self.ext_api)

            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            self.assertIn(
                "bgpvpn specified in route does not belong to the tenant",
                str(res.body))

    def test_bgpvpn_port_assoc_update_bgpvpn_route_wrong_type(self):
        with self.network() as net, \
                self.subnet(network={'network': net['network']}) as subnet, \
                self.port(subnet={'subnet': subnet['subnet']}) as port, \
                self.bgpvpn(type='l2') as bgpvpn_l2, \
                self.bgpvpn(type='l3') as bgpvpn_l3, \
                self.assoc_port(bgpvpn_l2['bgpvpn']['id'],
                                port['port']['id']) as port_assoc:

            bgpvpn_id = bgpvpn_l2['bgpvpn']['id']

            req = self.new_update_request(
                'bgpvpn/bgpvpns/%s/port_associations' % bgpvpn_id,
                {'port_association': {
                    'routes': [{
                        'type': 'bgpvpn',
                        'bgpvpn_id': bgpvpn_l3['bgpvpn']['id']
                        }]
                    }
                 },
                port_assoc['port_association']['id']
            )

            res = req.get_response(self.ext_api)

            self.assertEqual(res.status_int, webob.exc.HTTPBadRequest.code)
            self.assertIn("differing from type of associated BGPVPN",
                          str(res.body))


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
            self.assertTrue(mock_create_db.called)
            self.assertDictSupersetOf(
                self.converted_data['bgpvpn'],
                mock_create_db.call_args[0][1])
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

    def test_delete_bgpvpn_precommit_fails(self):
        with self.bgpvpn(do_delete=False) as bgpvpn, \
                mock.patch.object(bgpvpn_db.BGPVPNPluginDb,
                                  'delete_bgpvpn',
                                  return_value=self.converted_data), \
                mock.patch.object(driver_api.BGPVPNDriver,
                                  'delete_bgpvpn_precommit',
                                  new=self._raise_bgpvpn_driver_precommit_exc):
            bgpvpn_req = self.new_delete_request('bgpvpn/bgpvpns',
                                                 bgpvpn['bgpvpn']['id'])
            res = bgpvpn_req.get_response(self.ext_api)
            self.assertEqual(webob.exc.HTTPError.code,
                             res.status_int)
            # Assert that existing bgpvpn remains
            list = self._list('bgpvpn/bgpvpns', fmt='json')
            self.assertEqual([bgpvpn['bgpvpn']], list['bgpvpns'])

    @mock.patch.object(driver_api.BGPVPNDriver,
                       'delete_bgpvpn_postcommit')
    def test_delete_bgpvpn(self, mock_delete_postcommit):
        with self.bgpvpn(do_delete=False) as bgpvpn, \
                mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_bgpvpn') \
                as mock_delete_db, \
                mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_bgpvpn',
                                  return_value=self.converted_data):
            self._delete('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'])
            mock_delete_db.assert_called_once_with(mock.ANY,
                                                   bgpvpn['bgpvpn']['id'])
            mock_delete_postcommit.assert_called_once_with(mock.ANY,
                                                           self.converted_data)

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
            old_bgpvpn['ports'] = []
            old_bgpvpn['project_id'] = old_bgpvpn['tenant_id']
            old_bgpvpn['local_pref'] = None
            new_bgpvpn = copy.copy(old_bgpvpn)
            update = {'name': 'foo'}
            new_bgpvpn.update(update)

            mock_update_db.return_value = new_bgpvpn

            data = {"bgpvpn": {"name": new_bgpvpn['name']}}
            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         data)

            mock_update_db.assert_called_once_with(
                mock.ANY, bgpvpn['bgpvpn']['id'], data['bgpvpn'])
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
                    self.assertTrue(mock_db_create_assoc.called)
                    self.assertEqual(
                        bgpvpn_id, mock_db_create_assoc.call_args[0][1])
                    self.assertDictSupersetOf(
                        data,
                        mock_db_create_assoc.call_args[0][2])
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
                       'delete_net_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_net_assoc')
    def test_delete_bgpvpn_net_assoc_precommit_fails(self, mock_db_del,
                                                     mock_precommit):
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
                    mock_precommit.return_value = \
                        self._raise_bgpvpn_driver_precommit_exc
                    # Assert that existing bgpvpn and net-assoc remains
                    list = self._list('bgpvpn/bgpvpns', fmt='json')
                    bgpvpn['bgpvpn']['networks'] = [net_assoc['network_id']]
                    self.assertEqual([bgpvpn['bgpvpn']], list['bgpvpns'])

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
                    self.add_tenant(net_assoc)
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
                self.assertTrue(mock_db_create_assoc.called)
                self.assertEqual(
                    bgpvpn_id, mock_db_create_assoc.call_args[0][1])
                self.assertDictSupersetOf(
                    data,
                    mock_db_create_assoc.call_args[0][2])
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
                       'delete_router_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_router_assoc')
    def test_delete_bgpvpn_router_assoc_precommit_fails(self, mock_db_del,
                                                        mock_precommit):
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
                    mock_precommit.return_value = \
                        self._raise_bgpvpn_driver_precommit_exc
                    # Assert that existing bgpvpn and router-assoc remains
                    list = self._list('bgpvpn/bgpvpns', fmt='json')
                    bgpvpn['bgpvpn']['routers'] = [router_assoc['router_id']]
                    self.assertEqual([bgpvpn['bgpvpn']], list['bgpvpns'])

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
                                    'bgpvpn_id': bgpvpn_id,
                                    'advertise_extra_routes': True}
                    self.add_tenant(router_assoc)
                    mock_db_del.return_value = router_assoc

            # (delete triggered by exit from with statement)

            mock_db_del.assert_called_once_with(mock.ANY,
                                                assoc_id,
                                                bgpvpn_id)
            mock_postcommit.assert_called_once_with(mock.ANY,
                                                    router_assoc)

    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'create_port_assoc_postcommit')
    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'create_port_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'create_port_assoc')
    def test_create_bgpvpn_port_assoc(self, mock_db_create_assoc,
                                      mock_pre_commit,
                                      mock_post_commit):
        with self.bgpvpn() as bgpvpn, \
                self.network() as net,\
                self.subnet(network={'network': net['network']}) as subnet,\
                self.port(subnet={'subnet': subnet['subnet']},
                          tenant_id=self._tenant_id) as port:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            port_id = port['port']['id']
            assoc_id = _uuid()
            data = {'tenant_id': self._tenant_id,
                    'port_id': port_id}
            port_assoc_dict = copy.copy(data)
            port_assoc_dict.update({'id': assoc_id,
                                    'bgpvpn_id': bgpvpn_id})
            mock_db_create_assoc.return_value = port_assoc_dict
            with self.assoc_port(bgpvpn_id, port_id=port_id,
                                 do_disassociate=False):
                self.assertTrue(mock_db_create_assoc.called)
                self.assertEqual(
                    bgpvpn_id, mock_db_create_assoc.call_args[0][1])
                self.assertDictSupersetOf(
                    data,
                    mock_db_create_assoc.call_args[0][2])
                mock_pre_commit.assert_called_once_with(mock.ANY,
                                                        port_assoc_dict)
                mock_post_commit.assert_called_once_with(mock.ANY,
                                                         port_assoc_dict)

    def test_create_bgpvpn_port_assoc_precommit_fails(self):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                mock.patch.object(driver_api.BGPVPNDriverRC,
                                  'create_port_assoc_precommit',
                                  new=self._raise_bgpvpn_driver_precommit_exc):
            fmt = 'json'
            data = {'port_association': {'port_id': port['port']['id'],
                                         'tenant_id': self._tenant_id}}
            bgpvpn_port_req = self.new_create_request(
                'bgpvpn/bgpvpns',
                data=data,
                fmt=fmt,
                id=bgpvpn['bgpvpn']['id'],
                subresource='port_associations')
            res = bgpvpn_port_req.get_response(self.ext_api)
            # Assert that driver failure returns an error
            self.assertEqual(webob.exc.HTTPError.code,
                             res.status_int)
            # Assert that the bgpvpn is not associated to network
            bgpvpn_new = self._show('bgpvpn/bgpvpns',
                                    bgpvpn['bgpvpn']['id'])
            self.assertEqual([], bgpvpn_new['bgpvpn']['ports'])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_port_assoc')
    def test_get_bgpvpn_port_assoc(self, mock_get_db):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as assoc:
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            assoc_id = assoc['port_association']['id']
            res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                  '/port_associations'
            self._show(res, assoc_id)
            mock_get_db.assert_called_once_with(mock.ANY,
                                                assoc_id,
                                                bgpvpn_id,
                                                [])

    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'get_port_assocs')
    def test_get_bgpvpn_port_assoc_list(self, mock_get_db):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']):
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            res = 'bgpvpn/bgpvpns/' + bgpvpn_id + \
                  '/port_associations'
            self._list(res)
            mock_get_db.assert_called_once_with(mock.ANY,
                                                bgpvpn_id,
                                                mock.ANY, mock.ANY)

    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'delete_port_assoc_precommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_port_assoc')
    def test_delete_bgpvpn_port_assoc_precommit_fails(self, mock_db_del,
                                                      mock_precommit):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as assoc:
            port_id = port['port']['id']
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            assoc_id = assoc['port_association']['id']
            port_assoc = {'id': assoc_id,
                          'port_id': port_id,
                          'bgpvpn_id': bgpvpn_id}
            mock_db_del.return_value = port_assoc
            mock_precommit.return_value = \
                self._raise_bgpvpn_driver_precommit_exc
            # Assert that existing bgpvpn and port-assoc remains
            list = self._list('bgpvpn/bgpvpns', fmt='json')
            bgpvpn['bgpvpn']['ports'] = [port_assoc['port_id']]
            self.assertEqual([bgpvpn['bgpvpn']], list['bgpvpns'])

    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'update_port_assoc_precommit')
    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'update_port_assoc_postcommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'update_port_assoc')
    def test_update_bgpvpn_port_assoc(self, mock_db_update,
                                      mock_postcommit, mock_precommit):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as assoc:

            bgpvpn_id = bgpvpn['bgpvpn']['id']
            assoc_id = assoc['port_association']['id']

            assoc['port_association'].update({'bgpvpn_id': bgpvpn_id})

            new_port_assoc = copy.deepcopy(assoc)
            changed = {'advertise_fixed_ips': False}

            new_port_assoc['port_association'].update(changed)
            mock_db_update.return_value = new_port_assoc['port_association']

            data = {"port_association": changed}
            self._update('bgpvpn/bgpvpns/%s/port_associations' % bgpvpn_id,
                         assoc['port_association']['id'],
                         data)

            mock_db_update.assert_called_once_with(mock.ANY,
                                                   assoc_id,
                                                   bgpvpn_id,
                                                   data['port_association'])
            mock_precommit.assert_called_once_with(
                mock.ANY,
                assoc['port_association'],
                new_port_assoc['port_association']
                )
            mock_postcommit.assert_called_once_with(
                mock.ANY,
                assoc['port_association'],
                new_port_assoc['port_association']
                )

    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'delete_port_assoc_precommit')
    @mock.patch.object(driver_api.BGPVPNDriverRC,
                       'delete_port_assoc_postcommit')
    @mock.patch.object(bgpvpn_db.BGPVPNPluginDb, 'delete_port_assoc')
    def test_delete_bgpvpn_port_assoc(self, mock_db_del,
                                      mock_postcommit, mock_precommit):
        with self.bgpvpn() as bgpvpn, \
                self.port(tenant_id=self._tenant_id) as port, \
                self.assoc_port(bgpvpn['bgpvpn']['id'],
                                port['port']['id']) as assoc:
            port_id = port['port']['id']
            bgpvpn_id = bgpvpn['bgpvpn']['id']
            assoc_id = assoc['port_association']['id']

            port_assoc = {'id': assoc_id,
                          'bgpvpn_id': bgpvpn_id,
                          'port_id': port_id,
                          'routes': [],
                          'advertise_fixed_ips': True}
            self.add_tenant(port_assoc)
            mock_db_del.return_value = port_assoc

        # (delete triggered by exit from with statement)

        mock_db_del.assert_called_once_with(mock.ANY,
                                            assoc_id,
                                            bgpvpn_id)
        mock_precommit.assert_called_once_with(mock.ANY, port_assoc)
        mock_postcommit.assert_called_once_with(mock.ANY, port_assoc)
