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

from openstack.network.v2._proxy import Proxy as networkclient
from openstack.network.v2 import bgpvpn as sdk_bgpvpn
from openstack.network.v2 import bgpvpn_network_association
from openstack.network.v2 import bgpvpn_router_association
from openstack_dashboard.test import helpers as test

from bgpvpn_dashboard import api
from bgpvpn_dashboard.test import helpers as bgpvpn_test


class BgpvpnApiTests(bgpvpn_test.APITestCase):

    def setUp(self):
        bgpvpn_test.APITestCase.setUp(self)

    @test.create_mocks({networkclient: ('bgpvpns',)})
    def test_bgpvpn_list(self):
        exp_bgpvpns = self.bgpvpns.list()

        api_bgpvpns = self.api_bgpvpns
        self.mock_bgpvpns.return_value = api_bgpvpns

        ret_vals = api.bgpvpn.bgpvpns_list(self.request)
        for (ret_val, exp_bgpvpn) in zip(ret_vals, exp_bgpvpns):
            self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
            self.assertEqual(exp_bgpvpn.id, ret_val.id)
            self.assertEqual(exp_bgpvpn.name, ret_val.name)

    @test.create_mocks({networkclient: ('create_bgpvpn',)})
    def test_bgpvpn_create(self):
        bgpvpn = self.bgpvpns.first()
        data = {'name': bgpvpn.name,
                'route_targets': bgpvpn.route_targets,
                'tenant_id': bgpvpn.tenant_id}

        self.mock_create_bgpvpn.return_value = self.api_bgpvpns[0]

        ret_val = api.bgpvpn.bgpvpn_create(self.request, **data)

        self.mock_create_bgpvpn.assert_called_once_with(**data)

        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual(bgpvpn.name, ret_val.name)

    @test.create_mocks({networkclient: ('get_bgpvpn',)})
    def test_bgpvpn_get(self):
        bgpvpn = self.bgpvpns.first()
        ret_dict = self.api_bgpvpns[0]

        self.mock_get_bgpvpn.return_value = ret_dict

        ret_val = api.bgpvpn.bgpvpn_get(self.request, bgpvpn.id)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual(bgpvpn.name, ret_val.name)

    @test.create_mocks({networkclient: ('update_bgpvpn',)})
    def test_bgpvpn_update(self):
        bgpvpn = self.bgpvpns.first()
        bgpvpn_dict = self.api_bgpvpns[0].to_dict()

        bgpvpn.name = 'new name'
        bgpvpn.route_targets = ['65001:2']

        bgpvpn_dict['name'] = 'new name'
        bgpvpn_dict['route_targets'] = ['65001:2']

        data = {'name': bgpvpn.name,
                'route_targets': bgpvpn.route_targets}

        self.mock_update_bgpvpn.return_value = sdk_bgpvpn.BgpVpn(
            **bgpvpn_dict)

        ret_val = api.bgpvpn.bgpvpn_update(self.request, bgpvpn.id, **data)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)
        self.assertEqual('new name', ret_val.name)
        self.assertEqual(['65001:2'], ret_val.route_targets)

    @test.create_mocks({networkclient: ('delete_bgpvpn',)})
    def test_bgpvpn_delete(self):
        bgpvpn = self.bgpvpns.first()
        api.bgpvpn.bgpvpn_delete(self.request, bgpvpn.id)

        self.mock_delete_bgpvpn.assert_called_once_with(bgpvpn.id)

    @test.create_mocks({
        networkclient: ('get_bgpvpn_network_association',)})
    def test_network_association_get(self):
        bgpvpn = self.bgpvpns.first()
        na = self.network_associations.first()
        ret_dict = self.api_network_associations[0]

        self.mock_get_bgpvpn_network_association.return_value = ret_dict

        ret_val = api.bgpvpn.network_association_get(
            self.request, bgpvpn.id, na.id)
        self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)

    @test.create_mocks({networkclient: ('bgpvpn_network_associations',)})
    def test_network_association_list(self):
        exp_nas = self.network_associations.list()

        api_na = self.api_network_associations
        self.mock_bgpvpn_network_associations.return_value = api_na

        ret_vals = api.bgpvpn.network_association_list(self.request, 'dummy')
        for (ret_val, exp_na) in zip(ret_vals, exp_nas):
            self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)
            self.assertEqual(exp_na.id, ret_val.id)
            self.assertEqual(exp_na.network_id, ret_val.network_id)

    @test.create_mocks({
        networkclient: ('create_bgpvpn_network_association',)})
    def test_network_association_create(self):
        bgpvpn = self.bgpvpns.first()
        network = self.networks.first()
        data = {'network_id': network.id}

        self.mock_create_bgpvpn_network_association.return_value = (
            bgpvpn_network_association.BgpVpnNetworkAssociation(**data))

        ret_val = api.bgpvpn.network_association_create(
            self.request, bgpvpn.id, **data)

        self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)
        self.assertEqual(network.id, ret_val.network_id)

    @test.create_mocks({
        networkclient: ('delete_bgpvpn_network_association',)})
    def test_network_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.network_associations.first()

        api.bgpvpn.network_association_delete(self.request, na.id, bgpvpn.id)

        self.mock_delete_bgpvpn_network_association.assert_called_once_with(
            bgpvpn.id, na.id)

    @test.create_mocks({
        networkclient: ('get_bgpvpn_router_association',)})
    def test_router_association_get(self):
        bgpvpn = self.bgpvpns.first()
        na = self.router_associations.first()

        self.mock_get_bgpvpn_router_association.return_value = (
            self.api_router_associations[0])

        ret_val = api.bgpvpn.router_association_get(
            self.request, bgpvpn.id, na.id)
        self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)

    @test.create_mocks({
        networkclient: ('bgpvpn_router_associations',)})
    def test_router_association_list(self):
        exp_nas = self.router_associations.list()

        self.mock_bgpvpn_router_associations.return_value = (
            self.api_router_associations)

        ret_vals = api.bgpvpn.router_association_list(self.request, 'dummy')
        for (ret_val, exp_na) in zip(ret_vals, exp_nas):
            self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)
            self.assertEqual(exp_na.id, ret_val.id)
            self.assertEqual(exp_na.router_id, ret_val.router_id)

    @test.create_mocks({
        networkclient: ('create_bgpvpn_router_association',)})
    def test_router_association_create(self):
        bgpvpn = self.bgpvpns.first()
        router = self.routers.first()
        data = {'router_id': router.id}

        self.mock_create_bgpvpn_router_association.return_value = (
            bgpvpn_router_association.BgpVpnRouterAssociation(**data)
        )

        ret_val = api.bgpvpn.router_association_create(
            self.request, bgpvpn.id, **data)

        self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)
        self.assertEqual(router.id, ret_val.router_id)

    @test.create_mocks({
        networkclient: ('delete_bgpvpn_router_association',)})
    def test_router_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.router_associations.first()

        api.bgpvpn.router_association_delete(self.request, na.id, bgpvpn.id)

        self.mock_delete_bgpvpn_router_association.assert_called_once_with(
            bgpvpn.id, na.id)
