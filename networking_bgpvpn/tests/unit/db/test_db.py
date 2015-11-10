# Copyright (c) 2015 Orange.
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

from neutron import context

from networking_bgpvpn.neutron.db.bgpvpn_db import BGPVPNNetAssocNotFound
from networking_bgpvpn.neutron.db.bgpvpn_db import BGPVPNNotFound
from networking_bgpvpn.neutron.db.bgpvpn_db import BGPVPNPluginDb
from networking_bgpvpn.tests.unit.services import test_plugin


class BgpvpnDBTestCase(test_plugin.BgpvpnTestCaseMixin):

    def setUp(self):
        super(BgpvpnDBTestCase, self).setUp()
        self.ctx = context.get_admin_context()
        self.plugin_db = BGPVPNPluginDb()

    def test_bgpvpn_create_update_delete(self):
        with self.network() as net:
            # create
            bgpvpn = self.plugin_db.create_bgpvpn(
                self.ctx,
                {"bgpvpn": {
                    "type": "l3",
                    "name": "",
                    "route_targets": ["64512:1"],
                    "import_targets": ["64512:11", "64512:12"],
                    "export_targets": ["64512:13", "64512:14"],
                    "route_distinguishers": ["64512:15", "64512:16"],
                    "auto_aggregate": False
                }}
            )

            # associate network
            assoc1 = self.plugin_db.create_net_assoc(self.ctx, bgpvpn['id'],
                                                     net['network']['id'])

            # retrieve
            bgpvpn = self.plugin_db.get_bgpvpn(self.ctx, bgpvpn['id'])

            # check
            self.assertEqual("l3", bgpvpn['type'])
            # we could check tenant_id
            self.assertEqual(["64512:1"], bgpvpn['route_targets'])
            self.assertEqual(["64512:11", "64512:12"],
                             bgpvpn['import_targets'])
            self.assertEqual(["64512:13", "64512:14"],
                             bgpvpn['export_targets'])
            self.assertEqual(False, bgpvpn['auto_aggregate'])
            self.assertEqual(["64512:15", "64512:16"],
                             bgpvpn['route_distinguishers'])
            self.assertEqual([net['network']['id']], bgpvpn['networks'])

            assoc1 = self.plugin_db.get_net_assoc(self.ctx, assoc1['id'],
                                                  bgpvpn['id'])
            self.assertEqual(net['network']['id'], assoc1['network_id'])
            self.assertEqual(bgpvpn['id'], assoc1['bgpvpn_id'])

            with self.network(name='net2') as net2:
                # associate network
                assoc2 = self.plugin_db.create_net_assoc(self.ctx,
                                                         bgpvpn['id'],
                                                         net2['network']['id'])
                # retrieve
                assoc2 = self.plugin_db.get_net_assoc(self.ctx, assoc2['id'],
                                                      bgpvpn['id'])
                assoc_list = self.plugin_db.get_net_assocs(self.ctx,
                                                           bgpvpn['id'])
                self.assertIn(assoc2, assoc_list)
                self.assertIn(assoc1, assoc_list)

            # update
            self.plugin_db.update_bgpvpn(
                self.ctx,
                bgpvpn['id'],
                {"bgpvpn": {
                    "type": "l2",
                    "name": "foo",
                    "tenant_id": "a-b-c-d",
                    "route_targets": [],
                    "import_targets": ["64512:22"],
                    "route_distinguishers": [],
                    "auto_aggregate": True
                }})

            # retrieve
            bgpvpn2 = self.plugin_db.get_bgpvpn(self.ctx, bgpvpn['id'])
            # check
            self.assertEqual("l2", bgpvpn2['type'])
            self.assertEqual("a-b-c-d", bgpvpn2['tenant_id'])
            self.assertEqual("foo", bgpvpn2['name'])
            self.assertEqual([], bgpvpn2['route_targets'])
            self.assertEqual(["64512:22"], bgpvpn2['import_targets'])
            self.assertEqual(["64512:13", "64512:14"],
                             bgpvpn2['export_targets'])
            self.assertEqual([], bgpvpn2['route_distinguishers'])
            self.assertEqual(True, bgpvpn2['auto_aggregate'])

            # find bgpvpn by network_id
            bgpvpn3 = self.plugin_db.find_bgpvpns_for_network(
                self.ctx,
                net['network']['id']
                )
            self.assertEqual(1, len(bgpvpn3))
            self.assertEqual(bgpvpn2['id'], bgpvpn3[0]['id'])

            # asset that GETting the assoc, but for another BGPVPN, does fails
            self.assertRaises(BGPVPNNetAssocNotFound,
                              self.plugin_db.get_net_assoc,
                              self.ctx,
                              assoc2['id'],
                              "bogus_bgpvpn_id")

            # assert that deleting a net remove the assoc
            self._delete('networks', net2['network']['id'])
            assoc_list = self.plugin_db.get_net_assocs(self.ctx,
                                                       bgpvpn['id'])
            self.assertNotIn(assoc2, assoc_list)
            self.assertRaises(BGPVPNNetAssocNotFound,
                              self.plugin_db.get_net_assoc,
                              self.ctx,
                              assoc2['id'], bgpvpn['id'])
            # delete
            self.plugin_db.delete_bgpvpn(self.ctx, bgpvpn['id'])
            # check that delete was effective
            self.assertRaises(BGPVPNNotFound,
                              self.plugin_db.get_bgpvpn,
                              self.ctx, bgpvpn['id'])
            # check that the assoc has been deleted after deleting the bgpvpn
            self.assertRaises(BGPVPNNetAssocNotFound,
                              self.plugin_db.get_net_assoc,
                              self.ctx,
                              assoc1['id'], bgpvpn['id'])

    def test_db_associate_disassociate_net(self):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                with self.assoc_net(id, net_id):
                    bgpvpn = self.plugin_db.get_bgpvpn(self.ctx, id)
                    self.assertEqual([net_id], bgpvpn['networks'])
                bgpvpn = self.plugin_db.get_bgpvpn(self.ctx, id)
                self.assertEqual([], bgpvpn['networks'])

    def test_db_find_bgpvpn_for_net(self):
        with self.network() as net:
            net_id = net['network']['id']
            with self.bgpvpn() as bgpvpn:
                id = bgpvpn['bgpvpn']['id']
                with self.assoc_net(id, net_id=net_id):
                    bgpvpn_list = self.plugin_db.\
                        find_bgpvpns_for_network(self.ctx, net_id)
                    self.assertEqual(id, bgpvpn_list[0]['id'])

    def test_db_delete_net(self):
        with self.bgpvpn() as bgpvpn:
            id = bgpvpn['bgpvpn']['id']
            with self.network() as net:
                net_id = net['network']['id']
                self.assoc_net(id, net_id=net_id, do_disassociate=False)
            bgpvpn_db = self.plugin_db.get_bgpvpn(self.ctx, id)
            self.assertEqual([], bgpvpn_db['networks'])

#     def test_db_get_assoc_list(self):
#         with self.bgpvpn() as bgpvpn:
#             bgpvpn_id = bgpvpn['bgpvpn']['id']
#             net1 = self.network()
#             net1_id = net1['network']['id']
#             net2 = self.network(name='net2')
#             net2_id = net2['network']['id']
#             with self.assoc_net(bgpvpn_id, net1_id) as assoc1:
#                 assoc1_id = assoc1['network_association']['id']
#                 with self.assoc_net(bgpvpn_id, net2_id) as assoc2:
#                     assoc2_id = assoc2['network_association']['id']
#                     bgpvpns_list = self.plugin_db.get_bgpvpns(self.ctx)
#                     expected_res = [{'id': assoc1_id,
#                                      'network_id': net1_id,
#                                      'bgpvpn_id': bgpvpn_id},
#                                     {'id': assoc2_id,
#                                      'network_id': net2_id,
#                                      'bgpvpn_id': bgpvpn_id}]
#                     self.assertEqual(expected_res, bgpvpns_list)
