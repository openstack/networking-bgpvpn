# Copyright (c) 2017 Juniper Networks, Inc.
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

from neutron.tests import base

from networking_bgpvpn.neutron.services.common.utils import filter_resource


class TestFilterResource(base.BaseTestCase):
    _fake_resource_string = {
        'fake_attribute': 'fake_value1',
    }
    _fake_resource_list = {
        'fake_attribute': ['fake_value1', 'fake_value2', 'fake_value3'],
    }

    def test_filter_resource_succeeds_with_one_value(self):
        filters = {
            'fake_attribute': 'fake_value1',
        }
        self.assertTrue(filter_resource(self._fake_resource_string, filters))
        self.assertTrue(filter_resource(self._fake_resource_list, filters))

    def test_filter_resource_fails_with_one_value(self):
        filters = {
            'fake_attribute': 'wrong_fake_value1',
        }
        self.assertFalse(filter_resource(self._fake_resource_string, filters))
        self.assertFalse(filter_resource(self._fake_resource_list, filters))

    def test_filter_resource_succeeds_with_list_of_values(self):
        filters = {
            'fake_attribute': ['fake_value1'],
        }
        self.assertTrue(filter_resource(self._fake_resource_string, filters))
        filters = {
            'fake_attribute': ['fake_value1', 'fake_value2'],
        }
        self.assertTrue(filter_resource(self._fake_resource_list, filters))

    def test_filter_resource_fails_with_list_of_values(self):
        filters = {
            'fake_attribute': ['wrong_fake_value1'],
        }
        self.assertFalse(filter_resource(self._fake_resource_string, filters))
        filters = {
            'fake_attribute': ['wrong_fake_value1', 'fake_value2'],
        }
        self.assertFalse(filter_resource(self._fake_resource_list, filters))
