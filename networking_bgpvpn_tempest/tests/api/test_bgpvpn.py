# Copyright (c) 2015 Ericsson.
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

from networking_bgpvpn_tempest.tests.base import BaseBgpvpnTest as base
from tempest.lib import exceptions
from tempest import test


class BgpvpnTest(base):
    """Tests the following operations in the Neutron API:

        create bgpvpn
        delete bgpvpn
        associate network to bgpvpn
        disassociate network from bgpvpn

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:

    ...
    """

    def test_create_bgpvpn(self):
        self.create_bgpvpn(self.bgpvpn_admin_client)

    @test.attr(type=['negative'])
    def test_create_bgpvpn_as_non_admin_fail(self):
        self.assertRaises(exceptions.Forbidden,
                          self.create_bgpvpn, self.bgpvpn_client)

    @test.attr(type=['negative'])
    def test_delete_bgpvpn_as_non_admin_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.delete_bgpvpn, bgpvpn['id'])

    def test_associate_disassociate_network(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()
        network_id = network['network']['id']

        # Associate the network to the bgpvpn resource
        association = self.bgpvpn_client.associate_network_to_bgpvpn(
            bgpvpn['id'], network_id)
        self.assertEqual(association['network_association']['network_id'],
                         network_id)
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['networks'], [network_id])

        # Disassociate the network from the bgpvpn resource
        self.bgpvpn_client.disassociate_network_from_bgpvpn(
            bgpvpn['id'],
            association['network_association']['id'])
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['networks'], [])

        self.networks_client.delete_network(network_id)
