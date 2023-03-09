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
        'create_bgpvpn_router_association',
        base.RULE_ADMIN_OR_OWNER,
        'Create a router association',
        [
            {
                'method': 'POST',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/router_associations',
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'update_bgpvpn_router_association',
        base.RULE_ADMIN_OR_OWNER,
        'Update a router association',
        [
            {
                'method': 'PUT',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'router_associations/{router_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'delete_bgpvpn_router_association',
        base.RULE_ADMIN_OR_OWNER,
        'Delete a router association',
        [
            {
                'method': 'DELETE',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'router_associations/{router_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn_router_association',
        base.RULE_ADMIN_OR_OWNER,
        'Get router associations',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/router_associations',
            },
            {
                'method': 'GET',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'router_associations/{router_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn_router_association:tenant_id',
        base.RULE_ADMIN_ONLY,
        'Get ``tenant_id`` attributes of router associations',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/router_associations',
            },
            {
                'method': 'GET',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'router_associations/{router_association_id}'),
            },
        ]
    ),
]


def list_rules():
    return rules
