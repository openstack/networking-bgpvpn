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

import functools
import netaddr
import os
import random

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

from oslo_concurrency import lockutils


# TODO(tmorin): move to neutron-lib
# code copied from neutron repository - neutron/tests/base.py
def unstable_test(reason):
    def decor(f):
        @functools.wraps(f)
        def inner(self, *args, **kwargs):
            try:
                return f(self, *args, **kwargs)
            except Exception as e:
                msg = ("%s was marked as unstable because of %s, "
                       "failure was: %s") % (self.id(), reason, e)
                raise self.skipTest(msg)
        return inner
    return decor


CONF = config.CONF
LOG = logging.getLogger(__name__)
NET_A = 'A'
NET_A_BIS = 'A-Bis'
NET_B = 'B'
NET_C = 'C'

if "SUBNETPOOL_PREFIX_V4" in os.environ:
    subnet_base = netaddr.IPNetwork(os.environ['SUBNETPOOL_PREFIX_V4'])
    if subnet_base.prefixlen > 21:
        raise Exception("if SUBNETPOOL_PREFIX_V4 is set, it needs to offer "
                        "space for at least 8 /24 subnets")
else:
    subnet_base = netaddr.IPNetwork("10.100.0.0/16")


def assign_24(idx):
    # how many addresses in a /24:
    range_size = 2 ** (32 - 24)
    return netaddr.cidr_merge(
        subnet_base[range_size * idx:range_size * (idx + 1)]
        )[0]


S1A = assign_24(1)
S2A = assign_24(2)
S1B = assign_24(4)
S2B = assign_24(6)
S1C = assign_24(6)
NET_A_S1 = str(S1A)
NET_A_S2 = str(S2A)
NET_B_S1 = str(S1B)
NET_B_S2 = str(S2B)
NET_C_S1 = str(S1C)
IP_A_S1_1 = str(S1A[10])
IP_B_S1_1 = str(S1B[20])
IP_C_S1_1 = str(S1C[30])
IP_A_S1_2 = str(S1A[30])
IP_B_S1_2 = str(S1B[40])
IP_A_S1_3 = str(S1A[50])
IP_B_S1_3 = str(S1B[60])
IP_A_S2_1 = str(S2A[50])
IP_B_S2_1 = str(S2B[60])
IP_A_BIS_S1_1 = IP_A_S1_1
IP_A_BIS_S1_2 = IP_A_S1_2
IP_A_BIS_S1_3 = IP_A_S1_3
IP_A_BIS_S2_1 = IP_A_S2_1


