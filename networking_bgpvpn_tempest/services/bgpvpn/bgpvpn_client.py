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

from tempest.lib.services.network import base

# This is the representation of the bgpvpn
# client of networking-bgpvpn

BGPVPN_OBJECT_PATH = '/bgpvpn/bgpvpns'
BGPVPN_RESOURCE_PATH = '/bgpvpn/bgpvpns/%s'
BGPVPN_NETWORK_ASSOCIATION_PATH = '/bgpvpn/bgpvpns/%s/network_associations'
BGPVPN_ROUTER_ASSOCIATION_PATH = '/bgpvpn/bgpvpns/%s/router_associations'


class BgpvpnClient(base.BaseNetworkClient):

    def create_bgpvpn(self, **kwargs):
        uri = BGPVPN_OBJECT_PATH
        post_data = {'bgpvpn': kwargs}
        return self.create_resource(uri, post_data)

    def delete_bgpvpn(self, bgpvpn_id):
        uri = BGPVPN_RESOURCE_PATH % bgpvpn_id
        return self.delete_resource(uri)

    def show_bgpvpn(self, bgpvpn_id, **fields):
        uri = BGPVPN_RESOURCE_PATH % bgpvpn_id
        return self.show_resource(uri, **fields)

    def list_bgpvpns(self, **filters):
        uri = BGPVPN_OBJECT_PATH
        return self.list_resources(uri, **filters)

    def update_bgpvpn(self, bgpvpn_id, **kwargs):
        uri = BGPVPN_RESOURCE_PATH % bgpvpn_id
        post_data = {'bgpvpn': kwargs}
        return self.update_resource(uri, post_data)

    def create_network_association(self, bgpvpn_id, network_id):
        uri = BGPVPN_NETWORK_ASSOCIATION_PATH % bgpvpn_id
        post_data = {"network_association":
                     {"network_id": network_id}}
        return self.create_resource(uri, post_data)

    def delete_network_association(self, bgpvpn_id, association_id):
        uri_pattern = BGPVPN_NETWORK_ASSOCIATION_PATH + "/%s"
        uri = uri_pattern % (bgpvpn_id, association_id)
        return self.delete_resource(uri)

    def show_network_association(self, bgpvpn_id, association_id, **fields):
        uri_pattern = BGPVPN_NETWORK_ASSOCIATION_PATH + "/%s"
        uri = uri_pattern % (bgpvpn_id, association_id)
        return self.show_resource(uri, **fields)

    def list_network_associations(self, bgpvpn_id, **filters):
        uri = BGPVPN_NETWORK_ASSOCIATION_PATH % bgpvpn_id
        return self.list_resources(uri, **filters)

    def create_router_association(self, bgpvpn_id, router_id):
        uri = BGPVPN_ROUTER_ASSOCIATION_PATH % bgpvpn_id
        post_data = {"router_association":
                     {"router_id": router_id}}
        return self.create_resource(uri, post_data)

    def delete_router_association(self, bgpvpn_id, association_id):
        uri_pattern = BGPVPN_ROUTER_ASSOCIATION_PATH + "/%s"
        uri = uri_pattern % (bgpvpn_id, association_id)
        return self.delete_resource(uri)
