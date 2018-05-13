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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations \
    import tables as network_tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/bgpvpn/network_associations/_detail_overview.html"

    def get_context_data(self, request):
        network_association = self.tab_group.kwargs['network_association']
        network = self.get_network(network_association.network_id)
        network_association.network_name = network.get('name')
        network_association.network_url = self.get_network_detail_url(
            network_association.network_id)
        return {'network_association': network_association}

    @memoized.memoized_method
    def get_network(self, network_id):
        try:
            network = api.neutron.network_get(self.request, network_id)
        except Exception:
            network = {}
            msg = _('Unable to retrieve network details.')
            exceptions.handle(self.request, msg)

        return network

    @staticmethod
    def get_network_detail_url(network_id):
        return reverse('horizon:project:networks:detail', args=(network_id,))


class NetworkAssociationsTab(tabs.TableTab):
    name = _("Network Associations")
    slug = "network_associations_tab"
    table_classes = (network_tables.NetworkAssociationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_network_associations_data(self):
        try:
            bgpvpn_id = self.tab_group.kwargs['bgpvpn_id']
            network_associations = bgpvpn_api.network_association_list(
                self.request, bgpvpn_id)
            for network_asso in network_associations:
                network = api.neutron.network_get(self.request,
                                                  network_asso.network_id)
                network_asso.network_name = network.name
        except Exception:
            network_associations = []
            msg = _('Network associations list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return network_associations


class NetworkAssociationDetailTabs(tabs.TabGroup):
    slug = "network_association_details"
    tabs = (OverviewTab,)
