# Copyright (c) 2017 Orange.
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

import mock

from openstack_dashboard.test import helpers

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.admin.bgpvpn import forms as bgpvpn_a_form
from bgpvpn_dashboard.dashboards.project.bgpvpn import forms as bgpvpn_p_form


class Tenant(object):
    def __init__(self, id, name, enabled):
        self.id = id
        self.name = name
        self.enabled = enabled


class TestCreateDataBgpVpn(helpers.APITestCase):

    @mock.patch.object(bgpvpn_a_form, 'api')
    def setUp(self, mock_api):
        super(TestCreateDataBgpVpn, self).setUp()
        self.mock_request = mock.MagicMock()

    @mock.patch.object(bgpvpn_p_form, 'bgpvpn_api')
    @mock.patch.object(bgpvpn_a_form, 'api')
    def test_invalid_rt(self, mock_api, mock_bgpvpn_api):
        mock_api.keystone.tenant_list.return_value = [], False
        mock_bgpvpn_api.list_bgpvpns.return_value = []
        data = {"route_targets": "xyz",
                "import_targets": "0",
                "export_targets": "64512:1000000000000, xyz"}
        self.bgpvpn_form = bgpvpn_a_form.CreateBgpVpn(self.mock_request, data)

        self.assertTrue(self.bgpvpn_form.has_error("route_targets"))
        self.assertTrue(self.bgpvpn_form.has_error("import_targets"))
        self.assertTrue(self.bgpvpn_form.has_error("export_targets"))

    @mock.patch.object(bgpvpn_p_form, 'bgpvpn_api')
    @mock.patch.object(bgpvpn_a_form, 'api')
    def test_valid_rt(self, mock_api, mock_bgpvpn_api):
        mock_api.keystone.tenant_list.return_value = [], False
        mock_bgpvpn_api.list_bgpvpns.return_value = []
        data = {"route_targets": "65421:1",
                "import_targets": "65421:1, 65421:2",
                "export_targets": "65421:3"}
        self.bgpvpn_form = bgpvpn_a_form.CreateBgpVpn(self.mock_request, data)

        self.assertFalse(self.bgpvpn_form.has_error("route_targets"))
        self.assertFalse(self.bgpvpn_form.has_error("import_targets"))
        self.assertFalse(self.bgpvpn_form.has_error("export_targets"))

    @mock.patch.object(bgpvpn_p_form, 'bgpvpn_api')
    @mock.patch.object(bgpvpn_a_form, 'api')
    def test_handle_update(self, mock_api, mock_bgpvpn_api):
        data = {"bgpvpn_id": "foo-id",
                "type": "l3",
                "name": "foo-name",
                "route_targets": "65421:1",
                "import_targets": "65421:2",
                "export_targets": "65421:3"}
        mock_api.keystone.tenant_list.return_value = [], False
        self.bgpvpn_form = bgpvpn_a_form.CreateBgpVpn(self.mock_request)
        self.bgpvpn_form.action = "update"
        expected_data = bgpvpn_api.Bgpvpn({"bgpvpn_id": "foo-id",
                                           "name": "foo-name",
                                           "tenant_id": "tenant_id",
                                           "route_targets": ["65421:1"],
                                           "import_targets": ["65421:2"],
                                           "export_targets": ["65421:3"]})
        mock_bgpvpn_api.bgpvpn_update.return_value = expected_data

        result = self.bgpvpn_form.handle(self.mock_request, data)

        mock_bgpvpn_api.bgpvpn_update.assert_called_once_with(
            self.mock_request, "foo-id",
            name="foo-name",
            route_targets=["65421:1"],
            import_targets=["65421:2"],
            export_targets=["65421:3"])
        self.assertEqual(result, expected_data)
