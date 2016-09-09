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
from testtools import ExpectedException
import uuid


class BgpvpnTest(base):
    """Tests the following operations in the Neutron API:

        create bgpvpn
        delete bgpvpn
        show bgpvpn
        list bgpvpns
        associate network to bgpvpn
        disassociate network from bgpvpn
        show network association
        list network associations
        update route targets

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

    @test.attr(type=['negative'])
    def test_show_bgpvpn_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_alt_client.show_bgpvpn, bgpvpn['id'])

    @test.attr(type=['negative'])
    def test_list_bgpvpn_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        bgpvpns_alt = self.bgpvpn_alt_client.list_bgpvpns()['bgpvpns']
        self.assertNotIn(bgpvpn['id'],
                         [bgpvpn_alt['id'] for bgpvpn_alt in bgpvpns_alt])

    @test.attr(type=['negative'])
    def test_show_netassoc_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()['network']

        net_assoc = self.bgpvpn_client.create_network_association(
            bgpvpn['id'], network['id'])['network_association']

        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_alt_client.show_network_association,
                          bgpvpn['id'], net_assoc['id'])

    @test.attr(type=['negative'])
    def test_list_netassoc_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()['network']

        self.bgpvpn_client.create_network_association(bgpvpn['id'],
                                                      network['id'])
        net_assocs_alt = self.bgpvpn_alt_client\
            .list_network_associations(bgpvpn['id'])
        self.assertFalse(net_assocs_alt['network_associations'])

    def test_associate_disassociate_network(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()
        network_id = network['network']['id']

        # Associate the network to the bgpvpn resource
        association = self.bgpvpn_client.create_network_association(
            bgpvpn['id'], network_id)
        self.assertEqual(association['network_association']['network_id'],
                         network_id)
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['networks'], [network_id])

        # Disassociate the network from the bgpvpn resource
        self.bgpvpn_client.delete_network_association(
            bgpvpn['id'],
            association['network_association']['id'])
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['networks'], [])

        self.networks_client.delete_network(network_id)

    def test_update_route_target(self):
        bgpvpn = self.create_bgpvpn(
            self.bgpvpn_admin_client,
            route_targets=['64512:1'],
            import_targets=['64512:2'],
            export_targets=['64512:3'])
        bgpvpn = self.bgpvpn_admin_client.update_bgpvpn(
            bgpvpn['id'],
            route_targets=['64512:4'],
            import_targets=['64512:5'],
            export_targets=['64512:6']
        )['bgpvpn']
        self.assertEqual(['64512:4'], bgpvpn['route_targets'])
        self.assertEqual(['64512:5'], bgpvpn['import_targets'])
        self.assertEqual(['64512:6'], bgpvpn['export_targets'])

    @test.attr(type=['negative'])
    def test_update_route_target_non_admin_fail(self):
        bgpvpn = self.create_bgpvpn(
            self.bgpvpn_admin_client,
            tenant_id=self.bgpvpn_client.tenant_id,
            route_targets=['64512:1'])
        with ExpectedException(exceptions.Forbidden):
            self.bgpvpn_client.update_bgpvpn(
                bgpvpn['id'],
                route_targets=['64512:2'],
                import_targets=['64512:3'],
                export_targets=['64512:4'])

    @test.attr(type=['negative'])
    def test_create_bgpvpn_with_invalid_routetargets(self):
        """Create a bgpvpn with invalid route target

        This test verifies that invalid route targets,import targets,
        export targets are rejected by the Create API
        """
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
            "route_targets": ["0"]
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.create_bgpvpn, **postdata)
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
            "import_targets": ["test", " "]
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.create_bgpvpn, **postdata)
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
            "export_targets": ["64512:1000000000000", "xyz"]
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.create_bgpvpn, **postdata)

    @test.attr(type=['negative'])
    def test_update_bgpvpn_invalid_routetargets(self):
        """Update the bgpvpn with invalid route targets

        This test  verifies that invalid  route targets,import targets
        and export targets are rejected by the Update API
        """
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
        }
        bgpvpn = self.bgpvpn_admin_client.create_bgpvpn(**postdata)
        updatedata = {
            "route_targets": ["0"]
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.update_bgpvpn,
                          bgpvpn['bgpvpn']['id'], **updatedata)
        updatedata = {
            "import_targets": ["test", " "]
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.update_bgpvpn,
                          bgpvpn['bgpvpn']['id'], **updatedata)
        updatedata = {
            "export_targets": ["64512:1000000000000", "xyz"],
        }
        self.assertRaises(exceptions.BadRequest,
                          self.bgpvpn_admin_client.update_bgpvpn,
                          bgpvpn['bgpvpn']['id'], **updatedata)

    @test.attr(type=['negative'])
    def test_associate_invalid_network(self):
        """Associate the invalid network in bgpvpn

        This test verifies that invalid network id,bgpvpn id
        are rejected by the associate API
        """
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
        }
        bgpvpn = self.bgpvpn_admin_client.create_bgpvpn(**postdata)
        network = self.networks_client.create_network()
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.create_network_association,
                          bgpvpn['bgpvpn']['id'], uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.create_network_association,
                          uuid.uuid4(),
                          network['network']['id'])

    @test.attr(type=['negative'])
    def test_disassociate_invalid_network(self):
        """Disassociate the invalid network in bgpvpn

        This test verifies that invalid network id,
        bgpvpn id are rejected by the disassociate API
        """
        postdata = {
            "name": "testbgpvpn",
            "tenant_id": self.bgpvpn_client.tenant_id,
        }
        bgpvpn = self.bgpvpn_admin_client.create_bgpvpn(**postdata)
        network = self.networks_client.create_network()
        association = self.bgpvpn_client.create_network_association(
            bgpvpn['bgpvpn']['id'], network['network']['id'])
        self.assertEqual(association['network_association'][
                         'network_id'], network['network']['id'])
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.delete_network_association,
                          bgpvpn['bgpvpn']['id'],
                          uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.delete_network_association,
                          uuid.uuid4(),
                          association['network_association']['id'])

    def test_associate_disassociate_router(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        router = self.routers_client.create_router()
        router_id = router['router']['id']

        # Associate the network to the bgpvpn resource
        association = self.bgpvpn_client.create_router_association(
            bgpvpn['id'], router_id)
        self.assertEqual(association['router_association']['router_id'],
                         router_id)
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['routers'], [router_id])

        # Disassociate the network from the bgpvpn resource
        self.bgpvpn_client.delete_router_association(
            bgpvpn['id'],
            association['router_association']['id'])
        updated_bgpvpn = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])
        self.assertEqual(updated_bgpvpn['bgpvpn']['routers'], [])

        self.routers_client.delete_router(router_id)
