# Copyright (c) 2016 Juniper Networks Inc.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import copy
import mock

from osc_lib import exceptions
from osc_lib import utils

from networking_bgpvpn.tests.unit.osc import fakes


columns = list(col for _, col in fakes.BgpvpnFakeAssoc._columns_map)
headers = list(head for head, _ in fakes.BgpvpnFakeAssoc._columns_map)


def _get_data(attrs):
    return utils.get_dict_properties(attrs, columns)


class TestCreateResAssoc(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestCreateResAssoc, self).setUp()
        self.cmd = fakes.CreateBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_create_resource_association(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_res = fakes.FakeResource.create_one_resource()
        fake_res_assoc = fakes.FakeResAssoc.create_one_resource_association(
            fake_res)
        self.neutronclient.create_ext = mock.Mock(
            return_value={fakes.BgpvpnFakeAssoc._resource: fake_res_assoc})
        arglist = [
            fake_bgpvpn['id'],
            fake_res['id'],
            '--project', fake_bgpvpn['tenant_id'],
        ]
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
            ('resource', fake_res['id']),
            ('project', fake_bgpvpn['tenant_id'])
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        fake_res_assoc_call = copy.deepcopy(fake_res_assoc)
        fake_res_assoc_call.pop('id')
        self.neutronclient.create_ext.assert_called_once_with(
            fakes.BgpvpnFakeAssoc._object_path % fake_bgpvpn['id'],
            {fakes.BgpvpnFakeAssoc._resource: fake_res_assoc_call})
        self.assertEqual(columns, cols)
        self.assertEqual(_get_data(fake_res_assoc), data)


class TestUpdateResAssoc(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestUpdateResAssoc, self).setUp()
        self.cmd = fakes.UpdateBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_update_resource_association(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_res = fakes.FakeResource.create_one_resource()
        fake_res_assoc = fakes.FakeResAssoc.create_one_resource_association(
            fake_res)
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_association', fake_res_assoc['id']),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.UnsupportedVersion, self.cmd.take_action,
                          parsed_args)


class TestDeleteResAssoc(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestDeleteResAssoc, self).setUp()
        self.cmd = fakes.DeleteBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_delete_one_association(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_res = fakes.FakeResource.create_one_resource()
        fake_res_assoc = fakes.FakeResAssoc.create_one_resource_association(
            fake_res)
        self.neutronclient.delete_ext = mock.Mock()
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_associations', [fake_res_assoc['id']]),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.delete_ext.assert_called_once_with(
            fakes.BgpvpnFakeAssoc._resource_path % fake_bgpvpn['id'],
            fake_res_assoc['id'])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn(self):
        count = 3
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_ress = fakes.FakeResource.create_resources(count=count)
        fake_res_assocs = fakes.FakeResAssoc.create_resource_associations(
            fake_ress)
        fake_res_assoc_ids = [
            fake_res_assoc['id'] for fake_res_assoc in
            fake_res_assocs[fakes.BgpvpnFakeAssoc._resource_plural]
        ]
        self.neutronclient.delete_ext = mock.Mock()
        arglist = \
            fake_res_assoc_ids + [
                fake_bgpvpn['id']
            ]
        verifylist = [
            ('resource_associations', fake_res_assoc_ids),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.delete_ext.assert_has_calls(
            [mock.call(
                fakes.BgpvpnFakeAssoc._resource_path % fake_bgpvpn['id'], id)
                for id in fake_res_assoc_ids])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn_with_unknown(self):
        count = 3
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_ress = fakes.FakeResource.create_resources(count=count)
        fake_res_assocs = fakes.FakeResAssoc.create_resource_associations(
            fake_ress)
        fake_res_assoc_ids = [
            fake_res_assoc['id'] for fake_res_assoc in
            fake_res_assocs[fakes.BgpvpnFakeAssoc._resource_plural]
        ]

        def raise_unknonw_resource(resource_path, name_or_id):
            if str(count - 2) in name_or_id:
                raise Exception()
        self.neutronclient.delete_ext = mock.Mock(
            side_effect=raise_unknonw_resource)
        arglist = \
            fake_res_assoc_ids + [
                fake_bgpvpn['id']
            ]
        verifylist = [
            ('resource_associations', fake_res_assoc_ids),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError, self.cmd.take_action,
                          parsed_args)

        self.neutronclient.delete_ext.assert_has_calls(
            [mock.call(
                fakes.BgpvpnFakeAssoc._resource_path % fake_bgpvpn['id'], id)
                for id in fake_res_assoc_ids])


class TestListResAssoc(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestListResAssoc, self).setUp()
        self.cmd = fakes.ListBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_list_bgpvpn_associations(self):
        count = 3
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_ress = fakes.FakeResource.create_resources(count=count)
        fake_res_assocs = fakes.FakeResAssoc.create_resource_associations(
            fake_ress)
        self.neutronclient.list_ext = mock.Mock(return_value=fake_res_assocs)
        arglist = [
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        col_headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list_ext.assert_called_once_with(
            collection=fakes.BgpvpnFakeAssoc._resource_plural,
            path=fakes.BgpvpnFakeAssoc._object_path % fake_bgpvpn['id'],
            retrieve_all=True)
        self.assertEqual(col_headers, headers)
        self.assertEqual(
            list(data),
            [_get_data(fake_res_assoc) for fake_res_assoc
             in fake_res_assocs[fakes.BgpvpnFakeAssoc._resource_plural]])


class TestShowResAssoc(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestShowResAssoc, self).setUp()
        self.cmd = fakes.ShowBgpvpnFakeResAssoc(self.app, self.namespace)

    def test_show_resource_association(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        fake_res = fakes.FakeResource.create_one_resource()
        fake_res_assoc = fakes.FakeResAssoc.create_one_resource_association(
            fake_res)
        self.neutronclient.show_ext = mock.Mock(
            return_value={fakes.BgpvpnFakeAssoc._resource: fake_res_assoc})
        arglist = [
            fake_res_assoc['id'],
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('resource_association', fake_res_assoc['id']),
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        self.neutronclient.show_ext.assert_called_once_with(
            fakes.BgpvpnFakeAssoc._resource_path % fake_bgpvpn['id'],
            fake_res_assoc['id'])
        self.assertEqual(list(cols), columns)
        self.assertEqual(data, _get_data(fake_res_assoc))
