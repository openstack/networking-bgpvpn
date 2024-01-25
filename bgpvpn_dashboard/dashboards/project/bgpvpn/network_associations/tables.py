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

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

LOG = logging.getLogger(__name__)


class DeleteNetworkAssociation(tables.DeleteAction):

    @staticmethod
    def action_present(count):
        return ngettext_lazy(u"Delete Network Association",
                             u"Delete Network Associations",
                             count)

    @staticmethod
    def action_past(count):
        return ngettext_lazy(u"Deleted Network Association",
                             u"Deleted Network Associations",
                             count)

    def delete(self, request, asso_id):
        try:
            bgpvpn_api.network_association_delete(
                request, asso_id, self.table.kwargs['bgpvpn_id'])
        except Exception:
            msg = _('Failed to delete Network Association %s') % asso_id
            LOG.info(msg)
            redirect = reverse('horizon:project:bgpvpn:detail')
            exceptions.handle(request, msg, redirect=redirect)


class CreateNetworkAssociation(tables.LinkAction):
    name = "create_network_association"
    verbose_name = _("Create Network Association")
    url = "horizon:project:bgpvpn:create-network-association"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, datum=None):
        bgpvpn_id = self.table.kwargs['bgpvpn_id']
        return reverse(self.url, args=(bgpvpn_id,))


class IDColumn(tables.Column):
    url = "horizon:project:bgpvpn:network_assos:detail"

    def get_link_url(self, asso):
        bgpvpn_id = self.table.kwargs['bgpvpn_id']
        return reverse(self.url, args=(bgpvpn_id, asso.id))


class NetworkColumn(tables.Column):
    def get_raw_data(self, asso):
        url = reverse('horizon:project:networks:detail',
                      args=[asso.network_id])
        instance = '<a href=%s>%s</a>' % (url,
                                          asso.network_name or asso.network_id)
        return safestring.mark_safe(instance)


class NetworkAssociationsTable(tables.DataTable):
    id = IDColumn("id", verbose_name=_("Association ID"),
                  link='horizon:project:bgpvpn:network_assos:detail')
    network = NetworkColumn("network_id", verbose_name=_("Network"))

    failure_url = reverse_lazy('horizon:project:bgpvpn:detail')

    class Meta(object):
        name = "network_associations"
        verbose_name = _("Network Associations")
        table_actions = (CreateNetworkAssociation,)
        row_actions = (DeleteNetworkAssociation,)
        hidden_title = False

    def get_object_display(self, asso):
        return asso.id
