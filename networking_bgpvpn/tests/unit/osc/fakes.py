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

import argparse
import copy
import mock

from openstackclient.identity import common as identity_common
from osc_lib.tests import utils as tests_utils

from networking_bgpvpn.osc import bgpvpn
from networking_bgpvpn.osc.bgpvpn import resource_path as bgpvpn_resource_path
from networking_bgpvpn.osc.resource_association import CreateBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import DeleteBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import ListBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import ShowBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import UpdateBgpvpnResAssoc


class TestNeutronClientOSCV2(tests_utils.TestCommand):

    def setUp(self):
        super(TestNeutronClientOSCV2, self).setUp()
        self.namespace = argparse.Namespace()
        self.app.client_manager.session = mock.Mock()
        self.app.client_manager.neutronclient = mock.Mock()
        self.neutronclient = self.app.client_manager.neutronclient
        self.neutronclient.find_resource = mock.Mock(
            side_effect=lambda _, name_or_id: {'id': name_or_id})
        identity_common.find_project = mock.Mock(
            side_effect=lambda _, name_or_id, __: mock.Mock(id=name_or_id))


class FakeBgpvpn(object):
    """Fake BGP VPN with attributes."""

    @staticmethod
    def create_one_bgpvpn(attrs=None):
        """Create a fake BGP VPN."""

        attrs = attrs or {}

        # Set default attributes.
        bgpvpn_attrs = {
            'id': 'fake_bgpvpn_id',
            'tenant_id': 'fake_project_id',
            'name': '',
            'type': 'l3',
            'route_targets': [],
            'import_targets': [],
            'export_targets': [],
            'route_distinguishers': [],
            'networks': [],
            'routers': [],
        }

        # Overwrite default attributes.
        bgpvpn_attrs.update(attrs)
        return copy.deepcopy(bgpvpn_attrs)

    @staticmethod
    def create_bgpvpns(attrs=None, count=1):
        """Create multiple fake BGP VPN."""

        bgpvpns = []
        for i in range(0, count):
            if attrs is None:
                attrs = {'id': 'fake_id%d' % i}
            elif getattr(attrs, 'id', None) is None:
                attrs['id'] = 'fake_id%d' % i
            bgpvpns.append(FakeBgpvpn.create_one_bgpvpn(attrs))

        return {bgpvpn._resource_plural: bgpvpns}


class BgpvpnFakeAssoc(object):
    _assoc_res_name = 'fake_resource'
    _resource = '%s_association' % _assoc_res_name
    _resource_plural = '%ss' % _resource
    _object_path = '%s/%s' % (bgpvpn_resource_path, _resource_plural)
    _resource_path = '%s/%s/%%%%s' % (bgpvpn_resource_path, _resource_plural)

    _columns_map = (
        ('ID', 'id'),
        ('Project ID', 'tenant_id'),
        ('%s ID' % _assoc_res_name.capitalize(), '%s_id' % _assoc_res_name),
    )


class CreateBgpvpnFakeResAssoc(BgpvpnFakeAssoc, CreateBgpvpnResAssoc):
    pass


class UpdateBgpvpnFakeResAssoc(BgpvpnFakeAssoc, UpdateBgpvpnResAssoc):
    pass


class DeleteBgpvpnFakeResAssoc(BgpvpnFakeAssoc, DeleteBgpvpnResAssoc):
    pass


class ListBgpvpnFakeResAssoc(BgpvpnFakeAssoc, ListBgpvpnResAssoc):
    pass


class ShowBgpvpnFakeResAssoc(BgpvpnFakeAssoc, ShowBgpvpnResAssoc):
    pass


class FakeResource(object):
    """Fake resource with minimal attributes."""

    @staticmethod
    def create_one_resource(attrs=None):
        """Create a fake resource."""

        attrs = attrs or {}

        # Set default attributes.
        res_attrs = {
            'id': 'fake_resource_id',
            'tenant_id': 'fake_project_id',
        }

        # Overwrite default attributes.
        res_attrs.update(attrs)
        return copy.deepcopy(res_attrs)

    @staticmethod
    def create_resources(attrs=None, count=1):
        """Create multiple fake resources."""

        resources = []
        for i in range(0, count):
            if attrs is None:
                attrs = {'id': 'fake_id%d' % i}
            elif getattr(attrs, 'id', None) is None:
                attrs['id'] = 'fake_id%d' % i
            resources.append(FakeResource.create_one_resource(attrs))

        return {'%ss' % BgpvpnFakeAssoc._assoc_res_name: resources}


class FakeResAssoc(object):
    """Fake resource association with minimal attributes."""

    @staticmethod
    def create_one_resource_association(resource):
        """Create a fake resource association."""

        res_assoc_attrs = {
            'id': 'fake_association_id',
            'tenant_id': resource['tenant_id'],
            'fake_resource_id': resource['id'],
        }
        return copy.deepcopy(res_assoc_attrs)

    @staticmethod
    def create_resource_associations(resources):
        """Create multiple fake resource associations."""

        res_assocs = []
        for idx, resource in enumerate(
                resources['%ss' % BgpvpnFakeAssoc._assoc_res_name]):
            res_assoc_attrs = {
                'id': 'fake_association_id%d' % idx,
                'tenant_id': resource['tenant_id'],
                'fake_resource_id': resource['id'],
            }
            res_assocs.append(copy.deepcopy(res_assoc_attrs))

        return {BgpvpnFakeAssoc._resource_plural: res_assocs}
