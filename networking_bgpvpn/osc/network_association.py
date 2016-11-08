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


from networking_bgpvpn.osc.bgpvpn import resource_path as bgpvpn_resource_path
from networking_bgpvpn.osc.resource_association import CreateBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import DeleteBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import ListBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import ShowBgpvpnResAssoc
from networking_bgpvpn.osc.resource_association import UpdateBgpvpnResAssoc


class BgpvpnNetAssoc(object):
    _assoc_res_name = 'network'
    _resource = '%s_association' % _assoc_res_name
    _resource_plural = '%ss' % _resource
    _object_path = '%s/%s' % (bgpvpn_resource_path, _resource_plural)
    _resource_path = '%s/%s/%%%%s' % (bgpvpn_resource_path, _resource_plural)

    _columns_map = (
        ('ID', 'id'),
        ('Project ID', 'tenant_id'),
        ('%s ID' % _assoc_res_name.capitalize(), '%s_id' % _assoc_res_name),
    )


class CreateBgpvpnNetAssoc(BgpvpnNetAssoc, CreateBgpvpnResAssoc):
    pass


class UpdateBgpvpnNetAssoc(BgpvpnNetAssoc, UpdateBgpvpnResAssoc):
    pass


class DeleteBgpvpnNetAssoc(BgpvpnNetAssoc, DeleteBgpvpnResAssoc):
    pass


class ListBgpvpnNetAssoc(BgpvpnNetAssoc, ListBgpvpnResAssoc):
    pass


class ShowBgpvpnNetAssoc(BgpvpnNetAssoc, ShowBgpvpnResAssoc):
    pass
