#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from neutron_lib import policy as base
from oslo_policy import policy


rules = [
    policy.DocumentedRuleDefault(
        'create_bgpvpn',
        base.RULE_ADMIN_ONLY,
        'Create a BGP VPN',
        [
            {
                'method': 'POST',
                'path': '/bgpvpn/bgpvpns',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'update_bgpvpn',
        base.RULE_ADMIN_OR_OWNER,
        'Update a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    # TODO(amotoki): tenant_id is not updatable, so perhaps this can be dropped
    policy.DocumentedRuleDefault(
        'update_bgpvpn:tenant_id',
        base.RULE_ADMIN_ONLY,
        'Update ``tenant_id`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_bgpvpn:route_targets',
        base.RULE_ADMIN_ONLY,
        'Update ``route_targets`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_bgpvpn:import_targets',
        base.RULE_ADMIN_ONLY,
        'Update ``import_targets`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_bgpvpn:export_targets',
        base.RULE_ADMIN_ONLY,
        'Update ``export_targets`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_bgpvpn:route_distinguishers',
        base.RULE_ADMIN_ONLY,
        'Update ``route_distinguishers`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    # TODO(amotoki): vni is not updatable, so perhaps this can be dropped
    policy.DocumentedRuleDefault(
        'update_bgpvpn:vni',
        base.RULE_ADMIN_ONLY,
        'Update ``vni`` attribute of a BGP VPN',
        [
            {
                'method': 'PUT',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'delete_bgpvpn',
        base.RULE_ADMIN_ONLY,
        'Delete a BGP VPN',
        [
            {
                'method': 'DELETE',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn',
        base.RULE_ADMIN_OR_OWNER,
        'Get BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'get_bgpvpn:tenant_id',
        base.RULE_ADMIN_ONLY,
        'Get ``tenant_id`` attributes of BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn:route_targets',
        base.RULE_ADMIN_ONLY,
        'Get ``route_targets`` attributes of BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn:import_targets',
        base.RULE_ADMIN_ONLY,
        'Get ``import_targets`` attributes of BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn:export_targets',
        base.RULE_ADMIN_ONLY,
        'Get ``export_targets`` attributes of  BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn:route_distinguishers',
        base.RULE_ADMIN_ONLY,
        'Get ``route_distinguishers`` attributes of BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn:vni',
        base.RULE_ADMIN_ONLY,
        'Get ``vni`` attributes of BGP VPNs',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns',
            },
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{id}',
            },
        ]
    ),
]


def list_rules():
    return rules
