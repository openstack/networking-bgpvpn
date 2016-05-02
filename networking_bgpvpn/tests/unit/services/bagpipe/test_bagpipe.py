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
import webob.exc

from neutron import context as n_context

from neutron.common.constants import DEVICE_OWNER_NETWORK_PREFIX
from neutron.common.constants import DEVICE_OWNER_ROUTER_INTF
from neutron.common.constants import PORT_STATUS_ACTIVE
from neutron.common.constants import PORT_STATUS_DOWN

from neutron.debug import debug_agent

from neutron.extensions import portbindings

from neutron import manager
from neutron.plugins.ml2 import config as ml2_config
from neutron.plugins.ml2 import rpc as ml2_rpc

from networking_bgpvpn.neutron.services.service_drivers.bagpipe import bagpipe
from networking_bgpvpn.tests.unit.services import test_plugin


class TestBagpipeCommon(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self, plugin=None):
        self.mocked_bagpipeAPI = mock.patch(
            'networking_bagpipe.agent.bgpvpn.rpc_client'
            '.BGPVPNAgentNotifyApi').start().return_value

        provider = ('networking_bgpvpn.neutron.services.service_drivers.'
                    'bagpipe.bagpipe.BaGPipeBGPVPNDriver')
        super(TestBagpipeCommon, self).setUp(service_provider=provider,
                                             core_plugin=plugin)

        self.ctxt = n_context.Context('fake_user', 'fake_project')

        n_dict = {"name": "netfoo",
                  "tenant_id": "fake_project",
                  "admin_state_up": True,
                  "router:external": True,
                  "shared": True}

        self.external_net = {'network':
                             self.plugin.create_network(self.ctxt,
                                                        {'network': n_dict})}


