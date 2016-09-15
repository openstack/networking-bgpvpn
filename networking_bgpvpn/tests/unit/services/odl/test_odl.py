#
# Copyright (C) 2015 Ericsson India Global Services Pvt Ltd.
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#

import mock


from networking_bgpvpn.tests.unit.services import test_plugin


class TestBgpvpnOdlCommon(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self):
        self.mocked_odlclient = mock.patch(
            'networking_odl.common.client'
            '.OpenDaylightRestClient.create_client').start().return_value

        provider = ('networking_bgpvpn.neutron.services.service_drivers.'
                    'opendaylight.odl.OpenDaylightBgpvpnDriver')
        super(TestBgpvpnOdlCommon, self).setUp(service_provider=provider)


class TestOdlServiceDriver(TestBgpvpnOdlCommon):

    def test_odl_associate_net(self):
        mocked_sendjson = self.mocked_odlclient.sendjson
        with self.port() as port1:
            net_id = port1['port']['network_id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                mocked_sendjson.reset_mock()
                with self.assoc_net(id, net_id):
                    formatted_bgpvpn = {
                        'bgpvpn':
                        {'export_targets': mock.ANY,
                         'name': mock.ANY,
                         'route_targets': rt,
                         'tenant_id': mock.ANY,
                         'project_id': mock.ANY,
                         'import_targets': mock.ANY,
                         'route_distinguishers': mock.ANY,
                         'type': mock.ANY,
                         'id': id,
                         'networks': [net_id],
                         'routers': []}}
                    mocked_sendjson.assert_called_once_with(mock.ANY,
                                                            mock.ANY,
                                                            formatted_bgpvpn)

    def test_odl_associate_router(self):
        mocked_sendjson = self.mocked_odlclient.sendjson
        with self.router(tenant_id=self._tenant_id) as router:
            router_id = router['router']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                rt = bgpvpn['bgpvpn']['route_targets']
                mocked_sendjson.reset_mock()
                with self.assoc_router(id, router_id):
                    formatted_bgpvpn = {
                        'bgpvpn':
                        {'export_targets': mock.ANY,
                         'name': mock.ANY,
                         'route_targets': rt,
                         'tenant_id': mock.ANY,
                         'project_id': mock.ANY,
                         'import_targets': mock.ANY,
                         'route_distinguishers': mock.ANY,
                         'type': mock.ANY,
                         'id': id,
                         'networks': [],
                         'routers': [router_id]}}
                    mocked_sendjson.assert_called_once_with(mock.ANY,
                                                            mock.ANY,
                                                            formatted_bgpvpn)
