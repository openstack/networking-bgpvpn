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

from openstack_dashboard.test.test_data import utils


def load_test_data(load_onto=None):
    from openstack_dashboard.test.test_data import exceptions
    from openstack_dashboard.test.test_data import neutron_data

    from bgpvpn_dashboard.test.test_data import bgpvpn_data

    # The order of these loaders matters, some depend on others.
    loaders = (
        exceptions.data,
        neutron_data.data,
        bgpvpn_data.data,
    )
    if load_onto:
        for data_func in loaders:
            data_func(load_onto)
        return load_onto
    else:
        return utils.TestData(*loaders)
