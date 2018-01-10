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

from oslo_config import cfg

from neutron.api.rpc.handlers import resources_rpc
from neutron.db import agents_db
from neutron.db import db_base_plugin_v2
from neutron.debug import debug_agent
from neutron.plugins.ml2 import plugin as ml2_plugin
from neutron.plugins.ml2 import rpc as ml2_rpc
from neutron.tests.common import helpers

from neutron_lib.api.definitions import portbindings
from neutron_lib import constants as const
from neutron_lib import context as n_context
from neutron_lib.plugins import directory

from networking_bgpvpn.neutron.services.service_drivers.bagpipe import bagpipe
from networking_bgpvpn.tests.unit.services import test_plugin

from networking_bagpipe.objects import bgpvpn as objs


def _expected_formatted_bgpvpn(id, net_id, rt=None, gateway_mac=None):
        return {'id': id,
                'network_id': net_id,
                'l3vpn': {'import_rt': rt or mock.ANY,
                          'export_rt': rt or mock.ANY},
                'gateway_mac': gateway_mac or mock.ANY}


class TestCorePluginWithAgents(db_base_plugin_v2.NeutronDbPluginV2,
                               agents_db.AgentDbMixin):
    pass


class TestBagpipeCommon(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self, plugin=None,
              driver=('networking_bgpvpn.neutron.services.service_drivers.'
                      'bagpipe.bagpipe.BaGPipeBGPVPNDriver')):
        self.mocked_rpc = mock.patch(
            'networking_bagpipe.agent.bgpvpn.rpc_client'
            '.BGPVPNAgentNotifyApi').start().return_value

        self.mock_attach_rpc = self.mocked_rpc.attach_port_on_bgpvpn
        self.mock_detach_rpc = self.mocked_rpc.detach_port_from_bgpvpn
        self.mock_update_rpc = self.mocked_rpc.update_bgpvpn
        self.mock_delete_rpc = self.mocked_rpc.delete_bgpvpn

        mock.patch(
            'neutron.common.rpc.get_client').start().return_value

        if not plugin:
            plugin = '%s.%s' % (__name__, TestCorePluginWithAgents.__name__)

        super(TestBagpipeCommon, self).setUp(service_provider=driver,
                                             core_plugin=plugin)

        self.ctxt = n_context.Context('fake_user', self._tenant_id)

        n_dict = {"name": "netfoo",
                  "tenant_id": self._tenant_id,
                  "admin_state_up": True,
                  "router:external": True,
                  "shared": True}

        self.external_net = {'network':
                             self.plugin.create_network(self.ctxt,
                                                        {'network': n_dict})}


class AnyOfClass(object):

    def __init__(self, cls):
        self._class = cls

    def __eq__(self, other):
        return isinstance(other, self._class)

    def __repr__(self):
        return "AnyOfClass<%s>" % self._class.__name__


