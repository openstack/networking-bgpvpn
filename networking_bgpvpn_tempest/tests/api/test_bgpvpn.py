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
from oslo_utils import uuidutils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from testtools import ExpectedException


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

    @decorators.idempotent_id('4f90deb2-eb8e-4e7d-9d68-c5b5cc657f7e')
    def test_create_bgpvpn(self):
        self.create_bgpvpn(self.bgpvpn_admin_client)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0a911d61-d908-4c21-a11e-e403ac0d8e38')
    def test_create_bgpvpn_as_non_admin_fail(self):
        self.assertRaises(exceptions.Forbidden,
                          self.create_bgpvpn, self.bgpvpn_client)

    @decorators.idempotent_id('709b23b0-9719-47df-9f53-b0812a5d5a48')
    def test_delete_bgpvpn(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        self.delete_bgpvpn(self.bgpvpn_admin_client, bgpvpn)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('596abfc2-fd89-491d-863d-25459db1df4b')
    def test_delete_bgpvpn_as_non_admin_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        self.assertRaises(exceptions.Forbidden,
                          self.bgpvpn_client.delete_bgpvpn, bgpvpn['id'])

    @decorators.idempotent_id('9fa29db8-35d0-4beb-a986-23c369499ab1')
    def test_show_bgpvpn(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        bgpvpn_details = self.bgpvpn_client.show_bgpvpn(bgpvpn['id'])['bgpvpn']
        self.assertEqual(bgpvpn['id'], bgpvpn_details['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b20110bb-393b-4342-8b30-6486cd2b4fc6')
    def test_show_bgpvpn_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_alt_client.show_bgpvpn, bgpvpn['id'])

    @decorators.idempotent_id('7a7feca2-1c24-4f5d-ad4b-b0e5a712adb1')
    def test_list_bgpvpn(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        bgpvpns = self.bgpvpn_client.list_bgpvpns()['bgpvpns']
        self.assertIn(bgpvpn['id'],
                      [bgpvpn_alt['id'] for bgpvpn_alt in bgpvpns])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4875e65d-0b65-40c0-9efd-309420686ab4')
    def test_list_bgpvpn_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        bgpvpns_alt = self.bgpvpn_alt_client.list_bgpvpns()['bgpvpns']
        self.assertNotIn(bgpvpn['id'],
                         [bgpvpn_alt['id'] for bgpvpn_alt in bgpvpns_alt])

    @decorators.idempotent_id('096281da-356d-4c04-bd55-784a26bb1b0c')
    def test_list_show_network_association(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()['network']

        association = self.bgpvpn_client.create_network_association(
            bgpvpn['id'], network['id'])['network_association']
        net_assocs = self.bgpvpn_client\
            .list_network_associations(bgpvpn['id'])['network_associations']
        self.assertIn(association['id'],
                      [net_assoc['id'] for net_assoc in net_assocs])
        net_assoc_details = self.bgpvpn_client\
            .show_network_association(bgpvpn['id'],
                                      association['id'])['network_association']
        self.assertEqual(association['id'], net_assoc_details['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('57b0da93-8e37-459f-9aaf-f903acc36025')
    def test_show_netassoc_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()['network']

        net_assoc = self.bgpvpn_client.create_network_association(
            bgpvpn['id'], network['id'])['network_association']

        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_alt_client.show_network_association,
                          bgpvpn['id'], net_assoc['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('2cbb10af-bf9c-4b32-b6a6-4066de783758')
    def test_list_netassoc_as_non_owner_fail(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        network = self.networks_client.create_network()['network']

        self.bgpvpn_client.create_network_association(bgpvpn['id'],
                                                      network['id'])
        net_assocs_alt = self.bgpvpn_alt_client\
            .list_network_associations(bgpvpn['id'])
        self.assertFalse(net_assocs_alt['network_associations'])

    @decorators.idempotent_id('51e1b079-aefa-4c37-8b1a-0567b3ef7954')
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

    @decorators.idempotent_id('559013fd-1e34-4fde-9599-f8aafe9ae716')
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e35eb9be-fe1f-406c-b36b-fc1879328313')
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('464ca6f9-86e4-4ee3-9c65-f1edae93223d')
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7d4e9b87-e1ab-47a7-a8d6-9d179365556a')
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

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f049ce21-d239-47c0-b13f-fb57a2a558ce')
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
                          bgpvpn['bgpvpn']['id'], uuidutils.generate_uuid())
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.create_network_association,
                          uuidutils.generate_uuid(),
                          network['network']['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('078b2660-4adb-4c4c-abf0-b77bf0bface5')
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
                          uuidutils.generate_uuid())
        self.assertRaises(exceptions.NotFound,
                          self.bgpvpn_client.delete_network_association,
                          uuidutils.generate_uuid(),
                          association['network_association']['id'])

    @decorators.idempotent_id('de8d94b0-0239-4a48-9574-c3a4a4f7cacb')
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

    @decorators.idempotent_id('3ae91755-b1b6-4c62-a699-a44eeb4ee522')
    def test_list_show_router_association(self):
        bgpvpn = self.create_bgpvpn(self.bgpvpn_admin_client,
                                    tenant_id=self.bgpvpn_client.tenant_id)
        router = self.routers_client.create_router()
        router_id = router['router']['id']

        association = self.bgpvpn_client.create_router_association(
            bgpvpn['id'], router_id)['router_association']
        rtr_assocs = self.bgpvpn_client\
            .list_router_associations(bgpvpn['id'])['router_associations']
        self.assertIn(association['id'],
                      [rtr_assoc['id'] for rtr_assoc in rtr_assocs])
        rtr_assoc_details = self.bgpvpn_client\
            .show_router_association(bgpvpn['id'],
                                     association['id'])['router_association']
        self.assertEqual(association['id'], rtr_assoc_details['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4be1f073-fe57-4858-b7b9-9a189e90b770')
    def test_attach_associated_subnet_to_associated_router(self):
        # Create a first bgpvpn and associate a network with a subnet to it
        bgpvpn_net = self.create_bgpvpn(
            self.bgpvpn_admin_client,
            tenant_id=self.bgpvpn_client.tenant_id)
        network = self.create_network()
        subnet = self.create_subnet(network)
        self.bgpvpn_client.create_network_association(
            bgpvpn_net['id'], network['id'])

        # Create a second bgpvpn and associate a router to it
        bgpvpn_router = self.create_bgpvpn(
            self.bgpvpn_admin_client,
            tenant_id=self.bgpvpn_client.tenant_id)

        router = self.create_router(
            router_name=data_utils.rand_name('test-bgpvpn-'))
        self.bgpvpn_client.create_router_association(
            bgpvpn_router['id'],
            router['id'])

        # Attach the subnet of the network to the router
        subnet_data = {'subnet_id': subnet['id']}
        self.assertRaises(exceptions.Conflict,
                          self.routers_client.add_router_interface,
                          router['id'],
                          **subnet_data)
