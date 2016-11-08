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

from networking_bgpvpn.osc import bgpvpn
from networking_bgpvpn.tests.unit.osc import fakes


columns = list(col for _, col in bgpvpn._columns_map)
columns_without_assoc = columns[:-2]


def _get_data(attrs):
    return utils.get_dict_properties(attrs, bgpvpn._get_attr_names([attrs]),
                                     formatters=bgpvpn._formatters)


class TestCreateBgpvpn(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestCreateBgpvpn, self).setUp()
        self.cmd = bgpvpn.CreateBgpvpn(self.app, self.namespace)

    def test_create_bgpvpn_with_no_args(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        self.neutronclient.create_ext = mock.Mock(
            return_value={bgpvpn.resource: fake_bgpvpn})
        arglist = []
        verifylist = [
            ('project', None),
            ('name', None),
            ('type', 'l3'),
            ('route_targets', None),
            ('import_targets', None),
            ('export_targets', None),
            ('route_distinguishers', None),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        self.neutronclient.create_ext.assert_called_once_with(
            bgpvpn._object_path, {bgpvpn.resource: {'type': 'l3'}})
        self.assertEqual(['id', 'tenant_id', 'type'], list(cols))
        self.assertEqual(_get_data(fake_bgpvpn), data)

    def test_create_bgpvpn_with_all_args(self):
        attrs = {
            'tenant_id': 'new_fake_project_id',
            'name': 'fake_name',
            'type': 'l2',
            'route_targets': ['fake_rt1', 'fake_rt2', 'fake_rt3'],
            'import_targets': ['fake_irt1', 'fake_irt2', 'fake_irt3'],
            'export_targets': ['fake_ert1', 'fake_ert2', 'fake_ert3'],
            'route_distinguishers': ['fake_rd1', 'fake_rd2', 'fake_rd3'],
        }
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn(attrs)
        self.neutronclient.create_ext = mock.Mock(
            return_value={bgpvpn.resource: fake_bgpvpn})
        arglist = [
            '--project', fake_bgpvpn['tenant_id'],
            '--name', fake_bgpvpn['name'],
            '--type', fake_bgpvpn['type'],
        ]
        for rt in fake_bgpvpn['route_targets']:
            arglist.extend(['--route-target', rt])
        for rt in fake_bgpvpn['import_targets']:
            arglist.extend(['--import-target', rt])
        for rt in fake_bgpvpn['export_targets']:
            arglist.extend(['--export-target', rt])
        for rd in fake_bgpvpn['route_distinguishers']:
            arglist.extend(['--route-distinguisher', rd])
        verifylist = [
            ('project', fake_bgpvpn['tenant_id']),
            ('name', fake_bgpvpn['name']),
            ('type', fake_bgpvpn['type']),
            ('route_targets', fake_bgpvpn['route_targets']),
            ('import_targets', fake_bgpvpn['import_targets']),
            ('export_targets', fake_bgpvpn['export_targets']),
            ('route_distinguishers', fake_bgpvpn['route_distinguishers']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        fake_bgpvpn_call = copy.deepcopy(fake_bgpvpn)
        fake_bgpvpn_call.pop('id')
        fake_bgpvpn_call.pop('networks')
        fake_bgpvpn_call.pop('routers')
        self.neutronclient.create_ext.assert_called_once_with(
            bgpvpn._object_path, {bgpvpn.resource: fake_bgpvpn_call})
        self.assertEqual(columns_without_assoc, cols)
        self.assertEqual(_get_data(fake_bgpvpn), data)


class TestUpdateBgpvpn(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestUpdateBgpvpn, self).setUp()
        self.cmd = bgpvpn.UpdateBgpvpn(self.app, self.namespace)

    def test_update_bgpvpn(self):
        attrs = {
            'name': 'updated_name',
            'route_targets': ['updated_rt1', 'updated_rt2', 'updated_rt3'],
            'import_targets': ['updated_irt1', 'updated_irt2', 'updated_irt3'],
            'export_targets': ['updated_ert1', 'updated_ert2', 'updated_ert3'],
            'route_distinguishers': ['updated_rd1', 'updated_rd2',
                                     'updated_rd3'],
        }
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn(attrs)
        self.neutronclient.update_ext = mock.Mock(
            return_value={bgpvpn.resource: fake_bgpvpn})
        arglist = [
            fake_bgpvpn['id'],
            '--name', fake_bgpvpn['name'],
        ]
        for rt in fake_bgpvpn['route_targets']:
            arglist.extend(['--route-target', rt])
        for rt in fake_bgpvpn['import_targets']:
            arglist.extend(['--import-target', rt])
        for rt in fake_bgpvpn['export_targets']:
            arglist.extend(['--export-target', rt])
        for rd in fake_bgpvpn['route_distinguishers']:
            arglist.extend(['--route-distinguisher', rd])
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
            ('name', fake_bgpvpn['name']),
            ('route_targets', fake_bgpvpn['route_targets']),
            ('import_targets', fake_bgpvpn['import_targets']),
            ('export_targets', fake_bgpvpn['export_targets']),
            ('route_distinguishers', fake_bgpvpn['route_distinguishers']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.update_ext.assert_called_once_with(
            bgpvpn.resource_path, fake_bgpvpn['id'], {bgpvpn.resource: attrs})
        self.assertIsNone(result)


class TestDeleteBgpvpn(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestDeleteBgpvpn, self).setUp()
        self.cmd = bgpvpn.DeleteBgpvpn(self.app, self.namespace)

    def test_delete_one_bgpvpn(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        self.neutronclient.delete_ext = mock.Mock()
        arglist = [
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('bgpvpns', [fake_bgpvpn['id']]),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.delete_ext.assert_called_once_with(
            bgpvpn.resource_path, fake_bgpvpn['id'])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn(self):
        fake_bgpvpns = fakes.FakeBgpvpn.create_bgpvpns(count=3)
        fake_bgpvpn_ids = [fake_bgpvpn['id'] for fake_bgpvpn in
                           fake_bgpvpns[bgpvpn._resource_plural]]
        self.neutronclient.delete_ext = mock.Mock()
        arglist = fake_bgpvpn_ids
        verifylist = [
            ('bgpvpns', fake_bgpvpn_ids),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        result = self.cmd.take_action(parsed_args)

        self.neutronclient.delete_ext.assert_has_calls(
            [mock.call(bgpvpn.resource_path, id) for id in fake_bgpvpn_ids])
        self.assertIsNone(result)

    def test_delete_multi_bpgvpn_with_unknown(self):
        count = 3
        fake_bgpvpns = fakes.FakeBgpvpn.create_bgpvpns(count=count)
        fake_bgpvpn_ids = [fake_bgpvpn['id'] for fake_bgpvpn in
                           fake_bgpvpns[bgpvpn._resource_plural]]

        def raise_unknonw_resource(resource_path, name_or_id):
            if str(count - 2) in name_or_id:
                raise Exception()
        self.neutronclient.delete_ext = mock.Mock(
            side_effect=raise_unknonw_resource)
        arglist = fake_bgpvpn_ids
        verifylist = [
            ('bgpvpns', fake_bgpvpn_ids),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        self.assertRaises(exceptions.CommandError, self.cmd.take_action,
                          parsed_args)

        self.neutronclient.delete_ext.assert_has_calls(
            [mock.call(bgpvpn.resource_path, id) for id in fake_bgpvpn_ids])


class TestListBgpvpn(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestListBgpvpn, self).setUp()
        self.cmd = bgpvpn.ListBgpvpn(self.app, self.namespace)

    def test_list_all_bgpvpn(self):
        count = 3
        fake_bgpvpns = fakes.FakeBgpvpn.create_bgpvpns(count=count)
        self.neutronclient.list_ext = mock.Mock(return_value=fake_bgpvpns)
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list_ext.assert_called_once_with(
            collection=bgpvpn._resource_plural,
            path=bgpvpn._object_path,
            retrieve_all=True)
        self.assertEqual(headers, ['ID', 'Project ID', 'Type'])
        self.assertEqual(list(data),
                         [_get_data(fake_bgpvpn) for fake_bgpvpn
                          in fake_bgpvpns[bgpvpn._resource_plural]])

    def test_list_project_bgpvpn(self):
        count = 3
        project_id = 'list_fake_project_id'
        attrs = {'tenant_id': project_id}
        fake_bgpvpns = fakes.FakeBgpvpn.create_bgpvpns(count=count,
                                                       attrs=attrs)
        self.neutronclient.list_ext = mock.Mock(return_value=fake_bgpvpns)
        arglist = [
            '--project', project_id,
        ]
        verifylist = [
            ('project', project_id),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list_ext.assert_called_once_with(
            collection=bgpvpn._resource_plural,
            path=bgpvpn._object_path,
            retrieve_all=True,
            tenant_id=project_id)
        self.assertEqual(headers, ['ID', 'Project ID', 'Type'])
        self.assertEqual(list(data),
                         [_get_data(fake_bgpvpn) for fake_bgpvpn
                          in fake_bgpvpns[bgpvpn._resource_plural]])

    def test_list_bgpvpn_with_filters(self):
        count = 3
        name = 'fake_id0'
        layer_type = 'l2'
        attrs = {'type': layer_type}
        fake_bgpvpns = fakes.FakeBgpvpn.create_bgpvpns(count=count,
                                                       attrs=attrs)
        returned_bgpvpn = fake_bgpvpns[bgpvpn._resource_plural][0]
        self.neutronclient.list_ext = mock.Mock(
            return_value={bgpvpn._resource_plural: [returned_bgpvpn]})
        arglist = [
            '--property', 'name=%s' % name,
            '--property', 'type=%s' % layer_type,
        ]
        verifylist = [
            ('property', {'name': name, 'type': layer_type}),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        headers, data = self.cmd.take_action(parsed_args)

        self.neutronclient.list_ext.assert_called_once_with(
            collection=bgpvpn._resource_plural,
            path=bgpvpn._object_path,
            retrieve_all=True,
            name=name,
            type=layer_type)
        self.assertEqual(headers, ['ID', 'Project ID', 'Type'])
        self.assertEqual(list(data), [_get_data(returned_bgpvpn)])


class TestShowBgpvpn(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestShowBgpvpn, self).setUp()
        self.cmd = bgpvpn.ShowBgpvpn(self.app, self.namespace)

    def test_show_bgpvpn(self):
        fake_bgpvpn = fakes.FakeBgpvpn.create_one_bgpvpn()
        self.neutronclient.show_ext = mock.Mock(
            return_value={bgpvpn.resource: fake_bgpvpn})
        arglist = [
            fake_bgpvpn['id'],
        ]
        verifylist = [
            ('bgpvpn', fake_bgpvpn['id']),
        ]

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        cols, data = self.cmd.take_action(parsed_args)

        self.neutronclient.show_ext.assert_called_once_with(
            bgpvpn.resource_path, fake_bgpvpn['id'])
        self.assertEqual(['id', 'tenant_id', 'type'], list(cols))
        self.assertEqual(_get_data(fake_bgpvpn), data)
