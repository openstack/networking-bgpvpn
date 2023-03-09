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
        'create_bgpvpn_network_association',
        base.RULE_ADMIN_OR_OWNER,
        'Create a network association',
        [
            {
                'method': 'POST',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/network_associations',
            },
        ]
    ),
    # TODO(amotoki): PUT operation is not defined in the API ref. Drop it?
    policy.DocumentedRuleDefault(
        'update_bgpvpn_network_association',
        base.RULE_ADMIN_OR_OWNER,
        'Update a network association',
        [
            {
                'method': 'PUT',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'network_associations/{network_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'delete_bgpvpn_network_association',
        base.RULE_ADMIN_OR_OWNER,
        'Delete a network association',
        [
            {
                'method': 'DELETE',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'network_associations/{network_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn_network_association',
        base.RULE_ADMIN_OR_OWNER,
        'Get network associations',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/network_associations',
            },
            {
                'method': 'GET',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'network_associations/{network_association_id}'),
            },
        ]
    ),
    policy.DocumentedRuleDefault(
        'get_bgpvpn_network_association:tenant_id',
        base.RULE_ADMIN_ONLY,
        'Get ``tenant_id`` attributes of network associations',
        [
            {
                'method': 'GET',
                'path': '/bgpvpn/bgpvpns/{bgpvpn_id}/network_associations',
            },
            {
                'method': 'GET',
                'path': ('/bgpvpn/bgpvpns/{bgpvpn_id}/'
                         'network_associations/{network_association_id}'),
            },
        ]
    ),
]


def list_rules():
    return rules
