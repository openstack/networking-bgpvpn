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

from bgpvpn_dashboard.dashboards.project.bgpvpn.router_associations \
    import tables as router_tables


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/bgpvpn/router_associations/_detail_overview.html"

    def get_context_data(self, request):
        router_association = self.tab_group.kwargs['router_association']
        router = self.get_router(router_association.router_id)
        router_association.router_name = router.get('name')
        router_association.router_url = self.get_router_detail_url(
            router_association.router_id)
        return {'router_association': router_association}

    @memoized.memoized_method
    def get_router(self, router_id):
        try:
            router = api.neutron.router_get(self.request, router_id)
        except Exception:
            router = {}
            msg = _('Unable to retrieve router details.')
            exceptions.handle(self.request, msg)

        return router

    @staticmethod
    def get_router_detail_url(router_id):
        return reverse('horizon:project:routers:detail', args=(router_id,))


class RouterAssociationsTab(tabs.TableTab):
    name = _("Router Associations")
    slug = "router_associations_tab"
    table_classes = (router_tables.RouterAssociationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_router_associations_data(self):
        try:
            bgpvpn_id = self.tab_group.kwargs['bgpvpn_id']
            router_associations = bgpvpn_api.router_association_list(
                self.request, bgpvpn_id)
            for router_asso in router_associations:
                router = api.neutron.router_get(self.request,
                                                router_asso.router_id)
                router_asso.router_name = router.name
        except Exception:
            router_associations = []
            msg = _('Router associations list can not be retrieved.')
            exceptions.handle(self.request, msg)
        return router_associations


class RouterAssociationDetailTabs(tabs.TabGroup):
    slug = "router_association_details"
    tabs = (OverviewTab,)
