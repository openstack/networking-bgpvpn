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

import bgpvpn_dashboard.api.bgpvpn as bgpvpn_api

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations \
    import tabs as network_tabs
from bgpvpn_dashboard.dashboards.project.bgpvpn.router_associations \
    import tabs as router_tabs


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("project/bgpvpn/_detail_overview.html")
    preload = False

    def _get_data(self):
        bgpvpn = {}
        bgpvpn_id = None
        try:
            bgpvpn_id = self.tab_group.kwargs['bgpvpn_id']
            bgpvpn = bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
            bgpvpn.set_id_as_name_if_empty(length=0)
        except Exception:
            msg = _('Unable to retrieve details for bgpvpn "%s".') % (
                bgpvpn_id)
            exceptions.handle(self.request, msg)
        return bgpvpn

    def get_context_data(self, request, **kwargs):
        context = super(OverviewTab, self).get_context_data(request, **kwargs)
        bgpvpn = self._get_data()
        context["bgpvpn"] = bgpvpn
        return context


class BgpvpnDetailsTabs(tabs.DetailTabsGroup):
    slug = "bgpvpn_tabs"
    tabs = (OverviewTab,
            network_tabs.NetworkAssociationsTab,
            router_tabs.RouterAssociationsTab)
    sticky = True