class TestBagpipeServiceDriver(TestBagpipeCommon):

    def test_create_bgpvpn_l2_fails(self):
        bgpvpn_data = copy.copy(self.bgpvpn_data['bgpvpn'])
        bgpvpn_data.update({"type": "l2"})

        # Assert that an error is returned to the client
        bgpvpn_req = self.new_create_request(
            'bgpvpn/bgpvpns', bgpvpn_data)
        res = bgpvpn_req.get_response(self.ext_api)
        self.assertEqual(webob.exc.HTTPBadRequest.code,
                         res.status_int)

    def test_create_bgpvpn_rds_fails(self):
        bgpvpn_data = copy.copy(self.bgpvpn_data)
        bgpvpn_data['bgpvpn'].update({"route_distinguishers": ["4444:55"]})

        # Assert that an error is returned to the client
        bgpvpn_req = self.new_create_request(
            'bgpvpn/bgpvpns', bgpvpn_data)
        res = bgpvpn_req.get_response(self.ext_api)
        self.assertEqual(webob.exc.HTTPBadRequest.code,
                         res.status_int)

    def test_bagpipe_update_bgpvpn_rds_fails(self):
        with self.bgpvpn() as bgpvpn:
            update_data = {'bgpvpn': {"route_distinguishers": ["4444:55"]}}

            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         update_data,
                         expected_code=webob.exc.HTTPBadRequest.code)
            show_bgpvpn = self._show('bgpvpn/bgpvpns',
                                     bgpvpn['bgpvpn']['id'])
            self.assertEqual([],
                             show_bgpvpn['bgpvpn']['route_distinguishers'])

    def test_bagpipe_associate_net(self):
        mocked_update = self.mocked_bagpipeAPI.update_bgpvpn
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                mocked_update.reset_mock()
                with self.assoc_net(id, net_id):
                    formatted_bgpvpn = {'id': id,
                                        'network_id': net_id,
                                        'l3vpn':
                                        {'import_rt': rt,
                                         'export_rt': rt}}
                    mocked_update.assert_called_once_with(mock.ANY,
                                                          formatted_bgpvpn)

    def test_bagpipe_associate_external_net_failed(self):
        net_id = self.external_net['network']['id']
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

    def test_bagpipe_associate_router(self):
        mocked_update = self.mocked_bagpipeAPI.update_bgpvpn
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.subnet() as subnet:
                with self.port(subnet=subnet) as port:
                    net_id = port['port']['network_id']
                    subnet_id = subnet['subnet']['id']
                    self._router_interface_action('add', router_id,
                                                  subnet_id, None)

                    with self.bgpvpn() as bgpvpn:
                        id = bgpvpn['bgpvpn']['id']
                        rt = bgpvpn['bgpvpn']['route_targets']
                        mocked_update.reset_mock()
                        with self.assoc_router(id, router_id):
                            formatted_bgpvpn = {'id': id,
                                                'network_id': net_id,
                                                'l3vpn': {
                                                    'import_rt': rt,
                                                    'export_rt': rt}}
                            mocked_update.assert_called_once_with(
                                mock.ANY, formatted_bgpvpn)

    def test_bagpipe_disassociate_net(self):
        mocked_delete = self.mocked_bagpipeAPI.delete_bgpvpn
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                with self.assoc_net(id, net_id,
                                    do_disassociate=False) as assoc:
                    mocked_delete.reset_mock()
                    del_req = self.new_delete_request(
                        'bgpvpn/bgpvpns',
                        id,
                        fmt=self.fmt,
                        subresource='network_associations',
                        sub_id=assoc['network_association']['id'])
                    res = del_req.get_response(self.ext_api)
                    if res.status_int >= 400:
                        raise webob.exc.HTTPClientError(code=res.status_int)

                    formatted_bgpvpn = {'id': id,
                                        'network_id': net_id,
                                        'l3vpn':
                                        {'import_rt': rt,
                                         'export_rt': rt}}
                    mocked_delete.assert_called_once_with(mock.ANY,
                                                          formatted_bgpvpn)

    def test_bagpipe_update_bgpvpn_rt(self):
        mocked_update = self.mocked_bagpipeAPI.update_bgpvpn
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = ['6543:21']
                with self.assoc_net(id, net_id):
                    formatted_bgpvpn = {'id': id,
                                        'network_id': net_id,
                                        'l3vpn':
                                        {'import_rt': rt,
                                         'export_rt': rt}}
                    update_data = {'bgpvpn': {'route_targets': ['6543:21']}}
                    mocked_update.reset_mock()
                    self._update('bgpvpn/bgpvpns',
                                 bgpvpn['bgpvpn']['id'],
                                 update_data)
                    mocked_update.assert_called_once_with(mock.ANY,
                                                          formatted_bgpvpn)

    def test_bagpipe_delete_bgpvpn(self):
        mocked_delete = self.mocked_bagpipeAPI.delete_bgpvpn
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn(do_delete=False) as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                mocked_delete.reset_mock()
                with self.assoc_net(id, net_id, do_disassociate=False):
                    self._delete('bgpvpn/bgpvpns', id)
                    formatted_bgpvpn = {'id': id,
                                        'network_id': net_id,
                                        'l3vpn':
                                        {'import_rt': rt,
                                         'export_rt': rt}}
                    mocked_delete.assert_called_once_with(mock.ANY,
                                                          formatted_bgpvpn)

    def test_bagpipe_callback_to_rpc_update_port_after_router_itf_added(self):
        driver = self.bgpvpn_plugin.driver
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn:
            self._router_interface_action('add',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            with self.assoc_router(bgpvpn['bgpvpn']['id'],
                                   router['router']['id']), \
                    self.port(subnet=subnet) as port:
                context = n_context.Context(user_id='fake_user',
                                            tenant_id=self._tenant_id)
                mac_address = port['port']['mac_address']
                formatted_ip = (port['port']['fixed_ips'][0]['ip_address'] +
                                '/' + subnet['subnet']['cidr'].split('/')[-1])
                expected = {
                    'gateway_ip': subnet['subnet']['gateway_ip'],
                    'mac_address': mac_address,
                    'ip_address': formatted_ip
                }
                expected.update(driver._format_bgpvpn_network_route_targets(
                    [bgpvpn['bgpvpn']]))

                actual = driver._retrieve_bgpvpn_network_info_for_port(
                    context, port['port'])

                self.assertEqual(expected, actual)


TESTHOST = 'testhost'


BGPVPN_INFO = {'mac_address': 'de:ad:00:00:be:ef',
               'ip_address': '10.0.0.2',
               'gateway_ip': '10.0.0.1',
               'l3vpn': {'import_rt': ['12345:1'],
                         'export_rt': ['12345:1']
                         }
               }


class TestBagpipeServiceDriverCallbacks(TestBagpipeCommon):
    '''Check that receiving callbacks results in RPC calls to the agent'''

    _plugin_name = 'neutron.plugins.ml2.plugin.Ml2Plugin'

    def setUp(self):
        ml2_config.cfg.CONF.set_override('mechanism_drivers',
                                         ['logger', 'test', 'fake_agent'],
                                         'ml2')

        super(TestBagpipeServiceDriverCallbacks, self).setUp(self._plugin_name)

        self.port_create_status = 'DOWN'
        self.plugin = manager.NeutronManager.get_plugin()
        self.plugin.start_rpc_listeners()

        self.bagpipe_driver = self.bgpvpn_plugin.driver

        self.patched_driver = mock.patch.object(
            self.bgpvpn_plugin.driver,
            '_retrieve_bgpvpn_network_info_for_port',
            return_value=BGPVPN_INFO)
        self.patched_driver.start()

        self.mock_attach_rpc = self.mocked_bagpipeAPI.attach_port_on_bgpvpn
        self.mock_detach_rpc = self.mocked_bagpipeAPI.detach_port_from_bgpvpn
        self.mock_update_bgpvpn_rpc = self.mocked_bagpipeAPI.update_bgpvpn
        self.mock_delete_bgpvpn_rpc = self.mocked_bagpipeAPI.delete_bgpvpn

    def _build_expected_return_active(self, port):
        bgpvpn_info_port = BGPVPN_INFO.copy()
        bgpvpn_info_port.update({'id': port['id'],
                                 'network_id': port['network_id']})
        return bgpvpn_info_port

    def _build_expected_return_down(self, port):
        return {'id': port['id'],
                'network_id': port['network_id']}

    def _update_port_status(self, port, status):
        network_id = port['port']['network_id']
        some_network = {'id': network_id}
        self.plugin.get_network = mock.Mock(return_value=some_network)

        self.plugin.update_port_status(self.ctxt, port['port']['id'],
                                       status, TESTHOST)

    def test_bagpipe_callback_to_rpc_update_down2active(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:

            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_DOWN,
                               'device_owner': "foo"}
            )
            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                TESTHOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active2down(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:

            self._update_port_status(port, PORT_STATUS_DOWN)

            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_ACTIVE,
                               'device_owner': "foo"}
            )
            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                TESTHOST)
            self.assertFalse(self.mock_attach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active2active(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:

            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_ACTIVE,
                               'device_owner': "foo"}
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down2down(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:

            self._update_port_status(port, PORT_STATUS_DOWN)

            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_DOWN,
                               'device_owner': "foo"}
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_DOWN)
            self.bagpipe_driver.registry_port_deleted(
                None, None, None,
                context=self.ctxt,
                port_id=port['port']['id']
            )
            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                TESTHOST)
            self.assertFalse(self.mock_attach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active_ignore_net_ports(self):
        with self.port(device_owner=DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_dont_ignore_probe_ports_compute(self):
        with self.port(device_owner=debug_agent.DEVICE_OWNER_COMPUTE_PROBE,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_DOWN,
                               'device_owner': "foo"}
            )
            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                TESTHOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_dont_ignore_probe_ports_network(self):
        with self.port(device_owner=debug_agent.DEVICE_OWNER_NETWORK_PROBE,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port={'status': PORT_STATUS_DOWN,
                               'device_owner': "foo"}
            )
            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                TESTHOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down_ignore_net_ports(self):
        with self.port(device_owner=DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_DOWN)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted_ignore_net_ports(self):
        with self.port(device_owner=DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_DOWN)
            self.bagpipe_driver.registry_port_deleted(
                None, None, None,
                context=self.ctxt,
                port_id=port['port']['id']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active_ignore_external_net(self):
        with self.subnet(network=self.external_net) as subnet, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_ACTIVE)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down_ignore_external_net(self):
        with self.subnet(network=self.external_net) as subnet, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_DOWN)
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted_ignore_external_net(self):
        with self.subnet(network=self.external_net) as subnet, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: TESTHOST}) as port:
            self._update_port_status(port, PORT_STATUS_DOWN)
            self.bagpipe_driver.registry_port_deleted(
                None, None, None,
                context=self.ctxt,
                port_id=port['port']['id']
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_delete_port_to_bgpvpn_rpc(self):
        with self.network() as net, \
            self.subnet(network=net) as subnet, \
            self.port(subnet=subnet) as port, \
            mock.patch.object(self.plugin, 'get_port',
                              return_value=port['port']), \
            mock.patch.object(self.plugin, 'get_network',
                              return_value=net['network']):

            port['port'].update({'binding:host_id': TESTHOST})

            self.plugin.delete_port(self.ctxt, port['port']['id'])

            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                TESTHOST)

    def test_bagpipe_callback_to_rpc_update_port_router_itf_added(self):
        with self.port() as port, \
                self.router(tenant_id=self._tenant_id) as router, \
                mock.patch.object(self.bagpipe_driver, '_get_port_host',
                                  return_value=TESTHOST), \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(self.bagpipe_driver, 'get_bgpvpn',
                                  return_value=bgpvpn['bgpvpn']),\
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            original_port = copy.deepcopy(port['port'])
            port['port']['device_owner'] = DEVICE_OWNER_ROUTER_INTF
            port['port']['device_id'] = router['router']['id']
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port=original_port
            )
            self.mock_update_bgpvpn_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(bgpvpn['bgpvpn'],
                                                   port['port']['network_id']))

    def test_bagpipe_callback_to_rpc_update_port_router_itf_removed(self):
        with self.port() as port, \
                self.router(tenant_id=self._tenant_id) as router, \
                mock.patch.object(self.bagpipe_driver, '_get_port_host',
                                  return_value=TESTHOST), \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(self.bagpipe_driver, 'get_bgpvpn',
                                  return_value=bgpvpn['bgpvpn']),\
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            original_port = copy.deepcopy(port['port'])
            original_port['device_owner'] = DEVICE_OWNER_ROUTER_INTF
            original_port['device_id'] = router['router']['id']
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=port['port'],
                original_port=original_port
            )
            self.mock_delete_bgpvpn_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(bgpvpn['bgpvpn'],
                                                   port['port']['network_id']))

    def test_l3agent_add_remove_router_interface_to_bgpvpn_rpc(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            self._router_interface_action('add',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            self.mock_update_bgpvpn_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(bgpvpn['bgpvpn'],
                                                   net['network']['id']))
            self._router_interface_action('remove',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            self.mock_delete_bgpvpn_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(bgpvpn['bgpvpn'],
                                                   net['network']['id']))

    def test_l2agent_rpc_to_bgpvpn_rpc(self):
        #
        # Test that really simulate the ML2 codepath that
        # generate the registry events.

        ml2_rpc_callbacks = ml2_rpc.RpcCallbacks(mock.Mock(), mock.Mock())

        n_dict = {"name": "netfoo",
                  "tenant_id": "fake_project",
                  "admin_state_up": True,
                  "shared": False}

        net = self.plugin.create_network(self.ctxt, {'network': n_dict})

        subnet_dict = {'name': 'test_subnet',
                       'tenant_id': 'fake_project',
                       'ip_version': 4,
                       'cidr': '10.0.0.0/24',
                       'allocation_pools': [{'start': '10.0.0.2',
                                             'end': '10.0.0.254'}],
                       'enable_dhcp': False,
                       'dns_nameservers': [],
                       'host_routes': [],
                       'network_id': net['id']}

        self.plugin.create_subnet(self.ctxt, {'subnet': subnet_dict})

        p_dict = {'network_id': net['id'],
                  'tenant_id': "fake_project",
                  'name': 'fooport',
                  "admin_state_up": True,
                  "device_id": "tapfoo",
                  "device_owner": "not_me",
                  "mac_address": "de:ad:00:00:be:ef",
                  "fixed_ips": [],
                  "binding:host_id": TESTHOST,
                  }

        port = self.plugin.create_port(self.ctxt, {'port': p_dict})

        self.plugin.update_dvr_port_binding(self.ctxt,
                                            port['id'], {'port': p_dict})

        ml2_rpc_callbacks.update_device_up(self.ctxt,
                                           host=TESTHOST,
                                           agent_id='fooagent',
                                           device="de:ad:00:00:be:ef")

        self.mock_attach_rpc.assert_called_once_with(
            mock.ANY,
            self._build_expected_return_active(port),
            TESTHOST)

        # The test below currently fails, because there is
        # no registry event for Port down (in Neutron stable/liberty)
#             ml2_rpc_callbacks.update_device_down(self.ctxt,
#                                                  host=TESTHOST,
#                                                  agent_id='fooagent',
#                                                  device="de:ad:00:00:be:ef")
#
#             self.mock_detach_rpc.assert_called_once_with(
#                 mock.ANY,
#                 self._build_expected_return_down(port),
#                 TESTHOST)

        self.plugin.delete_port(self.ctxt, port['id'])

        self.mock_detach_rpc.assert_called_once_with(
            mock.ANY,
            self._build_expected_return_down(port),
            TESTHOST)

    def test_exception_on_callback(self):
        with mock.patch.object(bagpipe.LOG, 'exception') as log_exc:
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=self.ctxt,
                port=None
            )
            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)
            self.assertTrue(log_exc.called)
