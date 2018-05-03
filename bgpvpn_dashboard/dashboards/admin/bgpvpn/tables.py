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

from django.urls import reverse
from django.utils import html
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from horizon import exceptions
from horizon import tables
from openstack_dashboard import policy

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.project.bgpvpn import tables as project_tables

LOG = logging.getLogger(__name__)


class DeleteBgpvpn(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(u"Delete BGPVPN",
                              u"Delete BGPVPNs",
                              count)

    @staticmethod
    def action_past(count):
        return ungettext_lazy(u"Deleted BGPVPN",
                              u"Deleted BGPVPNs",
                              count)

    def delete(self, request, obj_id):
        try:
            bgpvpn_api.bgpvpn_delete(request, obj_id)
        except Exception:
            msg = _('Failed to delete BGPVPN %s') % obj_id
            LOG.info(msg)
            redirect = reverse('horizon:admin:bgpvpn:index')
            exceptions.handle(request, msg, redirect=redirect)


class CreateBgpVpn(tables.LinkAction):
    name = "create"
    verbose_name = _("Create BGPVPN")
    url = "horizon:admin:bgpvpn:create"
    classes = ("ajax-modal",)
    icon = "plus"


class EditInfoBgpVpn(project_tables.EditInfoBgpVpn):
    url = "horizon:admin:bgpvpn:edit"


class CreateNetworkAssociation(project_tables.CreateNetworkAssociation):
    url = "horizon:admin:bgpvpn:create-network-association"


class CreateRouterAssociation(project_tables.CreateRouterAssociation):
    url = "horizon:admin:bgpvpn:create-router-association"


def get_route_targets(bgpvpn):
    return ', '.join(rt for rt in bgpvpn.route_targets)


def get_import_targets(bgpvpn):
    return ', '.join(it for it in bgpvpn.import_targets)


def get_export_targets(bgpvpn):
    return ', '.join(et for et in bgpvpn.export_targets)


def get_network_url(network):
    url = reverse('horizon:admin:networks:detail', args=[network.id])
    instance = '<a href=%s>%s</a>' % (url, html.escape(network.name_or_id))
    return instance


def get_router_url(router):
    url = reverse('horizon:admin:routers:detail', args=[router.id])
    instance = '<a href=%s>%s</a>' % (url, html.escape(router.name_or_id))
    return instance


class BgpvpnTable(project_tables.BgpvpnTable):
    route_targets = tables.Column(get_route_targets,
                                  verbose_name=_("Route Targets"))
    import_targets = tables.Column(get_import_targets,
                                   verbose_name=_("Import Targets"))
    export_targets = tables.Column(get_export_targets,
                                   verbose_name=_("Export Targets"))

    class Meta(object):
        table_actions = (CreateBgpVpn, DeleteBgpvpn)
        row_actions = (EditInfoBgpVpn,
                       CreateNetworkAssociation,
                       CreateRouterAssociation,
                       DeleteBgpvpn)
        columns = ("tenant_id", "name", "type", "route_targets",
                   "import_targets", "export_targets", "networks", "routers")
