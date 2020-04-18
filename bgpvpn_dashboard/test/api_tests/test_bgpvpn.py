# Copyright (c) 2016 Orange.
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

from unittest import mock

from openstack_dashboard.test import helpers as test

from bgpvpn_dashboard import api
from bgpvpn_dashboard.test import helpers as bgpvpn_test

from neutronclient.v2_0.client import Client as neutronclient


class BgpvpnApiTests(bgpvpn_test.APITestCase):

    def setUp(self):
        bgpvpn_test.APITestCase.setUp(self)

        # Since the early days of networking-bgpvpn, the package was providing
        # a neutronclient.extensions entry point so that neutronclient would
        # dynamically add BGPVPN API methods to a Client instance.  This is
        # only kept for backward compatibility, but not required anymore for
        # users of >=Ocata python-neutronclient. However, the dynamic addition
        # of these methods makes is a pain to mock. The patch below disables
        # the addition of the dynamic BGPVPN methods.
        mock.patch('neutronclient.v2_0.client.Client._register_extensions'
                   ).start()

    @test.create_mocks({neutronclient: ('list_bgpvpns',)})
    def test_bgpvpn_list(self):
        exp_bgpvpns = self.bgpvpns.list()

        api_bgpvpns = {'bgpvpns': self.api_bgpvpns.list()}
        self.mock_list_bgpvpns.return_value = api_bgpvpns

        ret_vals = api.bgpvpn.bgpvpns_list(self.request)
        for (ret_val, exp_bgpvpn) in zip(ret_vals, exp_bgpvpns):
            self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
            self.assertEqual(exp_bgpvpn.id, ret_val.id)
            self.assertEqual(exp_bgpvpn.name, ret_val.name)

    @test.create_mocks({neutronclient: ('create_bgpvpn',)})
    def test_bgpvpn_create(self):
        bgpvpn = self.bgpvpns.first()
        data = {'name': bgpvpn.name,
                'route_targets': bgpvpn.route_targets,
                'tenant_id': bgpvpn.tenant_id}

        ret_dict = {'bgpvpn': data}
        self.mock_create_bgpvpn.return_value = ret_dict

        ret_val = api.bgpvpn.bgpvpn_create(self.request, **data)

        self.mock_create_bgpvpn.assert_called_once_with(body=ret_dict)

        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual(bgpvpn.name, ret_val.name)

    @test.create_mocks({neutronclient: ('show_bgpvpn',)})
    def test_bgpvpn_get(self):
        bgpvpn = self.bgpvpns.first()
        ret_dict = {'bgpvpn': self.api_bgpvpns.first()}

        self.mock_show_bgpvpn.return_value = ret_dict

        ret_val = api.bgpvpn.bgpvpn_get(self.request, bgpvpn.id)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual(bgpvpn.name, ret_val.name)

    @test.create_mocks({neutronclient: ('update_bgpvpn',)})
    def test_bgpvpn_update(self):
        bgpvpn = self.bgpvpns.first()
        bgpvpn_dict = self.api_bgpvpns.first()

        bgpvpn.name = 'new name'
        bgpvpn.route_targets = ['65001:2']

        bgpvpn_dict['name'] = 'new name'
        bgpvpn_dict['route_targets'] = ['65001:2']

        data = {'name': bgpvpn.name,
                'route_targets': bgpvpn.route_targets}
        ret_dict = {'bgpvpn': bgpvpn_dict}

        self.mock_update_bgpvpn.return_value = ret_dict

        ret_val = api.bgpvpn.bgpvpn_update(self.request, bgpvpn.id, **data)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual('new name', ret_val.name)
        self.assertEqual(['65001:2'], ret_val.route_targets)

    @test.create_mocks({neutronclient: ('delete_bgpvpn',)})
    def test_bgpvpn_delete(self):
        bgpvpn = self.bgpvpns.first()
        api.bgpvpn.bgpvpn_delete(self.request, bgpvpn.id)

        self.mock_delete_bgpvpn.assert_called_once_with(bgpvpn.id)

    @test.create_mocks({
        neutronclient: ('show_bgpvpn_network_assoc',)})
    def test_network_association_get(self):
        bgpvpn = self.bgpvpns.first()
        na = self.network_associations.first()
        ret_dict = {
            'network_association': self.api_network_associations.first()}

        self.mock_show_bgpvpn_network_assoc.return_value = ret_dict

        ret_val = api.bgpvpn.network_association_get(
            self.request, bgpvpn.id, na.id)
        self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)

    @test.create_mocks({
        neutronclient: ('list_bgpvpn_network_assocs',)})
    def test_network_association_list(self):
        exp_nas = self.network_associations.list()

        api_na = {'network_associations': self.api_network_associations.list()}
        self.mock_list_bgpvpn_network_assocs.return_value = api_na

        ret_vals = api.bgpvpn.network_association_list(self.request, 'dummy')
        for (ret_val, exp_na) in zip(ret_vals, exp_nas):
            self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)
            self.assertEqual(exp_na.id, ret_val.id)
            self.assertEqual(exp_na.network_id, ret_val.network_id)

    @test.create_mocks({
        neutronclient: ('create_bgpvpn_network_assoc',)})
    def test_network_association_create(self):
        bgpvpn = self.bgpvpns.first()
        network = self.networks.first()
        data = {'network_id': network.id}
        ret_dict = {'network_association': data}

        self.mock_create_bgpvpn_network_assoc.return_value = ret_dict

        ret_val = api.bgpvpn.network_association_create(
            self.request, bgpvpn.id, **data)

        self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)
        self.assertEqual(network.id, ret_val.network_id)

    @test.create_mocks({
        neutronclient: ('delete_bgpvpn_network_assoc',)})
    def test_network_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.network_associations.first()

        api.bgpvpn.network_association_delete(self.request, na.id, bgpvpn.id)

        self.mock_delete_bgpvpn_network_assoc.assert_called_once_with(
            bgpvpn.id, na.id)

    @test.create_mocks({
        neutronclient: ('show_bgpvpn_router_assoc',)})
    def test_router_association_get(self):
        bgpvpn = self.bgpvpns.first()
        na = self.router_associations.first()
        ret_dict = {
            'router_association': self.api_router_associations.first()}

        self.mock_show_bgpvpn_router_assoc.return_value = ret_dict

        ret_val = api.bgpvpn.router_association_get(
            self.request, bgpvpn.id, na.id)
        self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)

    @test.create_mocks({
        neutronclient: ('list_bgpvpn_router_assocs',)})
    def test_router_association_list(self):
        exp_nas = self.router_associations.list()

        api_na = {'router_associations': self.api_router_associations.list()}
        self.mock_list_bgpvpn_router_assocs.return_value = api_na

        ret_vals = api.bgpvpn.router_association_list(self.request, 'dummy')
        for (ret_val, exp_na) in zip(ret_vals, exp_nas):
            self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)
            self.assertEqual(exp_na.id, ret_val.id)
            self.assertEqual(exp_na.router_id, ret_val.router_id)

    @test.create_mocks({
        neutronclient: ('create_bgpvpn_router_assoc',)})
    def test_router_association_create(self):
        bgpvpn = self.bgpvpns.first()
        router = self.routers.first()
        data = {'router_id': router.id}
        ret_dict = {'router_association': data}

        self.mock_create_bgpvpn_router_assoc.return_value = ret_dict

        ret_val = api.bgpvpn.router_association_create(
            self.request, bgpvpn.id, **data)

        self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)
        self.assertEqual(router.id, ret_val.router_id)

    @test.create_mocks({
        neutronclient: ('delete_bgpvpn_router_assoc',)})
    def test_router_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.router_associations.first()

        api.bgpvpn.router_association_delete(self.request, na.id, bgpvpn.id)

        self.mock_delete_bgpvpn_router_assoc.assert_called_once_with(
            bgpvpn.id, na.id)
