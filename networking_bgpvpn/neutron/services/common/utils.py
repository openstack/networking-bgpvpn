# Copyright (c) 2015 Cloudwatt.
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

import six


def rtrd_list2str(list):
    """Format Route Target list to string"""
    if not list:
        return ''

    if isinstance(list, str):
        return list

    return ','.join(list)


def rtrd_str2list(str):
    """Format Route Target string to list"""
    if not str:
        return []

    if isinstance(str, list):
        return str

    return str.split(',')


def filter_resource(resource, filters=None):
    if not filters:
        filters = {}
    for key, value in six.iteritems(filters):
        if key in resource.keys():
            if isinstance(value, list):
                if resource[key] not in value:
                    return False
            elif resource[key] != value:
                return False
    return True


def filter_fields(resource, fields):
    if fields:
        return dict(((key, item) for key, item in resource.items()
                     if key in fields))
    return resource


def make_bgpvpn_dict(bgpvpn, fields=None):
    res = {
        'id': bgpvpn['id'],
        'tenant_id': bgpvpn['tenant_id'],
        'name': bgpvpn['name'],
        'type': bgpvpn['type'],
        'route_targets': rtrd_str2list(bgpvpn['route_targets']),
        'import_targets': rtrd_str2list(bgpvpn['import_targets']),
        'export_targets': rtrd_str2list(bgpvpn['export_targets']),
        'route_distinguishers': rtrd_str2list(bgpvpn['route_distinguishers']),
        'networks': bgpvpn.get('networks', []),
        'routers': bgpvpn.get('routers', []),
    }
    return filter_fields(res, fields)


def make_net_assoc_dict(id, tenant_id, bgpvpn_id, network_id, fields=None):
    res = {'id': id,
           'tenant_id': tenant_id,
           'bgpvpn_id': bgpvpn_id,
           'network_id': network_id}
    return filter_fields(res, fields)


def get_bgpvpn_differences(current_dict, old_dict):
    """Compare 2 BGP VPN

    - added elements (route_targets, import_targets or export_targets)
    - removed elements (route_targets, import_targets or export_targets)
    - changed values for keys in both dictionaries  (network_id,
      route_targets, import_targets or export_targets)
    """
    set_current = set(current_dict.keys())
    set_old = set(old_dict.keys())
    intersect = set_current.intersection(set_old)

    added = set_current - intersect
    removed = set_old - intersect
    changed = set(
        key for key in intersect if old_dict[key] != current_dict[key]
    )

    return (added, removed, changed)