class TestBagpipeOVOPushPullMixin(object):
    # tests for OVO-based push notifications go here

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_bgpvpn_update_name_only(self, mocked_push):
        with self.bgpvpn() as bgpvpn:
            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         {'bgpvpn': {'name': 'newname'}})
            # check that no RPC push is done for BGPVPN objects
            self.assertTrue(
                mocked_push.call_count == 0 or
                (not any([isinstance(ovo, objs.BGPVPNNetAssociation)
                          for ovo in mocked_push.mock_calls[0][1][1]]) and
                 not any([isinstance(ovo, objs.BGPVPNRouterAssociation)
                          for ovo in mocked_push.mock_calls[0][1][1]])
                 )
            )

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_bgpvpn_update_rts_no_assoc(self, mocked_push):
        with self.bgpvpn() as bgpvpn:
            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         {'bgpvpn': {'route_targets': ['64512:43']}})
            # check that no RPC push is done for BGPVPN objects
            self.assertTrue(
                mocked_push.call_count == 0 or
                (not any([isinstance(ovo, objs.BGPVPNNetAssociation)
                          for ovo in mocked_push.mock_calls[0][1][1]]) and
                 not any([isinstance(ovo, objs.BGPVPNRouterAssociation)
                          for ovo in mocked_push.mock_calls[0][1][1]])
                 )
            )

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, '_push')
    def test_bgpvpn_update_delete_rts_with_assocs(self, mocked_push):
        with self.bgpvpn(do_delete=False) as bgpvpn, \
                self.network() as net, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.assoc_net(bgpvpn['bgpvpn']['id'],
                               net['network']['id'],
                               do_disassociate=False), \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id'],
                                  do_disassociate=False):
            mocked_push.reset_mock()
            self._update('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'],
                         {'bgpvpn': {'route_targets': ['64512:43']}})

            mocked_push.assert_any_call(mock.ANY, 'BGPVPNNetAssociation',
                                        mock.ANY, 'updated')
            mocked_push.assert_any_call(mock.ANY, 'BGPVPNRouterAssociation',
                                        mock.ANY, 'updated')

            mocked_push.reset_mock()

            # delete BGPVPN
            self._delete('bgpvpn/bgpvpns',
                         bgpvpn['bgpvpn']['id'])

            # after delete
            mocked_push.assert_any_call(mock.ANY, 'BGPVPNNetAssociation',
                                        mock.ANY, 'deleted')
            mocked_push.assert_any_call(mock.ANY, 'BGPVPNRouterAssociation',
                                        mock.ANY, 'deleted')

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_net_assoc_create_delete(self, mocked_push):
        with self.network() as net, \
                self.bgpvpn() as bgpvpn:
            mocked_push.reset_mock()
            with self.assoc_net(bgpvpn['bgpvpn']['id'],
                                net['network']['id']):

                mocked_push.assert_called_once_with(mock.ANY, mock.ANY,
                                                    'created')

                ovos_in_call = mocked_push.mock_calls[0][1][1]

                self.assertEqual(
                    [AnyOfClass(objs.BGPVPNNetAssociation)],
                    ovos_in_call
                    )

                mocked_push.reset_mock()

            # after net assoc delete
            mocked_push.assert_called_once_with(mock.ANY, mock.ANY, 'deleted')

            ovos_in_call = mocked_push.mock_calls[0][1][1]

            self.assertEqual(
                [AnyOfClass(objs.BGPVPNNetAssociation)],
                ovos_in_call
                )

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_router_assoc_create_delete(self, mocked_push):
        with self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn:
            mocked_push.reset_mock()
            with self.assoc_router(bgpvpn['bgpvpn']['id'],
                                   router['router']['id']):

                mocked_push.assert_called_once_with(mock.ANY, mock.ANY,
                                                    'created')

                ovos_in_call = mocked_push.mock_calls[0][1][1]

                self.assertEqual(
                    [AnyOfClass(objs.BGPVPNRouterAssociation)],
                    ovos_in_call
                    )

                mocked_push.reset_mock()

            # after router assoc delete
            mocked_push.assert_called_once_with(mock.ANY, mock.ANY, 'deleted')

            ovos_in_call = mocked_push.mock_calls[0][1][1]

            self.assertEqual(
                [AnyOfClass(objs.BGPVPNRouterAssociation)],
                ovos_in_call
                )

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_port_assoc_crud(self, mocked_push):
        with self.port() as port, \
                self.bgpvpn() as bgpvpn:
            mocked_push.reset_mock()
            with self.assoc_port(bgpvpn['bgpvpn']['id'],
                                 port['port']['id']) as port_assoc:

                mocked_push.assert_called_once_with(mock.ANY, mock.ANY,
                                                    'created')

                ovos_in_call = mocked_push.mock_calls[0][1][1]

                self.assertEqual(
                    [AnyOfClass(objs.BGPVPNPortAssociation)],
                    ovos_in_call
                    )

                mocked_push.reset_mock()

                self._update(
                    ('bgpvpn/bgpvpns/%s/port_associations' %
                     bgpvpn['bgpvpn']['id']),
                    port_assoc['port_association']['id'],
                    {'port_association': {'advertise_fixed_ips': False}})

                mocked_push.assert_called_once_with(mock.ANY, mock.ANY,
                                                    'updated')

                ovos_in_call = mocked_push.mock_calls[0][1][1]

                self.assertEqual(
                    [AnyOfClass(objs.BGPVPNPortAssociation)],
                    ovos_in_call
                    )

                mocked_push.reset_mock()

            # after port assoc delete
            mocked_push.assert_called_once_with(mock.ANY, mock.ANY, 'deleted')

            ovos_in_call = mocked_push.mock_calls[0][1][1]

            self.assertEqual(
                [AnyOfClass(objs.BGPVPNPortAssociation)],
                ovos_in_call
                )


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
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                self.mock_update_rpc.reset_mock()
                with self.assoc_net(id, net_id):
                    self.mock_update_rpc.assert_called_once_with(
                        mock.ANY,
                        _expected_formatted_bgpvpn(id, net_id, rt))

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
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.subnet() as subnet:
                with self.port(subnet=subnet) as port:
                    net_id = port['port']['network_id']
                    subnet_id = subnet['subnet']['id']
                    itf = self._router_interface_action('add', router_id,
                                                        subnet_id, None)

                    itf_port = self.plugin.get_port(self.ctxt, itf['port_id'])

                    with self.bgpvpn() as bgpvpn:
                        id = bgpvpn['bgpvpn']['id']
                        rt = bgpvpn['bgpvpn']['route_targets']
                        self.mock_update_rpc.reset_mock()
                        with self.assoc_router(id, router_id):
                            self.mock_update_rpc.assert_called_once_with(
                                mock.ANY,
                                _expected_formatted_bgpvpn(
                                    id, net_id,
                                    rt,
                                    itf_port['mac_address']))

    def test_bagpipe_disassociate_net(self):
        mocked_delete = self.mocked_rpc.delete_bgpvpn
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

                    mocked_delete.assert_called_once_with(
                        mock.ANY,
                        _expected_formatted_bgpvpn(id, net_id, rt))

    def test_bagpipe_update_bgpvpn_rt(self):
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = ['6543:21']
                with self.assoc_net(id, net_id):
                    update_data = {'bgpvpn': {'route_targets': ['6543:21']}}
                    self.mock_update_rpc.reset_mock()
                    self._update('bgpvpn/bgpvpns',
                                 bgpvpn['bgpvpn']['id'],
                                 update_data)
                    self.mock_update_rpc.assert_called_once_with(
                        mock.ANY,
                        _expected_formatted_bgpvpn(id, net_id, rt))

    def test_bagpipe_update_bgpvpn_with_router_assoc(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']), \
                self.port(subnet=subnet):
            self._router_interface_action('add',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            update_data = {'bgpvpn': {'route_targets': ['6543:21']}}
            self.mock_update_rpc.reset_mock()
            self._update('bgpvpn/bgpvpns', bgpvpn['bgpvpn']['id'], update_data)
            self.mock_update_rpc.assert_called_once_with(
                mock.ANY,
                _expected_formatted_bgpvpn(bgpvpn['bgpvpn']['id'],
                                           net['network']['id']))

    def test_bagpipe_delete_bgpvpn(self):
        mocked_delete = self.mocked_rpc.delete_bgpvpn
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn(do_delete=False) as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                mocked_delete.reset_mock()
                with self.assoc_net(id, net_id, do_disassociate=False):
                    self._delete('bgpvpn/bgpvpns', id)
                    mocked_delete.assert_called_once_with(
                        mock.ANY,
                        _expected_formatted_bgpvpn(id, net_id, rt))

    def test_bagpipe_delete_bgpvpn_with_router_assoc(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn(do_delete=False) as bgpvpn, \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id'],
                                  do_disassociate=False), \
                self.port(subnet=subnet):
            self._router_interface_action('add',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            self.mock_delete_rpc.reset_mock()
            self._delete('bgpvpn/bgpvpns', bgpvpn['bgpvpn']['id'])
            self.mocked_rpc.delete_bgpvpn.assert_called_once_with(
                mock.ANY,
                _expected_formatted_bgpvpn(bgpvpn['bgpvpn']['id'],
                                           net['network']['id']))

    def test_bagpipe_callback_to_rpc_update_port_after_router_itf_added(self):
        driver = self.bgpvpn_plugin.driver
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn:
            itf = self._router_interface_action('add',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                None)
            with self.assoc_router(bgpvpn['bgpvpn']['id'],
                                   router['router']['id']), \
                    self.port(subnet=subnet) as port:
                mac_address = port['port']['mac_address']
                formatted_ip = (port['port']['fixed_ips'][0]['ip_address'] +
                                '/' + subnet['subnet']['cidr'].split('/')[-1])
                itf_port = self.plugin.get_port(self.ctxt, itf['port_id'])

                expected = {
                    'gateway_ip': subnet['subnet']['gateway_ip'],
                    'mac_address': mac_address,
                    'ip_address': formatted_ip,
                    'gateway_mac': itf_port['mac_address']
                }
                expected.update(driver._format_bgpvpn_network_route_targets(
                    [bgpvpn['bgpvpn']]))

                actual = driver._retrieve_bgpvpn_network_info_for_port(
                    self.ctxt, port['port'])

                self.assertEqual(expected, actual)

    def test_bagpipe_get_network_info_for_port(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.port(subnet=subnet) as port:
            itf = self._router_interface_action('add',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                None)
            itf_port = self.plugin.get_port(self.ctxt, itf['port_id'])

            r = bagpipe.get_network_info_for_port(self.ctxt,
                                                  port['port']['id'],
                                                  net['network']['id'])

            expected_ip = port['port']['fixed_ips'][0]['ip_address'] + "/24"
            self.assertEqual({
                'mac_address': port['port']['mac_address'],
                'ip_address': expected_ip,
                'gateway_ip': subnet['subnet']['gateway_ip'],
                'gateway_mac': itf_port['mac_address']
            }, r)

RT = '12345:1'

BGPVPN_INFO = {'mac_address': 'de:ad:00:00:be:ef',
               'ip_address': '10.0.0.2',
               'gateway_ip': '10.0.0.1',
               'l3vpn': {'import_rt': [RT],
                         'export_rt': [RT]
                         },
               'gateway_mac': None
               }


class TestCorePluginML2WithAgents(ml2_plugin.Ml2Plugin,
                                  agents_db.AgentDbMixin):
    pass


class TestBagpipeServiceDriverCallbacks(TestBagpipeCommon,
                                        TestBagpipeOVOPushPullMixin):

    '''Check that receiving callbacks results in RPC calls to the agent'''

    def setUp(self):
        cfg.CONF.set_override('mechanism_drivers',
                              ['logger', 'fake_agent'],
                              'ml2')

        super(TestBagpipeServiceDriverCallbacks, self).setUp(
            "%s.%s" % (__name__, TestCorePluginML2WithAgents.__name__))

        self.port_create_status = 'DOWN'
        self.plugin = directory.get_plugin()
        self.plugin.start_rpc_listeners()

        self.bagpipe_driver = self.bgpvpn_plugin.driver

        self.patched_driver = mock.patch.object(
            self.bgpvpn_plugin.driver,
            '_retrieve_bgpvpn_network_info_for_port',
            return_value=BGPVPN_INFO)
        self.patched_driver.start()

        # we choose an agent of type const.AGENT_TYPE_OFA
        # because this is the type used by the fake_agent mech driver
        helpers.register_ovs_agent(helpers.HOST, const.AGENT_TYPE_OFA)
        helpers.register_l3_agent()

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
                                       status, helpers.HOST)

    def test_bagpipe_callback_to_rpc_update_down2active(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:

            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                helpers.HOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active2down(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:

            self._update_port_status(port, const.PORT_STATUS_ACTIVE)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_DOWN)

            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                helpers.HOST)
            self.assertFalse(self.mock_attach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active2active(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:

            self._update_port_status(port, const.PORT_STATUS_ACTIVE)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down2down(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:

            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_DOWN)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted(self):
        with self.port(arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()

            self.plugin.delete_port(self.ctxt, port['port']['id'])

            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                helpers.HOST)
            self.assertFalse(self.mock_attach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_active_ignore_net_ports(self):
        with self.port(device_owner=const.DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_dont_ignore_probe_ports_compute(self):
        with self.port(device_owner=debug_agent.DEVICE_OWNER_COMPUTE_PROBE,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                helpers.HOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_dont_ignore_probe_ports_network(self):
        with self.port(device_owner=debug_agent.DEVICE_OWNER_NETWORK_PROBE,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                helpers.HOST)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down_ignore_net_ports(self):
        with self.port(device_owner=const.DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted_ignore_net_ports(self):
        with self.port(device_owner=const.DEVICE_OWNER_NETWORK_PREFIX,
                       arg_list=(portbindings.HOST_ID,),
                       **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()

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
                          **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down_ignore_external_net(self):
        with self.subnet(network=self.external_net) as subnet, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()
            self._update_port_status(port, const.PORT_STATUS_DOWN)

            self.assertFalse(self.mock_attach_rpc.called)
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted_ignore_external_net(self):
        with self.subnet(network=self.external_net) as subnet, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: helpers.HOST}) as port:
            self._update_port_status(port, const.PORT_STATUS_DOWN)
            self.mock_attach_rpc.reset_mock()
            self.mock_detach_rpc.reset_mock()

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
            self.port(subnet=subnet,
                      arg_list=(portbindings.HOST_ID,),
                      **{portbindings.HOST_ID: helpers.HOST}) as port, \
            mock.patch.object(self.plugin, 'get_port',
                              return_value=port['port']), \
            mock.patch.object(self.plugin, 'get_network',
                              return_value=net['network']):

            self.plugin.delete_port(self.ctxt, port['port']['id'])

            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                helpers.HOST)

    def test_bagpipe_callback_to_rpc_update_port_router_itf_added(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.port(subnet=subnet) as port, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(self.bagpipe_driver, 'get_bgpvpn',
                                  return_value=bgpvpn['bgpvpn']),\
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            self.bagpipe_driver.registry_router_interface_created(
                None, None, None,
                context=self.ctxt,
                port={'network_id': net['network']['id']},
                router_id=router['router']['id'],
            )
            self.mock_update_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(self.ctxt,
                                                   bgpvpn['bgpvpn'],
                                                   port['port']['network_id']))

    def test_bagpipe_callback_to_rpc_update_port_router_itf_removed(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.port(subnet=subnet) as port, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                mock.patch.object(self.bagpipe_driver, 'get_bgpvpn',
                                  return_value=bgpvpn['bgpvpn']),\
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            self.bagpipe_driver.registry_router_interface_deleted(
                None, None, None,
                context=self.ctxt,
                network_id=port['port']['network_id'],
                port={'device_id': router['router']['id'],
                      'network_id': net['network']['id']}
            )
            self.mock_delete_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(self.ctxt,
                                                   bgpvpn['bgpvpn'],
                                                   port['port']['network_id']))

    def test_l3agent_add_remove_router_interface_to_bgpvpn_rpc(self):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: helpers.HOST}), \
                mock.patch.object(bagpipe,
                                  'get_router_bgpvpn_assocs',
                                  return_value=[{
                                      'bgpvpn_id': bgpvpn['bgpvpn']['id']
                                  }]).start():
            self._router_interface_action('add',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            self.mock_update_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(self.ctxt,
                                                   bgpvpn['bgpvpn'],
                                                   net['network']['id']))
            self._router_interface_action('remove',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)
            self.mock_delete_rpc.assert_called_once_with(
                mock.ANY,
                self.bagpipe_driver._format_bgpvpn(self.ctxt,
                                                   bgpvpn['bgpvpn'],
                                                   net['network']['id']))

    def test_gateway_mac_info_rpc(self):
        BGPVPN_INFO_GW_MAC = copy.copy(BGPVPN_INFO)
        BGPVPN_INFO_GW_MAC.update(gateway_mac='aa:bb:cc:dd:ee:ff')
        self.patched_driver.stop()
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn(route_targets=[RT]) as bgpvpn, \
                self.port(subnet=subnet,
                          arg_list=(portbindings.HOST_ID,),
                          **{portbindings.HOST_ID: helpers.HOST}) as port, \
                self.assoc_net(bgpvpn['bgpvpn']['id'],
                               net['network']['id']), \
                mock.patch.object(self.bgpvpn_plugin.driver,
                                  'retrieve_bgpvpns_of_router_assocs'
                                  '_by_network',
                                  return_value=[{'type': 'l3',
                                                 'route_targets': [RT]}]
                                  ):
            self._update_port_status(port, const.PORT_STATUS_ACTIVE)

            itf = self._router_interface_action('add',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                None)
            itf_port = self.plugin.get_port(self.ctxt, itf['port_id'])

            self.mock_update_rpc.assert_called_with(
                mock.ANY,
                _expected_formatted_bgpvpn(bgpvpn['bgpvpn']['id'],
                                           net['network']['id'],
                                           [RT],
                                           gateway_mac=itf_port['mac_address'])
            )

            self._router_interface_action('remove',
                                          router['router']['id'],
                                          subnet['subnet']['id'],
                                          None)

            self.mock_update_rpc.assert_called_with(
                mock.ANY,
                _expected_formatted_bgpvpn(bgpvpn['bgpvpn']['id'],
                                           net['network']['id'],
                                           [RT],
                                           gateway_mac=None)
            )

        self.patched_driver.start()

    def test_l2agent_rpc_to_bgpvpn_rpc(self):
        #
        # Test that really simulate the ML2 codepath that
        # generate the registry events.

        ml2_rpc_callbacks = ml2_rpc.RpcCallbacks(mock.Mock(), mock.Mock())

        n_dict = {"name": "netfoo",
                  "tenant_id": self._tenant_id,
                  "admin_state_up": True,
                  "shared": False}

        net = self.plugin.create_network(self.ctxt, {'network': n_dict})

        subnet_dict = {'name': 'test_subnet',
                       'tenant_id': self._tenant_id,
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
                  'tenant_id': self._tenant_id,
                  'name': 'fooport',
                  "admin_state_up": True,
                  "device_id": "tapfoo",
                  "device_owner": "not_me",
                  "mac_address": "de:ad:00:00:be:ef",
                  "fixed_ips": [],
                  "binding:host_id": helpers.HOST,
                  }

        port = self.plugin.create_port(self.ctxt, {'port': p_dict})

        ml2_rpc_callbacks.update_device_up(self.ctxt,
                                           host=helpers.HOST,
                                           agent_id='fooagent',
                                           device="de:ad:00:00:be:ef")
        self.mock_attach_rpc.assert_called_once_with(
            mock.ANY,
            self._build_expected_return_active(port),
            helpers.HOST)

        ml2_rpc_callbacks.update_device_down(self.ctxt,
                                             host=helpers.HOST,
                                             agent_id='fooagent',
                                             device="de:ad:00:00:be:ef")

        self.mock_detach_rpc.assert_called_once_with(
            mock.ANY,
            self._build_expected_return_down(port),
            helpers.HOST)
        self.mock_detach_rpc.reset_mock()

        self.plugin.delete_port(self.ctxt, port['id'])

        self.mock_detach_rpc.assert_called_once_with(
            mock.ANY,
            self._build_expected_return_down(port),
            helpers.HOST)

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

    def test_format_bgpvpn_network_route_targets(self):
        driver = self.bgpvpn_plugin.driver
        bgpvpns = [{
            'type': 'l3',
            'route_targets': ['12345:1', '12345:2', '12345:3'],
            'import_targets': ['12345:2', '12345:3'],
            'export_targets': ['12345:3', '12345:4']
        },
            {
                'type': 'l3',
                'route_targets': ['12345:3', '12346:1']
            },
            {
                'type': 'l2',
                'route_targets': ['12347:1']
            }]
        result = driver._format_bgpvpn_network_route_targets(bgpvpns)
        expected = {
            'l3vpn': {
                'import_rt': ['12345:1', '12345:2', '12345:3', '12346:1'],
                'export_rt': ['12345:1', '12345:2', '12345:3', '12345:4',
                              '12346:1']
            },
            'l2vpn': {
                'import_rt': ['12347:1'],
                'export_rt': ['12347:1']
            }
        }

        self.assertItemsEqual(result['l3vpn']['import_rt'],
                              expected['l3vpn']['import_rt'])
        self.assertItemsEqual(result['l3vpn']['export_rt'],
                              expected['l3vpn']['export_rt'])
        self.assertItemsEqual(result['l2vpn']['import_rt'],
                              expected['l2vpn']['import_rt'])
        self.assertItemsEqual(result['l2vpn']['export_rt'],
                              expected['l2vpn']['export_rt'])


class TestBagpipeServiceDriverV2RPCs(TestBagpipeCommon,
                                     TestBagpipeOVOPushPullMixin):
    '''Check RPC push/pull and local registry callback effects'''

    def setUp(self):
        cfg.CONF.set_override('mechanism_drivers',
                              ['logger', 'fake_agent'],
                              'ml2')

        super(TestBagpipeServiceDriverV2RPCs, self).setUp(
            "%s.%s" % (__name__, TestCorePluginML2WithAgents.__name__),
            driver=('networking_bgpvpn.neutron.services.service_drivers.'
                    'bagpipe.bagpipe_v2.BaGPipeBGPVPNDriver'))

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_router_itf_event_router_assoc(self, mocked_push):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                self.assoc_router(bgpvpn['bgpvpn']['id'],
                                  router['router']['id']):

            mocked_push.reset_mock()

            itf = self._router_interface_action('add',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                None)

            mocked_push.assert_any_call(
                mock.ANY,
                [AnyOfClass(objs.BGPVPNRouterAssociation)], 'updated')

            mocked_push.reset_mock()

            itf = self._router_interface_action('remove',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                itf['port_id'])
            mocked_push.assert_any_call(
                mock.ANY,
                [AnyOfClass(objs.BGPVPNRouterAssociation)], 'updated')

    @mock.patch.object(resources_rpc.ResourcesPushRpcApi, 'push')
    def test_router_itf_event_network_assoc(self, mocked_push):
        with self.network() as net, \
                self.subnet(network=net) as subnet, \
                self.router(tenant_id=self._tenant_id) as router, \
                self.bgpvpn() as bgpvpn, \
                self.assoc_net(bgpvpn['bgpvpn']['id'],
                               net['network']['id']):

            mocked_push.reset_mock()

            itf = self._router_interface_action('add',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                None)

            mocked_push.assert_any_call(
                mock.ANY,
                [AnyOfClass(objs.BGPVPNNetAssociation)], 'updated')

            mocked_push.reset_mock()

            itf = self._router_interface_action('remove',
                                                router['router']['id'],
                                                subnet['subnet']['id'],
                                                itf['port_id'])

            mocked_push.assert_any_call(
                mock.ANY,
                [AnyOfClass(objs.BGPVPNNetAssociation)], 'updated')

            ovos_in_call = mocked_push.mock_calls[0][1][1]
            for ovo in ovos_in_call:
                if not isinstance(ovo, objs.BGPVPNNetAssociation):
                    continue
                for subnet in ovo.all_subnets(net['network']['id']):
                    self.assertIsNone(subnet['gateway_mac'])
