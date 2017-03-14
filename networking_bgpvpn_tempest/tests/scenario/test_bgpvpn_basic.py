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


class TestBGPVPNBasic(base.BaseBgpvpnTest, manager.NetworkScenarioTest):
    def setUp(self):
        super(TestBGPVPNBasic, self).setUp()
        self.servers_keypairs = {}
        self.servers = []
        self.server_fixed_ips = {}
        self.ports = []
        self._create_security_group_for_test()

    @test.services('compute', 'network')
    def test_bgpvpn_basic(self):
        """This test check basic BGPVPN.

        1. Create networks A and B with their respective subnets
        1. Start up server 1 in network A
        2. Start up server 2 in network B
        3. Associate network A and network B to a given L3 BGPVPN
        4. Check that server 1 can ping server 2
        """
        self._create_networks_and_subnets()
        self._create_servers()
        self._create_l3_bgpvpn()
        self.router = self._create_fip_router(
            subnet_id=self.subnets[0]['id'])
        self.fip = self.create_floating_ip(
            self.servers[0],
            external_network_id=CONF.network.public_network_id,
            port_id=self.ports[0]['id'])
        src_ip = self.fip['floating_ip_address']
        dst_ip = self.server_fixed_ips[self.servers[1]['id']]
        self._check_l3_bgpvpn(src_ip, dst_ip)

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
                self.manager)
            self.servers.append(server)
            self.servers_keypairs[server['id']] = keypair
            self.server_fixed_ips[server['id']] = (
                server['addresses'][network['name']][0]['addr'])
            self.assertTrue(self.servers_keypairs)

    def _create_l3_bgpvpn(self):
        self.bgpvpn = self.create_bgpvpn(
            self.bgpvpn_admin_client, tenant_id=self.bgpvpn_client.tenant_id,
            name='l3bgpvpn', route_targets=['64512:1'])
        for network in self.networks:
            LOG.debug('Associating network %s to BGPVPN %s', network['id'],
                      self.bgpvpn['id'])
            self.bgpvpn_client.create_network_association(self.bgpvpn['id'],
                                                          network['id'])
        LOG.debug('BGPVPN network associations completed')

    def _check_l3_bgpvpn(self, server_1_ip, server_2_ip):
        private_key = self.servers_keypairs[self.servers[0]['id']][
            'private_key']
        ssh_client = self.get_remote_client(server_1_ip,
                                            private_key=private_key)
        try:
            msg = "Timed out waiting for %s to become reachable" % server_2_ip
            self.assertTrue(
                self._check_remote_connectivity(ssh_client, server_2_ip, True),
                msg)
        except Exception:
            LOG.exception("Unable to ping VM with IP address {dest} from VM "
                          "with IP address {src}".format(dest=server_2_ip,
                                                         src=server_1_ip))
            raise
