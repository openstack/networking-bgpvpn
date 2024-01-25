# Copyright (c) 2017 Orange.
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
from django.urls import reverse_lazy
from django.utils import safestring
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

LOG = logging.getLogger(__name__)


class DeleteRouterAssociation(tables.DeleteAction):

    @staticmethod
    def action_present(count):
        return ngettext_lazy(u"Delete Router Association",
                             u"Delete Router Associations",
                             count)

    @staticmethod
    def action_past(count):
        return ngettext_lazy(u"Deleted Router Association",
                             u"Deleted Router Associations",
                             count)

    def delete(self, request, asso_id):
        try:
            bgpvpn_api.router_association_delete(
                request, asso_id, self.table.kwargs['bgpvpn_id'])
        except Exception:
            msg = _('Failed to delete Router Association %s') % asso_id
            LOG.info(msg)
            redirect = reverse('horizon:project:bgpvpn:detail')
            exceptions.handle(request, msg, redirect=redirect)


class UpdateRouterAssociation(tables.LinkAction):
    name = "update"
    verbose_name = _("Update Router Association")
    url = "horizon:project:bgpvpn:update-router-association"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, asso):
        bgpvpn_id = self.table.kwargs['bgpvpn_id']
        return reverse(self.url, args=(bgpvpn_id, asso.id))

    def allowed(self, request, datum=None):
        if api.neutron.is_extension_supported(request,
                                              'bgpvpn-routes-control'):
            return True


class CreateRouterAssociation(tables.LinkAction):
    name = "create_router_association"
    verbose_name = _("Create Router Association")
    url = "horizon:project:bgpvpn:create-router-association"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, datum=None):
        bgpvpn_id = self.table.kwargs['bgpvpn_id']
        return reverse(self.url, args=(bgpvpn_id,))


class IDColumn(tables.Column):
    url = "horizon:project:bgpvpn:router_assos:detail"

    def get_link_url(self, asso):
        bgpvpn_id = self.table.kwargs['bgpvpn_id']
        return reverse(self.url, args=(bgpvpn_id, asso.id))


class RouterColumn(tables.Column):
    def get_raw_data(self, asso):
        url = reverse('horizon:project:routers:detail', args=[asso.router_id])
        instance = '<a href=%s>%s</a>' % (url,
                                          asso.router_name or asso.router_id)
        return safestring.mark_safe(instance)


class RouterAssociationsTable(tables.DataTable):
    id = IDColumn("id", verbose_name=_("Association ID"),
                  link='horizon:project:bgpvpn:router_assos:detail')
    router = RouterColumn("router_id", verbose_name=_("Router"))
    failure_url = reverse_lazy('horizon:project:bgpvpn:detail')

    class Meta(object):
        name = "router_associations"
        verbose_name = _("Router Associations")
        table_actions = (CreateRouterAssociation, DeleteRouterAssociation)
        row_actions = (UpdateRouterAssociation, DeleteRouterAssociation,)
        hidden_title = False

    def get_object_display(self, asso):
        return asso.id
