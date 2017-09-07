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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest import test

from networking_bgpvpn_tempest.tests import base
from networking_bgpvpn_tempest.tests.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)
RT1 = '64512:1'
RT2 = '64512:2'


class TestBGPVPNBasic(base.BaseBgpvpnTest, manager.NetworkScenarioTest):
    def setUp(self):
        super(TestBGPVPNBasic, self).setUp()
        self.servers_keypairs = {}
        self.servers = []
        self.server_fixed_ips = {}
        self.ports = []
        self.networks = []
        self.subnets = []
        self.server_fips = {}
        self._create_security_group_for_test()

    @test.services('compute', 'network')
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

    @test.services('compute', 'network')
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

    @test.services('compute', 'network')
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
            subnet_id=self.subnets[1]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._associate_fip_and_check_l3_bgpvpn()

    @test.services('compute', 'network')
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
            subnet_id=self.subnets[1]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self.delete_router(self.router_b)
        self._associate_fip_and_check_l3_bgpvpn()

    @test.services('compute', 'network')
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
            subnet_id=self.subnets[1]['id'])
        self._associate_fip_and_check_l3_bgpvpn()

    @test.services('compute', 'network')
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
            subnet_id=self.subnets[1]['id'])
        self._create_l3_bgpvpn()
        self._associate_all_nets_to_bgpvpn()
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()

    @test.services('compute', 'network')
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
            subnet_id=self.subnets[1]['id'])
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn()

    @test.services('compute', 'network')
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
        self.bgpvpn_client.create_network_association(self.bgpvpn['id'],
                                                      self.networks[0]['id'])
        self._create_servers()
        self._associate_fip_and_check_l3_bgpvpn(should_succeed=False)

    @test.services('compute', 'network')
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

    def _create_security_group_for_test(self):
        self.security_group = self._create_security_group(
            tenant_id=self.bgpvpn_client.tenant_id)

    def _create_networks_and_subnets(self):
        name = ['A', 'B']
        ip_cidrs = ['10.100.1.0/24', '10.100.2.0/24']
        create_kwargs = {'ip_version': 4}
        for i in [0, 1]:
            network = self._create_network(namestart='network-' + name[i])
            self.networks.append(network)
            create_kwargs['cidr'] = ip_cidrs[i]
            self.subnets.append(self._create_subnet_with_cidr(
                network, namestart='subnet-' + name[i], **create_kwargs))

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

    def _create_router_and_associate_fip(self, server_index):
        server = self.servers[server_index]
        router = self._create_fip_router(
            subnet_id=self.subnets[server_index]['id'])
        self.server_fips[server['id']] = self.create_floating_ip(
            server, external_network_id=CONF.network.public_network_id,
            port_id=self.ports[server_index]['id'])
        return router

    def _create_server(self, name, keypair, network, ip_address,
                       security_group_ids, clients):
        create_port_body = {'fixed_ips': [{'ip_address': ip_address}],
                            'namestart': 'port-smoke',
                            'security_groups': security_group_ids}
        port = self._create_port(network_id=network['id'],
                                 client=clients.ports_client,
                                 **create_port_body)
        self.ports.append(port)
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
        return server

    def _create_servers(self):
        name = ['server-1', 'server-2']
        keypair = self.create_keypair()
        security_group_ids = [self.security_group['id']]
        port_ips = ['10.100.1.10', '10.100.2.20']
        for i in [0, 1]:
            network = self.networks[i]
            server = self._create_server(
                name[i], keypair, network, port_ips[i], security_group_ids,
                self.os_primary)
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
        for network in self.networks:
            self.bgpvpn_client.create_network_association(bgpvpn['id'],
                                                          network['id'])
        LOG.debug('BGPVPN network associations completed')

    def _check_l3_bgpvpn(self, from_server=None, to_server=None,
                         should_succeed=True):
        from_server = from_server or self.servers[0]
        to_server = to_server or self.servers[1]
        server_1_ip = self.server_fips[from_server['id']][
            'floating_ip_address']
        server_2_ip = self.server_fixed_ips[to_server['id']]
        private_key = self.servers_keypairs[from_server['id']][
            'private_key']
        ssh_client = self.get_remote_client(server_1_ip,
                                            private_key=private_key)
        try:
            msg = ""
            if should_succeed:
                msg = "Timed out waiting for {ip} to become reachable".format(
                    ip=server_2_ip)
            else:
                msg = ("Unexpected ping response from VM with IP address "
                       "{dest} originated from VM with IP address "
                       "{src}").format(dest=server_2_ip, src=server_1_ip)
            self.assertTrue(
                self._check_remote_connectivity(ssh_client, server_2_ip,
                                                should_succeed),
                msg)
        except Exception:
            LOG.exception(("Unable to ping VM with IP address {dest} from VM "
                           "with IP address {src}").format(dest=server_2_ip,
                                                           src=server_1_ip))
            raise

    def _associate_fip_and_check_l3_bgpvpn(self, should_succeed=True):
        self.router = self._create_router_and_associate_fip(0)
        self._check_l3_bgpvpn(should_succeed=should_succeed)
