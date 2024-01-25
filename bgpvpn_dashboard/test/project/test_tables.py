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

from django import test
from django.utils.translation import gettext_lazy as _

from bgpvpn_dashboard.dashboards.project.bgpvpn import tables as bgpvpn_tables


class TestFunctionGet(test.TestCase):

    @mock.patch.object(bgpvpn_tables, 'reverse')
    def test_get_network_url(self, mock_reverse):
        mock_reverse.return_value = 'foo_reverse_url'
        mock_network = mock.Mock(id='foo-id', name_or_id="foo")
        result = bgpvpn_tables.get_network_url(mock_network)
        mock_reverse.assert_called_once_with(
            'horizon:project:networks:detail', args=['foo-id'])
        self.assertEqual('<a href=foo_reverse_url>foo</a>', result)

    @mock.patch.object(bgpvpn_tables, 'reverse')
    def test_get_router_url(self, mock_reverse):
        mock_reverse.return_value = 'foo_reverse_url'
        mock_network = mock.Mock(id='foo-id', name_or_id="foo")
        result = bgpvpn_tables.get_router_url(mock_network)
        mock_reverse.assert_called_once_with(
            'horizon:project:routers:detail', args=['foo-id'])
        self.assertEqual('<a href=foo_reverse_url>foo</a>', result)


class TestNetworksColumn(test.TestCase):

    def setUp(self):
        super(TestNetworksColumn, self).setUp()
        self.nets_column = bgpvpn_tables.NetworksColumn(
            "networks", verbose_name=_("Networks"))

    def test_get_raw_data(self):
        result_expected = "<a href=/project/networks/id1/detail>foo1</a>, " \
                          "<a href=/project/networks/id2/detail>foo2</a>"
        mock_net1 = mock.Mock(id="id1", name_or_id="foo1")
        mock_net2 = mock.Mock(id="id2", name_or_id="foo2")
        networks = [mock_net1, mock_net2]
        mock_bgpvpn = mock.Mock(networks=networks)
        result = self.nets_column.get_raw_data(mock_bgpvpn)

        self.assertEqual(result_expected, result)


class TestRoutersColumn(test.TestCase):

    def setUp(self):
        super(TestRoutersColumn, self).setUp()
        self.routers_column = bgpvpn_tables.RoutersColumn(
            "routers", verbose_name=_("Routers"))

    def test_get_raw_data(self):
        result_expected = "<a href=/project/routers/id1/>foo1</a>, " \
                          "<a href=/project/routers/id2/>foo2</a>"
        mock_router1 = mock.Mock(id="id1", name_or_id="foo1")
        mock_router2 = mock.Mock(id="id2", name_or_id="foo2")
        routers = [mock_router1, mock_router2]
        mock_bgpvpn = mock.Mock(routers=routers)
        result = self.routers_column.get_raw_data(mock_bgpvpn)

        self.assertEqual(result_expected, result)
