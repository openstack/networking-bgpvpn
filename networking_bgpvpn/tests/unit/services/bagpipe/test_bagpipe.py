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

from networking_bgpvpn.tests.unit.services import test_plugin


class TestBagpipeServiceDriver(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self):
        self.mocked_bagpipeAPI = mock.patch(
            'networking_bagpipe_l2.agent.bgpvpn.rpc_client'
            '.BGPVPNAgentNotifyApi').start().return_value

        provider = ('networking_bgpvpn.neutron.services.service_drivers.'
                    'bagpipe.bagpipe.BaGPipeBGPVPNDriver')
        super(TestBagpipeServiceDriver, self).setUp(service_provider=provider)

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
                with self.assoc_net(id, net_id, do_disassociate=False):
                    net_body = {'network_id': net_id}
                    mocked_delete.reset_mock()
                    disassoc_req = self._req('PUT', 'bgpvpn/bgpvpns',
                                             data=net_body, fmt=self.fmt,
                                             id=id,
                                             action='disassociate_network')
                    res = disassoc_req.get_response(self.ext_api)
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
