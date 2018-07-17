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

import mock

from django.urls import reverse
from django.urls import reverse_lazy

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.project.bgpvpn import forms as bgpvpn_form
from bgpvpn_dashboard.dashboards.project.bgpvpn import tables as bgpvpn_tables
from bgpvpn_dashboard.dashboards.project.bgpvpn import views as bgpvpn_views

from openstack_dashboard.test import helpers


class TestIndexView(helpers.APITestCase):

    def setUp(self):
        super(TestIndexView, self).setUp()
        mock_request = mock.Mock(horizon={'async_messages': []})
        self.bgpvpn_view = bgpvpn_views.IndexView(request=mock_request)
        self.bgpvpn_view._prev = False
        self.bgpvpn_view._more = False

        self.assertEqual(bgpvpn_tables.BgpvpnTable,
                         self.bgpvpn_view.table_class)
        self.assertEqual('project/bgpvpn/index.html',
                         self.bgpvpn_view.template_name)

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

    @mock.patch.object(bgpvpn_views, 'bgpvpn_api', autospec=True)
    def test_get_data(self, mock_bgpvpn_api):
        """Test that get_data works."""

        bgpvpn_foo = self._get_mock_bgpvpn("foo")
        bgpvpn_bar = self._get_mock_bgpvpn("bar")

        mock_bgpvpn_api.bgpvpns_list.return_value = [bgpvpn_bar, bgpvpn_foo]
        result = self.bgpvpn_view.get_data()
        expected_bgpvpns = [bgpvpn_bar, bgpvpn_foo]
        self.assertEqual(expected_bgpvpns, result)


class TestEditDataView(helpers.APITestCase):

    def setUp(self):
        super(TestEditDataView, self).setUp()
        mock_request = mock.Mock(horizon={'async_messages': []})
        self.bgpvpn_view = bgpvpn_views.EditDataView(request=mock_request)
        fake_response = {'status_code': 200}
        self.mock_request = mock.Mock(return_value=fake_response, META=[])
        self.bgpvpn_view.request = self.mock_request
        self.bgpvpn_view.kwargs = {'bgpvpn_id': 'foo-id'}

        self.assertEqual(bgpvpn_form.EditDataBgpVpn,
                         self.bgpvpn_view.form_class)
        self.assertEqual('horizon:project:bgpvpn:edit',
                         self.bgpvpn_view.submit_url)
        self.assertEqual(reverse_lazy('horizon:project:bgpvpn:index'),
                         self.bgpvpn_view.success_url)
        self.assertEqual('project/bgpvpn/modify.html',
                         self.bgpvpn_view.template_name)

    @mock.patch.object(bgpvpn_views, 'bgpvpn_api', autospec=True)
    def test_get_initial_user(self, mock_bgpvpn_api):
        self.bgpvpn_view.request.user.is_superuser = False
        bgpvpn_data = {"name": "foo-name",
                       "id": "foo-id",
                       "type": "l3"}
        expected_data = {"name": "foo-name",
                         "bgpvpn_id": "foo-id",
                         "type": "l3"}
        mock_bgpvpn_api.bgpvpn_get.return_value = bgpvpn_api.Bgpvpn(
            bgpvpn_data)
        result = self.bgpvpn_view.get_initial()

        mock_bgpvpn_api.bgpvpn_get.assert_called_once_with(
            self.bgpvpn_view.request, "foo-id")
        for key, val in expected_data.items():
            self.assertEqual(val, result[key])

    @mock.patch.object(bgpvpn_views, 'bgpvpn_api', autospec=True)
    def test_get_initial_admin(self, mock_bgpvpn_api):
        self.bgpvpn_view.request.user.is_superuser = True
        bgpvpn_data = {"name": "foo-name",
                       "id": "foo-id",
                       "type": "l3",
                       "route_targets": ["65432:1", "65432:2"],
                       "import_targets": [],
                       "export_targets": []}
        expected_data = {"name": "foo-name",
                         "bgpvpn_id": "foo-id",
                         "type": "l3",
                         "route_targets": "65432:1,65432:2",
                         "import_targets": "",
                         "export_targets": ""}
        mock_bgpvpn_api.bgpvpn_get.return_value = bgpvpn_api.Bgpvpn(
            bgpvpn_data)
        result = self.bgpvpn_view.get_initial()

        mock_bgpvpn_api.bgpvpn_get.assert_called_once_with(
            self.bgpvpn_view.request, "foo-id")
        for key, val in expected_data.items():
            self.assertEqual(val, result[key])

    def test_get_context_data(self):
        mock_form = mock.Mock()
        args = ("foo-id",)
        expected_context = {
            'bgpvpn_id': 'foo-id',
            'submit_url': reverse("horizon:project:bgpvpn:edit", args=args)}
        context = self.bgpvpn_view.get_context_data(form=mock_form)
        self.assertIn('view', context)
        self.assertIsInstance(context['view'], bgpvpn_views.EditDataView)

        for key, val in expected_context.items():
            self.assertIn(key, context)

            self.assertEqual(val, context[key])

    def test_join_rts(self):
        route_targets_list = ["65400:1", "65401:1"]
        expected_result = "65400:1,65401:1"
        result = self.bgpvpn_view._join_rts(route_targets_list)
        self.assertEqual(expected_result, result)
