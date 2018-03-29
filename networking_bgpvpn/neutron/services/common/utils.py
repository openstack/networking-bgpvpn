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


from neutron_lib.api.definitions import bgpvpn as bgpvpn_def
from neutron_lib.api.definitions import bgpvpn_routes_control as bgpvpn_rc_def
from neutron_lib.api.definitions import bgpvpn_vni as bgpvpn_vni_def
from neutron_lib.plugins import directory


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
    for key, value in filters.items():
        if key in resource.keys():
            if not isinstance(value, list):
                value = [value]
            if isinstance(resource[key], list):
                resource_value = resource[key]
            else:
                resource_value = [resource[key]]
            if not set(value).issubset(set(resource_value)):
                return False
    return True


def filter_fields(resource, fields):
    if fields:
        return dict(((key, item) for key, item in resource.items()
                     if key in fields))
    return resource


def is_extension_supported(plugin, ext_alias):
    return ext_alias in plugin.supported_extension_aliases


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
        'ports': bgpvpn.get('ports', []),
    }
    plugin = directory.get_plugin(bgpvpn_def.ALIAS)
    if is_extension_supported(plugin, bgpvpn_vni_def.ALIAS):
        res[bgpvpn_vni_def.VNI] = bgpvpn.get(bgpvpn_vni_def.VNI)
    if is_extension_supported(plugin, bgpvpn_rc_def.ALIAS):
        res[bgpvpn_rc_def.LOCAL_PREF_KEY] = bgpvpn.get(
            bgpvpn_rc_def.LOCAL_PREF_KEY)
    return filter_fields(res, fields)


def make_net_assoc_dict(id, tenant_id, bgpvpn_id, network_id, fields=None):
    res = {'id': id,
           'tenant_id': tenant_id,
           'bgpvpn_id': bgpvpn_id,
           'network_id': network_id}
    return filter_fields(res, fields)


def make_router_assoc_dict(id, tenant_id, bgpvpn_id, router_id, fields=None):
    res = {'id': id,
           'tenant_id': tenant_id,
           'bgpvpn_id': bgpvpn_id,
           'router_id': router_id}
    return filter_fields(res, fields)


def make_port_assoc_dict(id, tenant_id, bgpvpn_id, port_id, fields=None):
    # NOTE(tmorin): fields need to be added here, this isn't used yet
    res = {'id': id,
           'tenant_id': tenant_id,
           'bgpvpn_id': bgpvpn_id,
           'port_id': port_id}
    return filter_fields(res, fields)


def get_bgpvpn_differences(current_dict, old_dict):
    """Compare 2 BGP VPN

    - added keys
    - removed keys
    - changed values for keys in both dictionaries
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
