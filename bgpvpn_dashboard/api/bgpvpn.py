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

neutronclient = neutron.neutronclient


class Bgpvpn(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn."""


class NetworkAssociation(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn networks associations."""


class RouterAssociation(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron bgpvpn routers associations."""


def bgpvpns_list(request, **kwargs):
    LOG.debug("bgpvpn_list(): params=%s", kwargs)
    bgpvpns = neutronclient(request).list_bgpvpns(**kwargs).get('bgpvpns')
    return [Bgpvpn(v) for v in bgpvpns]


def bgpvpn_get(request, bgpvpn_id, **kwargs):
    LOG.debug("bgpvpn_get(): bgpvpnid=%s, kwargs=%s", bgpvpn_id, kwargs)
    bgpvpn = neutronclient(request).show_bgpvpn(bgpvpn_id,
                                                **kwargs).get('bgpvpn')
    return Bgpvpn(bgpvpn)


def bgpvpn_create(request, **kwargs):
    LOG.debug("bgpvpn_create(): params=%s", kwargs)
    body = {'bgpvpn': kwargs}
    bgpvpn = neutronclient(request).create_bgpvpn(body=body)
    return Bgpvpn(bgpvpn)


def bgpvpn_update(request, bgpvpn_id, **kwargs):
    LOG.debug("bgpvpn_update(): bgpvpnid=%s, kwargs=%s", bgpvpn_id, kwargs)
    body = {'bgpvpn': kwargs}
    bgpvpn = neutronclient(request).update_bgpvpn(bgpvpn_id,
                                                  body=body).get('bgpvpn')
    return Bgpvpn(bgpvpn)


def bgpvpn_delete(request, bgpvpn_id):
    LOG.debug("bgpvpn_delete(): bgpvpnid=%s", bgpvpn_id)
    neutronclient(request).delete_bgpvpn(bgpvpn_id)


def network_association_list(request, bgpvpn_id, **kwargs):
    LOG.debug("network_association_list(): bgpvpn_id=%s, kwargs=%s",
              bgpvpn_id, kwargs)
    network_associations = neutronclient(
        request).list_network_associations(
        bgpvpn_id,
        **kwargs).get('network_associations')
    return [NetworkAssociation(v) for v in network_associations]


def network_association_create(request, bgpvpn_id, **kwargs):
    LOG.debug("network_association_create(): bgpvpnid=%s kwargs=%s",
              bgpvpn_id, kwargs)
    body = {'network_association': kwargs}
    network_association = neutronclient(
        request).create_network_association(bgpvpn_id, body=body)
    return NetworkAssociation(network_association)


def network_association_delete(request, resource_id, bgpvpn_id):
    LOG.debug("router_association_delete(): resource_id=%s bgpvpnid=%s",
              resource_id, bgpvpn_id)
    neutronclient(request).delete_network_association(resource_id, bgpvpn_id)


def router_association_list(request, bgpvpn_id, **kwargs):
    LOG.debug("router_association_list(): bgpvpn_id=%s, kwargs=%s",
              bgpvpn_id, kwargs)
    router_associations = neutronclient(
        request).list_router_associations(bgpvpn_id,
                                          **kwargs).get('router_associations')
    return [RouterAssociation(v) for v in router_associations]


def router_association_create(request, bgpvpn_id, **kwargs):
    LOG.debug("router_association_create(): bgpvpnid=%s params=%s",
              bgpvpn_id, kwargs)
    body = {'router_association': kwargs}
    router_associations = neutronclient(
        request).create_router_association(bgpvpn_id, body=body)
    return RouterAssociation(router_associations)


def router_association_delete(request, resource_id, bgpvpn_id):
    LOG.debug("router_association_delete(): resource_id=%s bgpvpnid=%s",
              resource_id, bgpvpn_id)
    neutronclient(request).delete_router_association(resource_id, bgpvpn_id)
