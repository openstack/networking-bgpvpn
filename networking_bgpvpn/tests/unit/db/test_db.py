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

from neutron.tests.unit import testlib_api

from networking_bgpvpn.neutron.db.bgpvpn.bgpvpn_db \
    import BGPVPNConnectionNotFound
from networking_bgpvpn.neutron.db.bgpvpn.bgpvpn_db import BGPVPNPluginDb


class BGPVPNDBTestCase(testlib_api.SqlTestCase):

    def setUp(self):
        super(BGPVPNDBTestCase, self).setUp()
        self.ctx = context.get_admin_context()
        self.plugin_db = BGPVPNPluginDb()

    def test_bgpvpnconnection_create_delete(self):
        with self.ctx.session.begin(subtransactions=True):

            # create
            bgpvpncnx = self.plugin_db.create_bgpvpn_connection(
                self.ctx,
                {"bgpvpn_connection": {
                    "type": "l3",
                    "name": "",
                    "network_id": None,
                    "route_targets": ["64512:1"],
                    "import_targets": ["64512:11", "64512:12"],
                    "export_targets": ["64512:13", "64512:14"],
                    "auto_aggregate": False
                }}
            )

            # retrieve
            bgpvpncnx = self.plugin_db.get_bgpvpn_connection(self.ctx,
                                                             bgpvpncnx['id'])

            # check
            self.assertEqual("l3", bgpvpncnx['type'])
            # we could check tenant_id
            self.assertEqual(["64512:1"], bgpvpncnx['route_targets'])
            self.assertEqual(["64512:11", "64512:12"],
                             bgpvpncnx['import_targets'])
            self.assertEqual(["64512:13", "64512:14"],
                             bgpvpncnx['export_targets'])
            self.assertEqual(False, bgpvpncnx['auto_aggregate'])

            # update
            self.plugin_db.update_bgpvpn_connection(
                self.ctx,
                bgpvpncnx['id'],
                {"bgpvpn_connection": {
                    "type": "l2",
                    "name": "foo",
                    "tenant_id": "a-b-c-d",
                    "network_id": "1-2-3-4",
                    "route_targets": [],
                    "import_targets": ["64512:22"],
                    "auto_aggregate": True
                }})

            # retrieve
            bgpvpncnx2 = self.plugin_db.get_bgpvpn_connection(self.ctx,
                                                              bgpvpncnx['id'])
            # check
            self.assertEqual("l2", bgpvpncnx2['type'])
            self.assertEqual("a-b-c-d", bgpvpncnx2['tenant_id'])
            self.assertEqual("1-2-3-4", bgpvpncnx2['network_id'])
            self.assertEqual("foo", bgpvpncnx2['name'])
            self.assertEqual([], bgpvpncnx2['route_targets'])
            self.assertEqual(["64512:22"], bgpvpncnx2['import_targets'])
            self.assertEqual(["64512:13", "64512:14"],
                             bgpvpncnx2['export_targets'])
            self.assertEqual(True, bgpvpncnx2['auto_aggregate'])

            # find bgpvpn by network_id
            bgpvpncnx3 = self.plugin_db.find_bgpvpn_connections_for_network(
                self.ctx,
                "1-2-3-4"
                )
            self.assertEqual(1, len(bgpvpncnx3))
            self.assertEqual(bgpvpncnx2['id'], bgpvpncnx3[0]['id'])

            # delete
            self.plugin_db.delete_bgpvpn_connection(self.ctx, bgpvpncnx['id'])
            # check that delete was effective
            self.assertRaises(BGPVPNConnectionNotFound,
                              self.plugin_db.get_bgpvpn_connection,
                              self.ctx, bgpvpncnx['id'])
