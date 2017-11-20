# Copyright 2016 Cisco Systems, Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging
from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

from networking_bgpvpn_tempest.tests import base
from networking_bgpvpn_tempest.tests.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)
RT1 = '64512:1'
RT2 = '64512:2'
NET_A = 'A'
NET_A_BIS = 'A-Bis'
NET_B = 'B'
NET_A_S1 = '10.101.11.0/24'
NET_A_S2 = '10.101.12.0/24'
NET_B_S1 = '10.102.21.0/24'
NET_B_S2 = '10.102.22.0/24'
IP_A_S1_1 = '10.101.11.10'
IP_B_S1_1 = '10.102.21.20'
IP_A_S1_2 = '10.101.11.30'
IP_B_S1_2 = '10.102.21.40'
IP_A_S1_3 = '10.101.11.50'
IP_B_S1_3 = '10.102.21.60'
IP_A_S2_1 = '10.101.12.50'
IP_B_S2_1 = '10.102.22.60'
IP_A_BIS_S1_1 = IP_A_S1_1
IP_A_BIS_S1_2 = IP_A_S1_2
IP_A_BIS_S1_3 = IP_A_S1_3
IP_A_BIS_S2_1 = IP_A_S2_1


class TestBGPVPNBasic(base.BaseBgpvpnTest, manager.NetworkScenarioTest):
    def setUp(self):
        super(TestBGPVPNBasic, self).setUp()
        self.servers_keypairs = {}
        self.servers = []
        self.server_fixed_ips = {}
        self.ports = {}
        self.networks = {}
        self.subnets = {}
        self.server_fips = {}
        self._create_security_group_for_test()

    @utils.services('compute', 'network')
    def test_bgpvpn_basic(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Associate network A and network B to a given L3 BGPVPN
        5. Create router and connect it to network A
        6. Give a FIP to server 1
        7. Check that server 1 can ping server 2
        """

        self._create_networks_and_subnets()
        self._create_servers()
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant1(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Associate network A and network B to a given L3 BGPVPN
        3. Start up server 1 in network A
        4. Start up server 2 in network B
        5. Create router and connect it to network A
        6. Give a FIP to server 1
        7. Check that server 1 can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant2(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Create router and associate to network B
        5. Associate network A and network B to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self.router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant3(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Create router and connect it to network B
        5. Associate network A and network B to a given L3 BGPVPN
        6. Delete router associated to network B
        7. Create router and connect it to network A
        8. Give a FIP to server 1
        9. Check that server 1 can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self.router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self.delete_router(self.router_b)
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant4(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Associate network A and network B to a given L3 BGPVPN
        5. Create router and connect it to network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 2 can ping server 1
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self.router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant5(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create router and connect it to network B
        3. Associate network A and network B to a given L3 BGPVPN
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 2 can ping server 1
        """
        self._create_networks_and_subnets()
        self.router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_variant6(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Associate network A and network B to a given L3 BGPVPN
        3. Create router and connect it to network B
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 2 can ping server 1
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self.router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_update_route_targets_disjoint_targets(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Create L3 BGPVPN with only RT defined
        5. Associate network A to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Update L3 BGPVPN to have eRT<>iRT and no RT what is insufficient
           for proper connectivity between network A and B
        10. Check that server 1 cannot ping server 2
        11. Update L3 BGPVPN to have again only RT defined
        12. Check that server 1 can ping again server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self._create_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[RT1], export_rts=[RT2])
        self._check_l3_bgpvpn(should_succeed=False)
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_update_route_targets_common_target(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Create L3 BGPVPN with only RT defined
        5. Associate network A to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Update L3 BGPVPN to have eRT<>iRT and RT=iRT
        10. Check that server 1 can ping server 2
        11. Update L3 BGPVPN to have again only RT defined
        12. Check that server 1 can ping again server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self._create_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[RT1], export_rts=[RT2])
        self._check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_update_route_targets_and_unassociated_net(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Create invalid L3 BGPVPN with eRT<>iRT that is insufficient
           for proper connectivity between network A and B
        5. Associate network A to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 cannot ping server 2
        9. Associate network B to a given L3 BGPVPN
        10. Check that server 1 cannot ping server 2
        11. Update L3 BGPVPN to have only RT defined
        12. Check that server 1 can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self.router = self._create_router_and_associate_fip(
            0, self.subnets[NET_A][0])
        self._create_l3_bgpvpn(rts=[], export_rts=[RT1], import_rts=[RT2])
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_B]['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @utils.services('compute', 'network')
    def test_bgpvpn_update_rt_and_keep_local_connectivity_variant1(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Start up server 3 in network A
        5. Start up server 4 in network B
        6. Create invalid L3 BGPVPN with eRT<>iRT that is insufficient
           for proper connectivity between network A and B
        7. Associate network A to a given L3 BGPVPN
        8. Create router A and connect it to network A
        9. Give a FIP to server 1
        10. Check that server 1 cannot ping server 2
        11. Check that server 1 can ping server 3
        12. Associate network B to a given L3 BGPVPN
        13. Create router B and connect it to network B
        14. Give a FIP to server 2
        15. Check that server 1 still cannot ping server 2
        16. Check that server 2 can ping server 4
        17. Update L3 BGPVPN to have now only RT defined
        18. Check that server 1 can now ping server 2
        19. Check that server 1 still can ping server 3
        20. Check that server 2 still can ping server 4
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn(rts=[], import_rts=[RT1], export_rts=[RT2])
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                             [self.networks[NET_B], IP_B_S1_1],
                             [self.networks[NET_A], IP_A_S1_2],
                             [self.networks[NET_B], IP_B_S1_2]])
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        self.router_a = self._create_router_and_associate_fip(
            0, self.subnets[NET_A][0])
        self._check_l3_bgpvpn(should_succeed=False)
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_B]['id'])
        self.router_b = self._create_router_and_associate_fip(
            1, self.subnets[NET_B][0])
        self._check_l3_bgpvpn(should_succeed=False)
        self._check_l3_bgpvpn(self.servers[1], self.servers[3])
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self._check_l3_bgpvpn(self.servers[1], self.servers[3])

    @utils.services('compute', 'network')
    def test_bgpvpn_update_rt_and_keep_local_connectivity_variant2(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Start up server 1 in network A
        3. Start up server 2 in network B
        4. Start up server 3 in network A
        5. Start up server 4 in network B
        6. Create invalid L3 BGPVPN with eRT<>iRT that is insufficient
           for proper connectivity between network A and B
        7. Create router A and connect it to network A
        8. Give a FIP to server 1
        9. Create router B and connect it to network B
        10. Give a FIP to server 4
        11. Associate network A to a given L3 BGPVPN
        12. Check that server 1 cannot ping server 2
        13. Check that server 1 can ping server 3
        14. Associate router B to a given L3 BGPVPN
        15. Check that server 1 still cannot ping server 2
        16. Check that server 4 can ping server 2
        17. Update L3 BGPVPN to have now only RT defined
        18. Check that server 1 can now ping server 2
        19. Check that server 1 still can ping server 3
        20. Check that server 4 still can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn(rts=[], import_rts=[RT1], export_rts=[RT2])
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                             [self.networks[NET_B], IP_B_S1_1],
                             [self.networks[NET_A], IP_A_S1_2],
                             [self.networks[NET_B], IP_B_S1_2]])
        self._create_router_and_associate_fip(
            0, self.subnets[NET_A][0])
        router_b = self._create_router_and_associate_fip(
            3, self.subnets[NET_B][0])
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self.bgpvpn_client.create_router_association(self.bgpvpn['id'],
                                                     router_b['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self._check_l3_bgpvpn(self.servers[3], self.servers[1])
        self._update_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self._check_l3_bgpvpn(self.servers[3], self.servers[1])

    @utils.services('compute', 'network')
    def test_bgpvpn_tenant_separation_and_local_connectivity(self):
        """This test checks tenant separation for BGPVPN.

        1. Create networks A with subnet S1 and S2
        2. Create networks A-Bis with subnet S1 and S2 (like for network A)
        3. Create L3 BGPVPN for network A with RT1
        4. Create L3 BGPVPN for network A-Bis with RT2
        5. Associate network A to a given L3 BGPVPN
        6. Associate network A-Bis to a given L3 BGPVPN
        7. Start up server 1 in network A and subnet S1
        8. Start up server 2 in network A-Bis and subnet S1
        9. Start up server 3 in network A and subnet S1
        10. Start up server 4 in network A-Bis and subnet S1
        11. Start up server 5 in network A and subnet S1
        12. Create router A and connect it to network A
        13. Create router A-Bis and connect it to network A-Bis
        14. Give a FIP to all servers
        15. Setup dummy HTTP service on server 2 and 3
        16. Check that server 1 pings server 3 instead of server 2
        17. Check that server 1 can ping server 3
        18. Check that server 2 cannot ping server 1
        19. Check that server 2 pings itself instead of server 3
        20. Check that server 2 can ping server 4
        21. Check that server 2 pings server 4 instead of server 5
        """
        self._create_networks_and_subnets([NET_A, NET_A_BIS],
                                          [[NET_A_S1, NET_A_S2],
                                           [NET_A_S1, NET_A_S2]])
        bgpvpn_a = self._create_l3_bgpvpn(name='test-l3-bgpvpn-a',
                                          rts=[RT1])
        bgpvpn_a_bis = self._create_l3_bgpvpn(name='test-l3-bgpvpn-a-bis',
                                              rts=[RT2])
        self.bgpvpn_client.create_network_association(
            bgpvpn_a['id'], self.networks[NET_A]['id'])
        self.bgpvpn_client.create_network_association(
            bgpvpn_a_bis['id'], self.networks[NET_A_BIS]['id'])
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                             [self.networks[NET_A_BIS], IP_A_BIS_S1_2],
                             [self.networks[NET_A], IP_A_S1_2],
                             [self.networks[NET_A_BIS], IP_A_BIS_S1_3],
                             [self.networks[NET_A], IP_A_S1_3]])
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_A_BIS][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)
        self._associate_fip(2)
        self._associate_fip(3)
        self._associate_fip(4)
        self._setup_http_server(1)
        self._setup_http_server(2)
        self._setup_http_server(3)
        self._setup_http_server(4)
        self._check_l3_bgpvpn(self.servers[0], self.servers[1],
                              should_succeed=False, validate_server=True)
        self._check_l3_bgpvpn(self.servers[0], self.servers[2],
                              validate_server=True)
        self._check_l3_bgpvpn(self.servers[1], self.servers[0],
                              should_succeed=False)
        self._check_l3_bgpvpn(self.servers[1], self.servers[2],
                              should_succeed=False, validate_server=True)
        self._check_l3_bgpvpn(self.servers[1], self.servers[3],
                              validate_server=True)
        self._check_l3_bgpvpn(self.servers[1], self.servers[4],
                              should_succeed=False, validate_server=True)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_ping_to_unassociated_net(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Associate network A to a given L3 BGPVPN
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn()
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_disjoint_import_export(self):
        """This test checks basic BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create invalid L3 BGPVPN with eRT<>iRT that is insufficient
           for proper connectivity between network A and B
        3. Associate network A and B to a given L3 BGPVPN
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn(rts=[], import_rts=[RT1], export_rts=[RT2])
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_delete_bgpvpn(self):
        """This test checks BGPVPN delete.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Associate network A and network B to a given L3 BGPVPN
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Delete L3 BGPVPN
        10. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()
        self.delete_bgpvpn(self.bgpvpn_admin_client, self.bgpvpn)
        self._check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_delete_net_association(self):
        """This test checks BGPVPN net association delete.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Associate network A and network B to a given L3 BGPVPN
        4. Start up server 1 in network A
        5. Start up server 2 in network B
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Delete association of network A
        10. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn()
        body = self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        assoc_b = body['network_association']
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_B]['id'])
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()
        self.bgpvpn_admin_client.delete_network_association(self.bgpvpn['id'],
                                                            assoc_b['id'])
        self._check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_delete_router_association(self):
        """This test checks BGPVPN router association delete.

        1. Create networks A and B with their respective subnets
        2. Create router and connect it to network B
        3. Create L3 BGPVPN
        4. Associate network A to a given L3 BGPVPN
        5. Associate router B to a given L3 BGPVPN
        6. Start up server 1 in network A
        7. Start up server 2 in network B
        8. Create router and connect it to network A
        9. Give a FIP to server 1
        10. Check that server 1 can ping server 2
        11. Delete association of router B
        12. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        router_b = self._create_fip_router(
            subnet_id=self.subnets[NET_B][0]['id'])
        self._create_l3_bgpvpn()
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        body = self.bgpvpn_client.create_router_association(self.bgpvpn['id'],
                                                            router_b['id'])
        assoc_b = body['router_association']
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()
        self.bgpvpn_admin_client.delete_router_association(self.bgpvpn['id'],
                                                           assoc_b['id'])
        self._check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    def test_bgpvpn_negative_update_to_disjoint_import_export(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN with only RT defined
        3. Start up server 1 in network A
        4. Start up server 2 in network B
        5. Associate network A to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Update L3 BGPVPN to have eRT<>iRT and no RT what is insufficient
           for proper connectivity between network A and B
        10. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._create_servers()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[RT1], export_rts=[RT2])
        self._check_l3_bgpvpn(should_succeed=False)

    @utils.services('compute', 'network')
    @decorators.skip_because(bug="1732070")
    def test_bgpvpn_negative_update_to_empty_rt_list(self):
        """This test checks basic BGPVPN route targets update.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN with only RT defined
        3. Start up server 1 in network A
        4. Start up server 2 in network B
        5. Associate network A and B to a given L3 BGPVPN
        6. Create router and connect it to network A
        7. Give a FIP to server 1
        8. Check that server 1 can ping server 2
        9. Update L3 BGPVPN to empty RT list what is insufficient
           for proper connectivity between network A and B
        10. Check that server 1 cannot ping server 2
        """
        self._create_networks_and_subnets()
        self._create_l3_bgpvpn(rts=[RT1], import_rts=[], export_rts=[])
        self._create_servers()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn(should_succeed=False)

    def _create_security_group_for_test(self):
        self.security_group = self._create_security_group(
            tenant_id=self.bgpvpn_client.tenant_id)

    def _create_networks_and_subnets(self, names=None, subnet_cidrs=None):
        if not names:
            names = [NET_A, NET_B]
        if not subnet_cidrs:
            subnet_cidrs = [[NET_A_S1], [NET_B_S1]]
        for (name, subnet_cidrs) in zip(names, subnet_cidrs):
            network = self._create_network(namestart=name)
            self.networks[name] = network
            self.subnets[name] = []
            for (j, cidr) in enumerate(subnet_cidrs):
                sub_name = "subnet-%s-%d" % (name, j + 1)
                subnet = self._create_subnet_with_cidr(network,
                                                       namestart=sub_name,
                                                       cidr=cidr,
                                                       ip_version=4)
                self.subnets[name].append(subnet)

    def _create_subnet_with_cidr(self, network, subnets_client=None,
                                 namestart='subnet-smoke', **kwargs):
        if not subnets_client:
            subnets_client = self.subnets_client
        tenant_cidr = kwargs.get('cidr')
        subnet = dict(
            name=data_utils.rand_name(namestart),
            network_id=network['id'],
            tenant_id=network['tenant_id'],
            **kwargs)
        result = subnets_client.create_subnet(**subnet)
        self.assertIsNotNone(result, 'Unable to allocate tenant network')
        subnet = result['subnet']
        self.assertEqual(subnet['cidr'], tenant_cidr)
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        subnets_client.delete_subnet, subnet['id'])
        return subnet

    def _create_fip_router(self, client=None, public_network_id=None,
                           subnet_id=None):
        router = self._create_router(client, namestart='router-')
        router_id = router['id']
        if public_network_id is None:
            public_network_id = CONF.network.public_network_id
        if client is None:
            client = self.routers_client
        kwargs = {'external_gateway_info': {'network_id': public_network_id}}
        router = client.update_router(router_id, **kwargs)['router']
        if subnet_id is not None:
            client.add_router_interface(router_id, subnet_id=subnet_id)
            self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                            client.remove_router_interface, router_id,
                            subnet_id=subnet_id)
        return router

    def _associate_fip(self, server_index):
        server = self.servers[server_index]
        fip = self.create_floating_ip(
            server, external_network_id=CONF.network.public_network_id,
            port_id=self.ports[server['id']]['id'])
        self.server_fips[server['id']] = fip
        return fip

    def _create_router_and_associate_fip(self, server_index, subnet):
        router = self._create_fip_router(subnet_id=subnet['id'])
        self._associate_fip(server_index)
        return router

    def _create_server(self, name, keypair, network, ip_address,
                       security_group_ids, clients):
        create_port_body = {'fixed_ips': [{'ip_address': ip_address}],
                            'namestart': 'port-smoke',
                            'security_groups': security_group_ids}
        port = self._create_port(network_id=network['id'],
                                 client=clients.ports_client,
                                 **create_port_body)
        create_server_kwargs = {
            'key_name': keypair['name'],
            'networks': [{'uuid': network['id'], 'port': port['id']}]
        }
        body, servers = compute.create_test_server(
            clients, wait_until='ACTIVE', name=name, **create_server_kwargs)
        self.addCleanup(waiters.wait_for_server_termination,
                        clients.servers_client, body['id'])
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        clients.servers_client.delete_server, body['id'])
        server = clients.servers_client.show_server(body['id'])['server']
        LOG.debug('Created server: %s with status: %s', server['id'],
                  server['status'])
        self.ports[server['id']] = port
        return server

    def _create_servers(self, ports_config=None):
        keypair = self.create_keypair()
        security_group_ids = [self.security_group['id']]
        if ports_config is None:
            ports_config = [[self.networks[NET_A], IP_A_S1_1],
                            [self.networks[NET_B], IP_B_S1_1]]
        for (i, port_config) in enumerate(ports_config):
            network = port_config[0]
            server = self._create_server(
                'server-' + str(i + 1), keypair, network, port_config[1],
                security_group_ids, self.os_primary)
            self.servers.append(server)
            self.servers_keypairs[server['id']] = keypair
            self.server_fixed_ips[server['id']] = (
                server['addresses'][network['name']][0]['addr'])
            self.assertTrue(self.servers_keypairs)

    def _create_l3_bgpvpn(self, name='test-l3-bgpvpn', rts=None,
                          import_rts=None, export_rts=None):
        if rts is None:
            rts = [RT1]
        import_rts = import_rts or []
        export_rts = export_rts or []
        self.bgpvpn = self.create_bgpvpn(
            self.bgpvpn_admin_client, tenant_id=self.bgpvpn_client.tenant_id,
            name=name, route_targets=rts, export_targets=export_rts,
            import_targets=import_rts)
        return self.bgpvpn

    def _update_l3_bgpvpn(self, rts=None, import_rts=None, export_rts=None,
                          bgpvpn=None):
        bgpvpn = bgpvpn or self.bgpvpn
        if rts is None:
            rts = [RT1]
        import_rts = import_rts or []
        export_rts = export_rts or []
        LOG.debug('Updating targets in BGPVPN %s', bgpvpn['id'])
        self.bgpvpn_admin_client.update_bgpvpn(bgpvpn['id'],
                                               route_targets=rts,
                                               export_targets=export_rts,
                                               import_targets=import_rts)

    def _associate_all_nets_to_bgpvpn(self, bgpvpn=None):
        bgpvpn = bgpvpn or self.bgpvpn
        for network in self.networks.values():
            self.bgpvpn_client.create_network_association(
                bgpvpn['id'], network['id'])
        LOG.debug('BGPVPN network associations completed')

    def _setup_ssh_client(self, server):
        server_fip = self.server_fips[server['id']][
            'floating_ip_address']
        private_key = self.servers_keypairs[server['id']][
            'private_key']
        ssh_client = self.get_remote_client(server_fip,
                                            private_key=private_key)
        return ssh_client

    def _setup_http_server(self, server_index):
        server = self.servers[server_index]
        ssh_client = self._setup_ssh_client(server)
        ssh_client.exec_command("sudo nc -kl -p 80 -e echo '%s' &"
                                % server['name'])

    def _log_gw_arp_info(self, ssh_client, gateway_ip):
        output = ssh_client.exec_command('arp -n %s' % gateway_ip)
        LOG.warning("Ping origin server GW ARP info:")
        LOG.warning(output)

    def _check_l3_bgpvpn(self, from_server=None, to_server=None,
                         should_succeed=True, validate_server=False):
        from_server = from_server or self.servers[0]
        to_server = to_server or self.servers[1]
        server_1_ip = self.server_fips[from_server['id']][
            'floating_ip_address']
        server_2_ip = self.server_fixed_ips[to_server['id']]
        ssh_client = self._setup_ssh_client(from_server)
        try:
            should_be_reachable = should_succeed or validate_server
            msg = ""
            if should_be_reachable:
                msg = "Timed out waiting for {ip} to become reachable".format(
                    ip=server_2_ip)
            else:
                msg = ("Unexpected ping response from VM with IP address "
                       "{dest} originated from VM with IP address "
                       "{src}").format(dest=server_2_ip, src=server_1_ip)
            result = self._check_remote_connectivity(ssh_client, server_2_ip,
                                                     should_be_reachable)
            if should_be_reachable and not result:
                allocation = self.ports[from_server['id']]['fixed_ips'][0]
                subnet_id = allocation['subnet_id']
                gateway_ip = ''
                for net_name in self.subnets:
                    for subnet in self.subnets[net_name]:
                        if subnet_id == subnet['id']:
                            gateway_ip = subnet['gateway_ip']
                            break
                self._log_gw_arp_info(ssh_client, gateway_ip)
                ssh_client.exec_command('sudo arp -d %s' % gateway_ip)
                LOG.warning("Ping origin server GW ARP cleared")
                ssh_client.ping_host(gateway_ip)
                self._log_gw_arp_info(ssh_client, gateway_ip)
                result = self._check_remote_connectivity(ssh_client,
                                                         server_2_ip,
                                                         should_be_reachable)
            self.assertTrue(result, msg)
            if validate_server and result:
                to_name = ssh_client.exec_command(
                    "nc %s 80" % server_2_ip).strip()
                result = to_name == to_server['name']
                self.assertTrue(should_succeed == result,
                                ("Destination server name is invalid. Has '"
                                 "{name}', expected is '{exp}'").format(
                                     name=to_name, exp=to_server['name']))
        except Exception:
            LOG.exception(("Unable to ping VM with IP address {dest} from VM "
                           "with IP address {src}").format(dest=server_2_ip,
                                                           src=server_1_ip))
            raise

    def _associate_fip_and_check_l3_bgpvpn(self, should_succeed=True):
        subnet = self.subnets[NET_A][0]
        self.router = self._create_router_and_associate_fip(0, subnet)
        self._check_l3_bgpvpn(should_succeed=should_succeed)
