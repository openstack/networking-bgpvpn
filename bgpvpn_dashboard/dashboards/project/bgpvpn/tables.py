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

from django.core.urlresolvers import reverse
from django.utils import html
from django.utils.http import urlencode
from django.utils import safestring
from django.utils.translation import ugettext_lazy as _
from horizon import tables


class EditInfoBgpVpn(tables.LinkAction):
    name = "update_info"
    verbose_name = _("Edit BGPVPN")
    url = "horizon:project:bgpvpn:edit"
    classes = ("ajax-modal",)
    icon = "pencil"


class UpdateNetworkAssociations(tables.LinkAction):
    name = "update_network_associations"
    verbose_name = _("Update Network Associations")
    url = "horizon:project:bgpvpn:update-associations"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, bgpvpn):
        step = 'update_bgpvpn_network'
        base_url = reverse(self.url, args=[bgpvpn.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class UpdateRouterAssociations(tables.LinkAction):
    name = "update_router_associations"
    verbose_name = _("Update Router Associations")
    url = "horizon:project:bgpvpn:update-associations"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, bgpvpn):
        step = 'update_bgpvpn_router'
        base_url = reverse(self.url, args=[bgpvpn.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


def get_network_url(network):
    url = reverse('horizon:project:networks:detail', args=[network.id])
    instance = '<a href=%s>%s</a>' % (url, html.escape(network.name_or_id))
    return instance


def get_router_url(router):
    url = reverse('horizon:project:routers:detail', args=[router.id])
    instance = '<a href=%s>%s</a>' % (url, html.escape(router.name_or_id))
    return instance


class NetworksColumn(tables.Column):
    def get_raw_data(self, bgpvpn):
        networks = [get_network_url(network) for network in bgpvpn.networks]
        return safestring.mark_safe(', '.join(networks))


class RoutersColumn(tables.Column):
    def get_raw_data(self, bgpvpn):
        routers = [get_router_url(router) for router in bgpvpn.routers]
        return safestring.mark_safe(', '.join(routers))


class BgpvpnTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link=("horizon:project:bgpvpn:detail"))
    type = tables.Column("type", verbose_name=_("Type"))
    networks = NetworksColumn("networks", verbose_name=_("Networks"))
    routers = RoutersColumn("routers", verbose_name=_("Routers"))

    class Meta(object):
        name = "bgpvpns"
        verbose_name = _("BGPVPN")
        row_actions = (EditInfoBgpVpn,
                       UpdateNetworkAssociations,
                       UpdateRouterAssociations)
