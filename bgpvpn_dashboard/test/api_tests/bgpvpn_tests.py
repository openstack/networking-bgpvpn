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

from openstack_dashboard.test import helpers as test

from bgpvpn_dashboard import api
from bgpvpn_dashboard.test import helpers as bgpvpn_test

from neutronclient.v2_0.client import Client as neutronclient


class BgpvpnApiTests(bgpvpn_test.APITestCase):
    @test.create_stubs({neutronclient: ('list_ext',)})
    def test_bgpvpn_list(self):
        bgpvpns = {'bgpvpns': self.api_bgpvpns.list()}
        neutronclient.list_ext('bgpvpns',
                               '/bgpvpn/bgpvpns', True).AndReturn(bgpvpns)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.bgpvpns_list(self.request)
        for n in ret_val:
            self.assertIsInstance(n, api.bgpvpn.Bgpvpn)

    @test.create_stubs({neutronclient: ('create_ext',)})
    def test_bgpvpn_create(self):
        bgpvpn = self.bgpvpns.first()
        data = {'name': bgpvpn.name,
                'route_targets': bgpvpn.route_targets,
                'tenant_id': bgpvpn.tenant_id}
        ret_dict = {'bgpvpn': data}
        neutronclient.create_ext('/bgpvpn/bgpvpns',
                                 ret_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.bgpvpn_create(self.request, **data)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)

    @test.create_stubs({neutronclient: ('show_ext',)})
    def test_bgpvpn_get(self):
        bgpvpn = self.bgpvpns.first()
        ret_dict = {'bgpvpn': self.api_bgpvpns.first()}
        neutronclient.show_ext('/bgpvpn/bgpvpns/%s',
                               bgpvpn.id).AndReturn(ret_dict)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.bgpvpn_get(self.request, bgpvpn.id)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)

    @test.create_stubs({neutronclient: ('update_ext',)})
    def test_bgpvpn_update(self):
        bgpvpn = self.bgpvpns.first()
        bgpvpn_dict = self.api_bgpvpns.first()

        bgpvpn.name = 'new name'
        bgpvpn.route_targets = '65001:2'

        bgpvpn_dict['name'] = 'new name'
        bgpvpn_dict['route_targets'] = '65001:2'

        form_data = {'name': bgpvpn.name,
                     'route_targets': bgpvpn.route_targets}
        form_dict = {'bgpvpn': form_data}
        ret_dict = {'bgpvpn': bgpvpn_dict}

        neutronclient.update_ext('/bgpvpn/bgpvpns/%s',
                                 bgpvpn.id, form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.bgpvpn_update(self.request,
                                           bgpvpn.id,
                                           **form_data)
        self.assertIsInstance(ret_val, api.bgpvpn.Bgpvpn)

    @test.create_stubs({neutronclient: ('delete_ext',)})
    def test_bgpvpn_delete(self):
        bgpvpn = self.bgpvpns.first()
        api_bgpvpn = {'bgpvpn': self.api_bgpvpns.first()}
        neutronclient.delete_ext('/bgpvpn/bgpvpns/%s',
                                 bgpvpn.id).AndReturn(api_bgpvpn)
        self.mox.ReplayAll()
        api.bgpvpn.bgpvpn_delete(self.request, bgpvpn.id)

    @test.create_stubs({neutronclient: ('list_ext',)})
    def test_network_association_list(self):
        bgpvpn = self.bgpvpns.first()
        na = {'network_associations': self.api_network_associations.list()}
        neutronclient.list_ext(
            'network_associations',
            '/bgpvpn/bgpvpns/%s/network_associations' % bgpvpn.id,
            True).AndReturn(na)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.network_association_list(self.request, bgpvpn.id)
        for n in ret_val:
            self.assertIsInstance(n, api.bgpvpn.NetworkAssociation)

    @test.create_stubs({neutronclient: ('create_ext',)})
    def test_network_association_create(self):
        bgpvpn = self.bgpvpns.first()
        network = self.networks.first()
        data = {'network_id': network.id}
        ret_dict = {'network_association': data}
        neutronclient.create_ext(
            '/bgpvpn/bgpvpns/%s/network_associations' % bgpvpn.id,
            ret_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.network_association_create(self.request,
                                                        bgpvpn.id,
                                                        **data)
        self.assertIsInstance(ret_val, api.bgpvpn.NetworkAssociation)

    @test.create_stubs({neutronclient: ('delete_ext',)})
    def test_network_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.network_associations.first()
        api_bgpvpn = {
            'network_association': self.api_network_associations.first()}
        neutronclient.delete_ext(
            '/bgpvpn/bgpvpns/' + bgpvpn.id + '/network_associations/%s',
            na.id).AndReturn(api_bgpvpn)
        self.mox.ReplayAll()
        api.bgpvpn.network_association_delete(self.request, na.id, bgpvpn.id)

    @test.create_stubs({neutronclient: ('list_ext',)})
    def test_router_association_list(self):
        bgpvpn = self.bgpvpns.first()
        na = {'router_associations': self.api_network_associations.list()}
        neutronclient.list_ext(
            'router_associations',
            '/bgpvpn/bgpvpns/%s/router_associations' % bgpvpn.id,
            True).AndReturn(na)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.router_association_list(self.request, bgpvpn.id)
        for n in ret_val:
            self.assertIsInstance(n, api.bgpvpn.RouterAssociation)

    @test.create_stubs({neutronclient: ('create_ext',)})
    def test_router_association_create(self):
        bgpvpn = self.bgpvpns.first()
        router = self.routers.first()
        data = {'router_id': router.id}
        ret_dict = {'router_association': data}
        neutronclient.create_ext(
            '/bgpvpn/bgpvpns/%s/router_associations' % bgpvpn.id,
            ret_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()
        ret_val = api.bgpvpn.router_association_create(self.request,
                                                       bgpvpn.id,
                                                       **data)
        self.assertIsInstance(ret_val, api.bgpvpn.RouterAssociation)

    @test.create_stubs({neutronclient: ('delete_ext',)})
    def test_router_association_delete(self):
        bgpvpn = self.bgpvpns.first()
        na = self.router_associations.first()
        api_bgpvpn = {
            'router_association': self.api_router_associations.first()
        }
        neutronclient.delete_ext(
            '/bgpvpn/bgpvpns/' + bgpvpn.id + '/router_associations/%s',
            na.id).AndReturn(api_bgpvpn)
        self.mox.ReplayAll()
        api.bgpvpn.router_association_delete(self.request, na.id, bgpvpn.id)
