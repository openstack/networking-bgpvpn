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

from unittest import mock

from openstack_dashboard.test import helpers

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.project.bgpvpn import forms as bgpvpn_form


class TestEditDataBgpVpn(helpers.APITestCase):

    def setUp(self):
        super(TestEditDataBgpVpn, self).setUp()
        self.mock_request = mock.MagicMock()
        self.bgpvpn_form = bgpvpn_form.EditDataBgpVpn(self.mock_request)
        self.bgpvpn_form.action = "update"

    @mock.patch.object(bgpvpn_form, 'bgpvpn_api')
    def test_handle(self, mock_bgpvpn_api):
        self.bgpvpn_form.request.user.is_superuser = False
        test_data = {"bgpvpn_id": "foo-id",
                     "name": "foo-name",
                     "type": "l3"}
        expected_data = bgpvpn_api.Bgpvpn({"id": "foo-id",
                                           "name": "foo-name",
                                           "type": "l3"})
        mock_bgpvpn_api.bgpvpn_update.return_value = expected_data
        result = self.bgpvpn_form.handle(self.mock_request, test_data)

        self.assertEqual(expected_data, result)
        mock_bgpvpn_api.bgpvpn_update.assert_called_once_with(
            self.mock_request, "foo-id", name="foo-name")
