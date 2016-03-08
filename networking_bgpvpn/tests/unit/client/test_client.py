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

import mock

from neutron.tests.unit.extensions import base as test_extensions_base

from neutronclient.v2_0 import client


BGPVPN_ID = "uuid-bgpvpn-foo"
NET_ASSOC_ID = "uuid-netassoc-bar"

ASSOCS_PATH = "/bgpvpn/bgpvpns/%s/network_associations" % BGPVPN_ID
ASSOC_PATH = "/bgpvpn/bgpvpns/%s/network_associations/%%s" % BGPVPN_ID


class BgpvpnClientTestCase(test_extensions_base.ExtensionTestCase):

    def setUp(self):
        super(BgpvpnClientTestCase, self).setUp()

        self.client = client.Client()
        self.client.list_ext = mock.Mock()
        self.client.create_ext = mock.Mock()
        self.client.show_ext = mock.Mock()
        self.client.update_ext = mock.Mock()
        self.client.delete_ext = mock.Mock()

    def test_api_url_list(self):
        self.client.list_network_associations(BGPVPN_ID)
        self.client.list_ext.assert_called_once_with(mock.ANY, ASSOCS_PATH,
                                                     mock.ANY)

    def test_api_url_create(self):
        self.client.create_network_association(BGPVPN_ID, {})
        self.client.create_ext.assert_called_once_with(ASSOCS_PATH, mock.ANY)

    def test_api_url_show(self):
        self.client.show_network_association(NET_ASSOC_ID, BGPVPN_ID)
        self.client.show_ext.assert_called_once_with(ASSOC_PATH,
                                                     NET_ASSOC_ID)

    def test_api_url_update(self):
        self.client.update_network_association(NET_ASSOC_ID, BGPVPN_ID, {})
        self.client.update_ext.assert_called_once_with(ASSOC_PATH,
                                                       NET_ASSOC_ID,
                                                       mock.ANY)

    def test_api_url_delete(self):
        self.client.delete_network_association(NET_ASSOC_ID, BGPVPN_ID)
        self.client.delete_ext.assert_called_once_with(ASSOC_PATH,
                                                       NET_ASSOC_ID)
