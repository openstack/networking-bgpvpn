# Copyright (c) 2017 Orange.
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

from unittest import mock

from collections import namedtuple

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.admin.bgpvpn import tables as bgpvpn_tables
from bgpvpn_dashboard.dashboards.admin.bgpvpn import views as bgpvpn_views

from openstack_dashboard.test import helpers

VIEWS = "bgpvpn_dashboard.dashboards.admin.bgpvpn.views"


class TestIndexView(helpers.APITestCase):

    def setUp(self):
        super(TestIndexView, self).setUp()
        mock_request = mock.Mock(horizon={'async_messages': []})
        self.bgpvpn_view = bgpvpn_views.IndexView(request=mock_request)
        self.assertEqual(bgpvpn_tables.BgpvpnTable,
                         self.bgpvpn_view.table_class)

    def _get_mock_bgpvpn(self, prefix):
        bgpvpn_info = {}
        if prefix:
            bgpvpn_info = {
                "name": "%s_name" % prefix,
                "route_targets": [],
                "import_targets": [],
                "export_targets": [],
                "networks": [],
                "routers": [],
                "tenant_id": "tenant_id",
                "type": "l3"
            }
        return bgpvpn_api.Bgpvpn(bgpvpn_info)

    @mock.patch.object(bgpvpn_views.api, 'keystone', autospec=True)
    def test_get_tenant_name(self, mock_api):
        Tenant = namedtuple("Tenant", ["id", "name"])
        tenant = Tenant("tenant_id", "tenant_name")

        mock_api.tenant_get.return_value = tenant
        result = self.bgpvpn_view._get_tenant_name("tenant_id")

        mock_api.tenant_get.assert_called_once_with(
            self.bgpvpn_view.request, "tenant_id")
        self.assertEqual(result, "tenant_name")

    @mock.patch('%s.IndexView._get_tenant_name' % VIEWS,
                return_value={"tenant_id": "tenant_name"})
    @mock.patch.object(bgpvpn_views, 'api', autospec=True)
    @mock.patch.object(bgpvpn_views, 'bgpvpn_api', autospec=True)
    def test_get_data(self, mock_bgpvpn_api, mock_api, mock_get_tenant_name):
        bgpvpn_foo = self._get_mock_bgpvpn("foo")
        bgpvpn_bar = self._get_mock_bgpvpn("bar")
        mock_neutron_client = mock_api.neutron.neutronclient(mock.Mock())
        mock_bgpvpn_api.bgpvpns_list.return_value = [bgpvpn_foo, bgpvpn_bar]
        mock_neutron_client.list_networks.return_value = []
        mock_neutron_client.list_routers.return_value = []

        expected_bgpvpns = [bgpvpn_foo, bgpvpn_bar]
        result = self.bgpvpn_view.get_data()

        calls = [mock.call("tenant_id"), mock.call("tenant_id")]
        mock_get_tenant_name.assert_has_calls(calls)
        self.assertEqual(result, expected_bgpvpns)
