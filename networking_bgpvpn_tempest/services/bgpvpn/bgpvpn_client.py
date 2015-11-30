# Copyright (c) 2015 Ericsson.
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

from networking_bgpvpn.neutronclient.neutron.v2_0.bgpvpn.bgpvpn import \
    BGPVPN
from tempest.services.network.json import base


class BgpvpnClient(base.BaseNetworkClient):

    def create_bgpvpn(self, **kwargs):
        uri = BGPVPN.object_path
        post_data = {'bgpvpn': kwargs}
        return self.create_resource(uri, post_data)

    def delete_bgpvpn(self, bgpvpn_id):
        uri = BGPVPN.resource_path % bgpvpn_id
        return self.delete_resource(uri)

    def show_bgpvpn(self, bgpvpn_id, **fields):
        uri = BGPVPN.resource_path % bgpvpn_id
        return self.show_resource(uri, **fields)

    def list_bgpvpns(self, **filters):
        uri = BGPVPN.object_path
        return self.list_resources(uri, **filters)

    def update_bgpvpn(self, bgpvpn_id, **kwargs):
        uri = BGPVPN.resource_path % bgpvpn_id
        post_data = {'bgpvpn': kwargs}
        return self.update_resource(uri, post_data)
