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

from openstack.network.v2 import bgpvpn as sdk_bgpvpn
from openstack.network.v2 import bgpvpn_network_association
from openstack.network.v2 import bgpvpn_router_association

from bgpvpn_dashboard.api import bgpvpn
from openstack_dashboard.test.test_data import utils


def data(TEST):
    TEST.bgpvpns = utils.TestDataContainer()
    TEST.api_bgpvpns = list()
    TEST.network_associations = utils.TestDataContainer()
    TEST.api_network_associations = list()
    TEST.router_associations = utils.TestDataContainer()
    TEST.api_router_associations = list()

    bgpvpn_dict = {'id': 'b595e758-1877-4aec-92a2-6834d76f1025',
                   'tenant_id': '1',
                   'name': 'bgpvpn1',
                   'route_targets': '64500:1'
                   }
    TEST.api_bgpvpns.append(sdk_bgpvpn.BgpVpn(**bgpvpn_dict))
    b = bgpvpn.Bgpvpn(copy.deepcopy(bgpvpn_dict))
    TEST.bgpvpns.add(b)

    network_association_dict = {
        'id': '99ef096d-21fb-43a7-9e2a-b3c464abef3a',
        'network_id': '063cf7f3-ded1-4297-bc4c-31eae876cc91',
        'tenant_id': '1'}
    TEST.api_network_associations.append(
        bgpvpn_network_association.BgpVpnNetworkAssociation(
            **network_association_dict))
    na = bgpvpn.NetworkAssociation(copy.deepcopy(network_association_dict))
    TEST.network_associations.add(na)

    router_association_dict = {
        'id': '9736c228-745d-4e78-83a5-d971d9fd8f2c',
        'router_id': '279989f7-54bb-41d9-ba42-0d61f12fda61',
        'tenant_id': '1'}
    TEST.api_router_associations.append(
        bgpvpn_router_association.BgpVpnRouterAssociation(
            **router_association_dict))
    ra = bgpvpn.RouterAssociation(copy.deepcopy(router_association_dict))
    TEST.router_associations.add(ra)
