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

import mock
import webob.exc

from neutron.common.constants import DEVICE_OWNER_DHCP
from neutron.common.constants import PORT_STATUS_ACTIVE
from neutron.common.constants import PORT_STATUS_DOWN

from networking_bgpvpn.tests.unit.services import test_plugin


class TestBagpipeCommon(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self):
        self.mocked_bagpipeAPI = mock.patch(
            'networking_bagpipe.agent.bgpvpn.rpc_client'
            '.BGPVPNAgentNotifyApi').start().return_value

        provider = ('networking_bgpvpn.neutron.services.service_drivers.'
                    'bagpipe.bagpipe.BaGPipeBGPVPNDriver')
        super(TestBagpipeCommon, self).setUp(service_provider=provider)


class TestBagpipeServiceDriver(TestBagpipeCommon):

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


class TestBagpipeServiceDriverCallbacks(TestBagpipeCommon):
    '''Check that receiving callbacks results in RPC calls to the agent'''

    def setUp(self):
        super(TestBagpipeServiceDriverCallbacks, self).setUp()

        self.bagpipe_driver = self.bgpvpn_plugin.driver

        self.bgpvpn_info = {'mac_address': '00:00:de:ad:be:ef',
                            'ip_address': '10.0.0.2',
                            'gateway_ip': '10.0.0.1',
                            'l3vpn': {'import_rt': ['12345:1'],
                                      'export_rt': ['12345:1']
                                      }
                            }

        self.bagpipe_driver._retrieve_bgpvpn_network_info_for_port = mock.Mock(
            return_value=self.bgpvpn_info
        )

        self.testhost = 'TESTHOST'
        self.bagpipe_driver._get_port_host = mock.Mock(
            return_value=self.testhost
        )

        self.mock_attach_rpc = self.mocked_bagpipeAPI.attach_port_on_bgpvpn
        self.mock_detach_rpc = self.mocked_bagpipeAPI.detach_port_from_bgpvpn

    def _build_expected_return_active(self, port):
        bgpvpn_info_port = self.bgpvpn_info.copy()
        bgpvpn_info_port.update({'id': port['id'],
                                 'network_id': port['network_id']})
        return bgpvpn_info_port

    def _build_expected_return_down(self, port):
        return {'id': port['id'],
                'network_id': port['network_id']}

    def test_bagpipe_callback_to_rpc_update_active(self):
        with self.port() as port:
            port['port']['status'] = PORT_STATUS_ACTIVE
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.mock_attach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_active(port['port']),
                self.testhost)

    def test_bagpipe_callback_to_rpc_update_down(self):
        with self.port() as port:
            port['port']['status'] = PORT_STATUS_DOWN
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                self.testhost)

    def test_bagpipe_callback_to_rpc_deleted(self):
        with self.port() as port:
            port['port']['status'] = PORT_STATUS_DOWN
            self.bagpipe_driver.registry_port_deleted(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.mock_detach_rpc.assert_called_once_with(
                mock.ANY,
                self._build_expected_return_down(port['port']),
                self.testhost)

    def test_bagpipe_callback_to_rpc_update_active_ignore_DHCP(self):
        with self.port(device_owner=DEVICE_OWNER_DHCP) as port:
            port['port']['status'] = PORT_STATUS_ACTIVE
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.assertFalse(self.mock_attach_rpc.called)

    def test_bagpipe_callback_to_rpc_update_down_ignore_DHCP(self):
        with self.port(device_owner=DEVICE_OWNER_DHCP) as port:
            port['port']['status'] = PORT_STATUS_DOWN
            self.bagpipe_driver.registry_port_updated(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.assertFalse(self.mock_detach_rpc.called)

    def test_bagpipe_callback_to_rpc_deleted_ignore_DHCP(self):
        with self.port(device_owner=DEVICE_OWNER_DHCP) as port:
            port['port']['status'] = PORT_STATUS_DOWN
            self.bagpipe_driver.registry_port_deleted(
                None, None, None,
                context=None,
                port=port['port']
            )
            self.assertFalse(self.mock_detach_rpc.called)
