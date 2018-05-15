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

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations \
    import tabs as project_tabs


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.NetworkAssociationDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ network_association.id }}"

    def get_data(self):
        network_association_id = self.kwargs['network_association_id']
        bgpvpn_id = self.kwargs['bgpvpn_id']
        try:
            network_association = bgpvpn_api.network_association_get(
                self.request, bgpvpn_id, network_association_id)
            return network_association
        except Exception:
            network_association = []
            msg = _('Unable to retrieve network association details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return network_association

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        network_association = self.get_data()
        context["url"] = reverse(
            "horizon:project:bgpvpn:network_associations_tab",
            args=(self.kwargs["bgpvpn_id"], network_association.id))
        return context

    def get_tabs(self, request, *args, **kwargs):
        network_association = self.get_data()
        return self.tab_group_class(
            request, network_association=network_association, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:bgpvpn:index')