class TestBGPVPNBasic(base.BaseBgpvpnTest, manager.NetworkScenarioTest):

    @classmethod
    def setUpClass(cls):
        super(TestBGPVPNBasic, cls).setUpClass()
        cls._rt_index = 0

    @classmethod
    @lockutils.synchronized('bgpvpn')
    def new_rt(cls):
        cls._rt_index += 1
        return "64512:%d" % cls._rt_index

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
        self.RT1 = self.new_rt()
        self.RT2 = self.new_rt()
        self.RT3 = self.new_rt()
        self.RT4 = self.new_rt()

    @decorators.idempotent_id('afdd6cad-871a-4343-b97b-6319c76c815d')
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

    @decorators.idempotent_id('8a5a6fac-313c-464b-9c5c-29d4e1c0a51e')
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

    @decorators.idempotent_id('e7468636-0816-4092-82ca-3590680ed00b')
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

    @decorators.idempotent_id('7c66aa31-fb3a-4e15-8808-46eb361f153a')
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

    @decorators.idempotent_id('973ab26d-c7d8-4a32-9aa9-2d7e6f406135')
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

    @decorators.idempotent_id('2ac0696b-e828-4299-9e94-5f9c4988d961')
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

    @decorators.idempotent_id('9081338e-a52e-46bb-a40e-bda24ec4b1bd')
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

    @decorators.idempotent_id('133497a1-2788-40f7-be01-b3b64b5ef8cd')
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
        self._create_l3_bgpvpn(rts=[self.RT1], import_rts=[],
                               export_rts=[])
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[self.RT1],
                               export_rts=[self.RT2])
        self._check_l3_bgpvpn(should_succeed=False)
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @decorators.idempotent_id('bf417cad-0bc4-446a-b367-850aa619ca4f')
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
        self._create_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[self.RT1],
                               export_rts=[self.RT2])
        self._check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @decorators.idempotent_id('08d4f40e-3cec-485b-9da2-76e67fbd9881')
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
        self._create_l3_bgpvpn(rts=[], export_rts=[self.RT1],
                               import_rts=[self.RT2])
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_B]['id'])
        self._check_l3_bgpvpn(should_succeed=False)
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()

    @decorators.idempotent_id('c8bfd695-f731-47a6-86e3-3dfa492e08e0')
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
        self._create_l3_bgpvpn(rts=[], import_rts=[self.RT1],
                               export_rts=[self.RT2])
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
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self._check_l3_bgpvpn(self.servers[1], self.servers[3])

    @decorators.idempotent_id('758a8731-5070-4b1e-9a66-d6ff05bb5be1')
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
        self._create_l3_bgpvpn(rts=[], import_rts=[self.RT1],
                               export_rts=[self.RT2])
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
        self._update_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn()
        self._check_l3_bgpvpn(self.servers[0], self.servers[2])
        self._check_l3_bgpvpn(self.servers[3], self.servers[1])

    @decorators.idempotent_id('876b49bc-f34a-451b-ba3c-d74295838130')
    @utils.services('compute', 'network')
    @utils.requires_ext(extension='bgpvpn-routes-control', service='network')
    def test_bgpvpn_port_association_local_pref(self):
        """This test checks port association in BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Start up server 1 in network A
        4. Start up server 2 in network B
        5. Start up server 3 in network B
        6. Create router and connect it to network A
        7. Create router and connect it to network B
        8. Give a FIP to all servers
        9. Setup dummy HTTP service on server 2 and 3
        10. Configure ip forwarding on server 2
        11. Configure ip forwarding on server 3
        12. Configure alternative loopback address on server 2
        13. Configure alternative loopback address on server 3
        14. Associate network A to a given L3 BGPVPN
        15. Associate port of server 2 to a given L3 BGPVPN
            with higher local_pref value
        16. Associate port of server 3 to a given L3 BGPVPN
            with lower local_pref value
        17. Check that server 1 pings server's 2 alternative ip
        18. Update port association of server 2 to have now
            lower local_pref value
        19. Update port association of server 3 to have now
            higher local_pref value
        20. Check that server 1 pings now server's 3 alternative ip
        """
        self._create_networks_and_subnets(port_security=False)
        self._create_l3_bgpvpn()
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                             [self.networks[NET_B], IP_B_S1_1],
                             [self.networks[NET_B], IP_B_S1_2]],
                             port_security=False)
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_B][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)
        self._associate_fip(2)
        self._setup_http_server(1)
        self._setup_http_server(2)
        self._setup_ip_forwarding(1)
        self._setup_ip_forwarding(2)
        self._setup_ip_address(1, IP_C_S1_1)
        self._setup_ip_address(2, IP_C_S1_1)

        primary_port_routes = [{'type': 'prefix',
                                'local_pref': 200,
                                'prefix': NET_C_S1}]
        alternate_port_routes = [{'type': 'prefix',
                                  'local_pref': 100,
                                  'prefix': NET_C_S1}]

        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])

        port_id_1 = self.ports[self.servers[1]['id']]['id']
        body = self.bgpvpn_client.create_port_association(
            self.bgpvpn['id'], port_id=port_id_1, routes=primary_port_routes)
        port_association_1 = body['port_association']

        port_id_2 = self.ports[self.servers[2]['id']]['id']
        body = self.bgpvpn_client.create_port_association(
            self.bgpvpn['id'], port_id=port_id_2, routes=alternate_port_routes)
        port_association_2 = body['port_association']

        destination_srv_1 = '%s:%s' % (self.servers[1]['name'],
                                       self.servers[1]['id'])
        destination_srv_2 = '%s:%s' % (self.servers[2]['name'],
                                       self.servers[2]['id'])

        self._check_l3_bgpvpn_by_specific_ip(
            to_server_ip=IP_C_S1_1,
            validate_server=destination_srv_1)

        self.bgpvpn_client.update_port_association(
            self.bgpvpn['id'], port_association_1['id'],
            routes=alternate_port_routes)
        self.bgpvpn_client.update_port_association(
            self.bgpvpn['id'], port_association_2['id'],
            routes=primary_port_routes)

        self._check_l3_bgpvpn_by_specific_ip(
            to_server_ip=IP_C_S1_1,
            validate_server=destination_srv_2)

    @decorators.idempotent_id('f762e6ac-920e-4d0f-aa67-02bdd4ab8433')
    @utils.services('compute', 'network')
    def test_bgpvpn_tenant_separation_and_local_connectivity(self):
        """This test checks tenant separation for BGPVPN.

        1. Create networks A with subnet S1 and S2
        2. Create networks A-Bis with subnet S1 and S2 (like for network A)
        3. Create L3 BGPVPN for network A with self.RT1
        4. Create L3 BGPVPN for network A-Bis with self.RT2
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
                                          rts=[self.RT1])
        bgpvpn_a_bis = self._create_l3_bgpvpn(name='test-l3-bgpvpn-a-bis',
                                              rts=[self.RT2])
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

    @decorators.idempotent_id('3b44b2f4-f514-4004-8623-2682bc46bb07')
    @utils.services('compute', 'network')
    @utils.requires_ext(extension='bgpvpn-routes-control', service='network')
    def test_bgpvpn_port_association_create_and_update(self):
        """This test checks port association in BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Create router and connect it to network A
        4. Create router and connect it to network B
        5. Start up server 1 in network A
        6. Start up server 2 in network B
        7. Give a FIP to all servers
        8. Configure ip forwarding on server 2
        9. Configure alternative loopback address on server 2
        10. Associate network A to a given L3 BGPVPN
        11. Associate port of server 2 to a given L3 BGPVPN
        12. Check that server 1 can ping server's 2 alternative ip
        13. Update created before port association by routes removal
        14. Check that server 1 cannot ping server's 2 alternative ip
        """
        self._create_networks_and_subnets(port_security=False)
        self._create_l3_bgpvpn()
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                              [self.networks[NET_B], IP_B_S1_1]],
                             port_security=False)
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_B][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)

        # preliminary check that no connectivity to 192.168.0.1 initially
        # exists
        self._check_l3_bgpvpn_by_specific_ip(
            should_succeed=False, to_server_ip=IP_C_S1_1)

        self._setup_ip_forwarding(1)
        self._setup_ip_address(1, IP_C_S1_1)
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        port_id = self.ports[self.servers[1]['id']]['id']
        port_routes = [{'type': 'prefix',
                        'prefix': NET_C_S1}]
        body = self.bgpvpn_client.create_port_association(self.bgpvpn['id'],
                                                          port_id=port_id,
                                                          routes=port_routes)
        port_association = body['port_association']
        self._check_l3_bgpvpn_by_specific_ip(
            to_server_ip=IP_C_S1_1)
        self.bgpvpn_client.update_port_association(
            self.bgpvpn['id'], port_association['id'], routes=[])
        self._check_l3_bgpvpn_by_specific_ip(
            should_succeed=False, to_server_ip=IP_C_S1_1)

    @decorators.idempotent_id('d92a8a18-c4d0-40d5-8592-713d7dae7d25')
    @utils.services('compute', 'network')
    @utils.requires_ext(extension='bgpvpn-routes-control', service='network')
    @unstable_test("bug 1780205")
    def test_port_association_many_bgpvpn_routes(self):
        """This test checks port association in BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Create router and connect it to network A
        4. Create router and connect it to network B
        5. Start up server 1 in network A
        6. Start up server 2 in network B
        7. Give a FIP to all servers
        8. Configure ip forwarding on server 2
        9. Configure alternative loopback address on server 2
        10. Associate network A to a given L3 BGPVPN
        11. Associate port of server 2 to a given L3 BGPVPN
        12. Check that server 1 can ping server's 2 alternative ip
        13. Update created before port association by routes removal
        14. Check that server 1 cannot ping server's 2 alternative ip
        """
        AMOUNT_LOOPBACKS = 90
        START_IP_LOOPBACKS = 31
        SAMPLE_SIZE = 10
        LOOPBACKS = [str(ip) for ip in
                     S1C[START_IP_LOOPBACKS:
                     START_IP_LOOPBACKS + AMOUNT_LOOPBACKS]]
        SUB_LOOPBACKS = [LOOPBACKS[0], LOOPBACKS[-1]]

        self._create_networks_and_subnets(port_security=False)
        self._create_l3_bgpvpn()
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                              [self.networks[NET_B], IP_B_S1_1]],
                             port_security=False)
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_B][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)

        for ip in SUB_LOOPBACKS:
            LOG.debug("Preliminary check that no connectivity exist")
            self._check_l3_bgpvpn_by_specific_ip(
                should_succeed=False, to_server_ip=ip)

        self._setup_ip_forwarding(1)

        self._setup_range_ip_address(1, LOOPBACKS)

        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        port_id = self.ports[self.servers[1]['id']]['id']
        port_routes = [{'type': 'prefix',
                        'prefix': ip + "/32"}
                       for ip in LOOPBACKS]

        body = self.bgpvpn_client.create_port_association(self.bgpvpn['id'],
                                                          port_id=port_id,
                                                          routes=port_routes)
        port_association = body['port_association']

        for ip in random.sample(LOOPBACKS, SAMPLE_SIZE):
            LOG.debug("Check that server 1 can "
                      "ping server 2 alternative ip %s" % ip)
            self._check_l3_bgpvpn_by_specific_ip(
                to_server_ip=ip)

        self.bgpvpn_client.update_port_association(
            self.bgpvpn['id'], port_association['id'], routes=[])

        for ip in SUB_LOOPBACKS:
            LOG.debug("Check that server 1 can't "
                      "ping server 2 alternative ip %s" % ip)
            self._check_l3_bgpvpn_by_specific_ip(
                should_succeed=False, to_server_ip=ip)

    @decorators.idempotent_id('9c3280b5-0b32-4562-800c-0b50d9d52bfd')
    @utils.services('compute', 'network')
    @utils.requires_ext(extension='bgpvpn-routes-control', service='network')
    def test_bgpvpn_port_association_create_and_delete(self):
        """This test checks port association in BGPVPN.

        1. Create networks A and B with their respective subnets
        2. Create L3 BGPVPN
        3. Create router and connect it to network A
        4. Create router and connect it to network B
        5. Start up server 1 in network A
        6. Start up server 2 in network B
        7. Give a FIP to all servers
        8. Configure ip forwarding on server 2
        9. Configure alternative loopback address on server 2
        10. Associate network A to a given L3 BGPVPN
        11. Associate port of server 2 to a given L3 BGPVPN
        12. Check that server 1 can ping server's 2 alternative ip
        13. Remove created before port association
        14. Check that server 1 cannot ping server's 2 alternative ip
        """
        self._create_networks_and_subnets(port_security=False)
        self._create_l3_bgpvpn()
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                              [self.networks[NET_B], IP_B_S1_1]],
                             port_security=False)
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_B][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)

        # preliminary check that no connectivity to 192.168.0.1 initially
        # exists
        self._check_l3_bgpvpn_by_specific_ip(
            should_succeed=False, to_server_ip=IP_C_S1_1)

        self._setup_ip_forwarding(1)
        self._setup_ip_address(1, IP_C_S1_1)
        self.bgpvpn_client.create_network_association(
            self.bgpvpn['id'], self.networks[NET_A]['id'])
        port_id = self.ports[self.servers[1]['id']]['id']
        port_routes = [{'type': 'prefix',
                        'prefix': NET_C_S1}]
        body = self.bgpvpn_client.create_port_association(self.bgpvpn['id'],
                                                          port_id=port_id,
                                                          routes=port_routes)
        port_association = body['port_association']
        self._check_l3_bgpvpn_by_specific_ip(
            to_server_ip=IP_C_S1_1)
        self.bgpvpn_client.delete_port_association(
            self.bgpvpn['id'], port_association['id'])
        self._check_l3_bgpvpn_by_specific_ip(
            should_succeed=False, to_server_ip=IP_C_S1_1)

    @decorators.idempotent_id('73f629fa-fdae-40fc-8a7e-da3aedcf797a')
    @utils.services('compute', 'network')
    @utils.requires_ext(extension='bgpvpn-routes-control', service='network')
    def test_bgpvpn_port_association_bgpvpn_route(self):
        """Test port association routes of type 'bgpvpn'

        In this test we use a Port Association with a 'bgpvpn' route
        to have VM 1 in network A, reach a VM 3 in network C via the Port
        of a VM 2 (on network B), and vice-versa. For A->C traffic, one Port
        Association associates the port of VM 2 to a BGPVPN, with a route of
        type 'bgpvpn' redistributing routes from network  C. For C->A traffic,
        another Port Association associates the port of VM 2 to a BGPVPN, with
        a route of type 'bgpvpn' redistributing routes from network A.

        The use of RT in this test is a bit complex, and would be much
        simpler if we were using a VM with two interfaces.

        We confirm that VM 1 can join VM 3, and we confirm that the traffic
        actually goes through VM 2, by turning ip_forwaring off then on in VM2.
        """
        # create networks A, B and C with their respective subnets
        self._create_networks_and_subnets(port_security=False)

        RT_to_A = self.RT1
        RT_from_A = self.RT2
        RT_to_C = self.RT3
        RT_from_C = self.RT4

        # Create L3 BGPVPN for network A
        bgpvpn_a = self._create_l3_bgpvpn(name="test-vpn-a",
                                          import_rts=[RT_to_A],
                                          export_rts=[RT_from_A])

        # Create L3 BGPVPN for network C
        bgpvpn_c = self._create_l3_bgpvpn(name="test-vpn-c",
                                          import_rts=[RT_to_C],
                                          export_rts=[RT_from_C])

        # Create L3 BGPVPN for network B
        bgpvpn_b = self._create_l3_bgpvpn(name="test-vpn-b",
                                          import_rts=[RT_from_C, RT_from_A])

        # BGPVPNs to only export into A and C
        bgpvpn_to_a = self._create_l3_bgpvpn(name="test-vpn-to-a",
                                             export_rts=[RT_to_A])
        bgpvpn_to_c = self._create_l3_bgpvpn(name="test-vpn-to-c",
                                             export_rts=[RT_to_C])

        # create the three VMs
        self._create_servers([[self.networks[NET_A], IP_A_S1_1],
                              [self.networks[NET_B], IP_B_S1_1],
                              [self.networks[NET_C], IP_C_S1_1]],
                             port_security=False)
        vm1, vm2, vm3 = self.servers

        # Create one router for each of network A, B, C and give floating
        # IPs to servers 1, 2, 3
        self._create_fip_router(subnet_id=self.subnets[NET_A][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_B][0]['id'])
        self._create_fip_router(subnet_id=self.subnets[NET_C][0]['id'])
        self._associate_fip(0)
        self._associate_fip(1)
        self._associate_fip(2)

        # disable IP forwarding on VM2
        self._setup_ip_forwarding(0)

        # connect network A to its BGPVPN
        self.bgpvpn_client.create_network_association(
            bgpvpn_a['id'], self.networks[NET_A]['id'])

        # connect network B to its BGPVPN
        self.bgpvpn_client.create_network_association(
            bgpvpn_b['id'], self.networks[NET_B]['id'])

        # connect network C to its BGPVPN
        self.bgpvpn_client.create_network_association(
            bgpvpn_c['id'], self.networks[NET_C]['id'])

        # create port associations for A->C traffic
        # (leak routes imported by BGPVPN B -- which happen to include the
        # routes net C -- into net A)
        self.bgpvpn_client.create_port_association(
            bgpvpn_to_a['id'],
            port_id=self.ports[vm2['id']]['id'],
            routes=[{'type': 'bgpvpn',
                     'bgpvpn_id': bgpvpn_b['id']},
                    ])

        # create port associations for C->A traffic
        # (leak routes imported by BGPVPN B -- which happen to include the
        # routes from net A -- into net C)
        body = self.bgpvpn_client.create_port_association(
            bgpvpn_to_c['id'],
            port_id=self.ports[vm2['id']]['id'],
            routes=[{'type': 'bgpvpn',
                     'bgpvpn_id': bgpvpn_a['id']}])

        port_association = body['port_association']

        # check that we don't have connectivity
        # (because destination is supposed to be reachable via VM2, which
        # still has ip_forwarding disabled)
        self._check_l3_bgpvpn_by_specific_ip(from_server=vm1,
                                             to_server_ip=IP_C_S1_1,
                                             should_succeed=False)

        # enable IP forwarding on VM2
        self._setup_ip_forwarding(1)

        # VM1 should now be able to join VM2
        self._check_l3_bgpvpn_by_specific_ip(from_server=vm1,
                                             to_server_ip=IP_C_S1_1,
                                             should_succeed=True)

        # remove port association 1
        self.bgpvpn_client.delete_port_association(self.bgpvpn['id'],
                                                   port_association['id'])

        # check that connectivity is actually interrupted
        self._check_l3_bgpvpn_by_specific_ip(from_server=vm1,
                                             to_server_ip=IP_C_S1_1,
                                             should_succeed=False)

    @decorators.idempotent_id('8478074e-22df-4234-b02b-61257b475b18')
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

    @decorators.idempotent_id('b6d219b2-90bb-431f-a566-bf6a780d1578')
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
        self._create_l3_bgpvpn(rts=[], import_rts=[self.RT1],
                               export_rts=[self.RT2])
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn(should_succeed=False)

    @decorators.idempotent_id('dc92643f-1b2c-4a3e-bc5e-ea780d721ef7')
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

    @decorators.idempotent_id('2e6bf893-1410-4ef6-9948-1877f3a8f3d1')
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

    @decorators.idempotent_id('9ebf4342-4448-4d63-98f9-44d3a606b6cf')
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

    @decorators.idempotent_id('be4471b3-5f57-4022-b719-b45a673a728b')
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
        self._create_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._create_servers()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[self.RT1],
                               export_rts=[self.RT2])
        self._check_l3_bgpvpn(should_succeed=False)

    @decorators.idempotent_id('fb37a546-7263-4ffe-a42c-77eca377ff1a')
    @utils.services('compute', 'network')
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
        self._create_l3_bgpvpn(rts=[self.RT1], import_rts=[], export_rts=[])
        self._create_servers()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()
        self._update_l3_bgpvpn(rts=[], import_rts=[], export_rts=[])
        self._check_l3_bgpvpn(should_succeed=False)

    def _create_security_group_for_test(self):
        self.security_group = self._create_security_group(
            tenant_id=self.bgpvpn_client.tenant_id)

    def _create_networks_and_subnets(self, names=None, subnet_cidrs=None,
                                     port_security=True):
        if not names:
            names = [NET_A, NET_B, NET_C]
        if not subnet_cidrs:
            subnet_cidrs = [[NET_A_S1], [NET_B_S1], [NET_C_S1]]
        for (name, subnet_cidrs) in zip(names, subnet_cidrs):
            network = self._create_network(
                namestart=name, port_security_enabled=port_security)
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
                       security_group_ids, clients, port_security):
        security_groups = []
        if port_security:
            security_groups = security_group_ids
        create_port_body = {'fixed_ips': [{'ip_address': ip_address}],
                            'namestart': 'port-smoke',
                            'security_groups': security_groups}
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

    def _create_servers(self, ports_config=None, port_security=True):
        keypair = self.create_keypair()
        security_group_ids = [self.security_group['id']]
        if ports_config is None:
            ports_config = [[self.networks[NET_A], IP_A_S1_1],
                            [self.networks[NET_B], IP_B_S1_1]]
        for (i, port_config) in enumerate(ports_config):
            network = port_config[0]
            server = self._create_server(
                'server-' + str(i + 1), keypair, network, port_config[1],
                security_group_ids, self.os_primary, port_security)
            self.servers.append(server)
            self.servers_keypairs[server['id']] = keypair
            self.server_fixed_ips[server['id']] = (
                server['addresses'][network['name']][0]['addr'])
            self.assertTrue(self.servers_keypairs)

    def _create_l3_bgpvpn(self, name='test-l3-bgpvpn', rts=None,
                          import_rts=None, export_rts=None):
        if rts is None and import_rts is None and export_rts is None:
            rts = [self.RT1]
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
            rts = [self.RT1]
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
        ssh_client.exec_command("sudo nc -kl -p 80 -e echo '%s:%s' &"
                                % (server['name'], server['id']))

    def _setup_ip_forwarding(self, server_index):
        server = self.servers[server_index]
        ssh_client = self._setup_ssh_client(server)
        ssh_client.exec_command("sudo sysctl -w net.ipv4.ip_forward=1")

    def _setup_ip_address(self, server_index, cidr, device=None):
        self._setup_range_ip_address(server_index, [cidr], device=None)

    def _setup_range_ip_address(self, server_index, cidrs, device=None):
        MAX_CIDRS = 50
        if device is None:
            device = 'lo'
        server = self.servers[server_index]
        ssh_client = self._setup_ssh_client(server)
        for i in range(0, len(cidrs), MAX_CIDRS):
            ips = ' '.join(cidrs[i:i + MAX_CIDRS])
            ssh_client.exec_command(
                ("for ip in {ips}; do sudo ip addr add $ip "
                 "dev {dev}; done").format(ips=ips, dev=device))

    def _check_l3_bgpvpn(self, from_server=None, to_server=None,
                         should_succeed=True, validate_server=False):
        to_server = to_server or self.servers[1]
        destination_srv = None
        if validate_server:
            destination_srv = '%s:%s' % (to_server['name'], to_server['id'])
        destination_ip = self.server_fixed_ips[to_server['id']]
        self._check_l3_bgpvpn_by_specific_ip(from_server=from_server,
                                             to_server_ip=destination_ip,
                                             should_succeed=should_succeed,
                                             validate_server=destination_srv)

    def _check_l3_bgpvpn_by_specific_ip(self, from_server=None,
                                        to_server_ip=None,
                                        should_succeed=True,
                                        validate_server=None,
                                        repeat_validate_server=10):
        from_server = from_server or self.servers[0]
        from_server_ip = self.server_fips[from_server['id']][
            'floating_ip_address']
        if to_server_ip is None:
            to_server_ip = self.server_fixed_ips[self.servers[1]['id']]
        ssh_client = self._setup_ssh_client(from_server)
        check_reachable = should_succeed or validate_server
        msg = ""
        if check_reachable:
            msg = "Timed out waiting for {ip} to become reachable".format(
                ip=to_server_ip)
        else:
            msg = ("Unexpected ping response from VM with IP address "
                   "{dest} originated from VM with IP address "
                   "{src}").format(dest=to_server_ip, src=from_server_ip)
        try:
            result = self._check_remote_connectivity(ssh_client,
                                                     to_server_ip,
                                                     check_reachable)
            # if a negative connectivity check was unsuccessful (unexpected
            # ping reply) then try to know more:
            if not check_reachable and not result:
                try:
                    content = ssh_client.exec_command(
                        "nc %s 80" % to_server_ip).strip()
                    LOG.warning("Can connect to %s: %s", to_server_ip, content)
                except Exception:
                    LOG.warning("Could ping %s, but no http", to_server_ip)

            self.assertTrue(result, msg)

            if validate_server and result:
                # repeating multiple times gives increased odds of avoiding
                # false positives in the case where the dataplane does
                # equal-cost multipath
                for i in range(0, repeat_validate_server):
                    real_dest = ssh_client.exec_command(
                        "nc %s 80" % to_server_ip).strip()
                    result = real_dest == validate_server
                    self.assertTrue(
                        should_succeed == result,
                        ("Destination server name is '%s', expected is '%s'" %
                         (real_dest, validate_server)))
                    LOG.info("nc server name check %d successful", i)
        except Exception:
            LOG.exception(
                "Error validating connectivity to %s "
                "from VM with IP address %s: %s" % (to_server_ip,
                                                    from_server_ip,
                                                    msg))
            raise

    def _associate_fip_and_check_l3_bgpvpn(self, should_succeed=True):
        subnet = self.subnets[NET_A][0]
        self.router = self._create_router_and_associate_fip(0, subnet)
        self._check_l3_bgpvpn(should_succeed=should_succeed)
