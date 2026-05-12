# Copyright (c) 2016 Orange.
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

import logging

from openstack_dashboard.api import neutron

LOG = logging.getLogger(__name__)

networkclient = neutron.networkclient


class Bgpvpn(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn."""


class NetworkAssociation(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn networks associations."""


class RouterAssociation(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn routers associations."""


def bgpvpns_list(request, **kwargs):
    LOG.debug("bgpvpn_list(): params=%s", kwargs)
    bgpvpns = networkclient(request).bgpvpns(**kwargs)
    return [Bgpvpn(v.to_dict()) for v in bgpvpns]


def bgpvpn_get(request, bgpvpn_id, **kwargs):
    LOG.debug("bgpvpn_get(): bgpvpnid=%s, kwargs=%s", bgpvpn_id, kwargs)
    bgpvpn = networkclient(request).get_bgpvpn(bgpvpn_id,
                                               **kwargs).to_dict()
    return Bgpvpn(bgpvpn)


def bgpvpn_create(request, **kwargs):
    LOG.debug("bgpvpn_create(): params=%s", kwargs)
    client = networkclient(request)
    bgpvpn = client.create_bgpvpn(**kwargs).to_dict()
    return Bgpvpn(bgpvpn)


def bgpvpn_update(request, bgpvpn_id, **kwargs):
    LOG.debug("bgpvpn_update(): bgpvpnid=%s, kwargs=%s", bgpvpn_id, kwargs)
    bgpvpn = networkclient(request).update_bgpvpn(
        bgpvpn_id, **kwargs).to_dict()
    return Bgpvpn(bgpvpn)


def bgpvpn_delete(request, bgpvpn_id):
    LOG.debug("bgpvpn_delete(): bgpvpnid=%s", bgpvpn_id)
    networkclient(request).delete_bgpvpn(bgpvpn_id)


def network_association_get(request, bgpvpn_id, network_assoc_id, **kwargs):
    LOG.debug("network_association_get(): "
              "bgpvpn_id=%s, network_assoc_id=%s, kwargs=%s",
              bgpvpn_id, network_assoc_id, kwargs)
    network_association = networkclient(
        request).get_bgpvpn_network_association(
            bgpvpn_id, network_assoc_id).to_dict()
    return NetworkAssociation(network_association)


def network_association_list(request, bgpvpn_id, **kwargs):
    LOG.debug("network_association_list(): bgpvpn_id=%s, kwargs=%s",
              bgpvpn_id, kwargs)
    network_associations = networkclient(
        request).bgpvpn_network_associations(bgpvpn_id, **kwargs)
    return [NetworkAssociation(v.to_dict()) for v in network_associations]


def network_association_create(request, bgpvpn_id, **kwargs):
    LOG.debug("network_association_create(): bgpvpnid=%s kwargs=%s",
              bgpvpn_id, kwargs)
    network_association = (
        networkclient(request)
        .create_bgpvpn_network_association(bgpvpn_id, **kwargs).to_dict())
    return NetworkAssociation(network_association)


def network_association_delete(request, resource_id, bgpvpn_id):
    LOG.debug("network_association_delete(): resource_id=%s bgpvpnid=%s",
              resource_id, bgpvpn_id)
    networkclient(request).delete_bgpvpn_network_association(
        bgpvpn_id, resource_id)


def router_association_get(request, bgpvpn_id, router_assoc_id, **kwargs):
    LOG.debug("router_association_get(): "
              "bgpvpn_id=%s, router_assoc_id=%s, kwargs=%s",
              bgpvpn_id, router_assoc_id, kwargs)
    router_association = networkclient(
        request).get_bgpvpn_router_association(
            bgpvpn_id, router_assoc_id).to_dict()
    return RouterAssociation(router_association)


def router_association_list(request, bgpvpn_id, **kwargs):
    LOG.debug("router_association_list(): bgpvpn_id=%s, kwargs=%s",
              bgpvpn_id, kwargs)
    router_associations = networkclient(request).bgpvpn_router_associations(
        bgpvpn_id, **kwargs)
    return [RouterAssociation(v.to_dict()) for v in router_associations]


def router_association_create(request, bgpvpn_id, **kwargs):
    LOG.debug("router_association_create(): bgpvpnid=%s params=%s",
              bgpvpn_id, kwargs)
    router_associations = networkclient(
        request).create_bgpvpn_router_association(
            bgpvpn_id, **kwargs).to_dict()
    return RouterAssociation(router_associations)


def router_association_update(request, bgpvpn_id, router_association_id,
                              **kwargs):
    LOG.debug("router_association_update(): bgpvpnid=%s "
              "router_association_id=%s params=%s", bgpvpn_id,
              router_association_id, kwargs)
    router_associations = networkclient(
        request).update_bgpvpn_router_association(
            bgpvpn_id, router_association_id, **kwargs).to_dict()
    return RouterAssociation(router_associations)


def router_association_delete(request, resource_id, bgpvpn_id):
    LOG.debug("router_association_delete(): resource_id=%s bgpvpnid=%s",
              resource_id, bgpvpn_id)
    networkclient(request).delete_bgpvpn_router_association(
        bgpvpn_id, resource_id)
