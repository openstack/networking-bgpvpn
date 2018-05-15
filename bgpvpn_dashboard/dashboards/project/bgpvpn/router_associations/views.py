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
from horizon import forms
from horizon import tabs

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

from bgpvpn_dashboard.dashboards.project.bgpvpn.router_associations \
    import forms as bgpvpn_router_associations_forms
from bgpvpn_dashboard.dashboards.project.bgpvpn.router_associations \
    import tabs as project_tabs


class UpdateRouterAssociationsView(forms.ModalFormView):
    form_class = bgpvpn_router_associations_forms.UpdateRouterAssociation
    form_id = "update_router_association_form"
    modal_header = _("Update BGPVPN Router Associations")
    submit_label = _("Update")
    submit_url = 'horizon:project:bgpvpn:update-router-association'
    template_name = 'project/bgpvpn/router_associations/modify.html'
    page_title = _("Update BGPVPN Router Association")
    url = 'horizon:project:bgpvpn:detail'

    def get_success_url(self):
        return reverse(self.url, args=(self.kwargs['bgpvpn_id'],))

    def get_context_data(self, **kwargs):
        context = super(
            UpdateRouterAssociationsView, self).get_context_data(**kwargs)
        args = (self.kwargs['bgpvpn_id'], self.kwargs['router_association_id'])
        context["bgpvpn_id"] = self.kwargs['bgpvpn_id']
        context["router_association_id"] = self.kwargs['router_association_id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        bgpvpn_id = self.kwargs['bgpvpn_id']
        router_association_id = self.kwargs['router_association_id']
        try:
            router_association = bgpvpn_api.router_association_get(
                self.request, bgpvpn_id, router_association_id)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve Router Association details.'),
                redirect=self.success_url)
        else:
            data = router_association.to_dict()
            data['router_association_id'] = data.pop('id')
            data['bgpvpn_id'] = bgpvpn_id
            return data


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.RouterAssociationDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ router_association.id }}"

    def get_data(self):
        router_association_id = self.kwargs['router_association_id']
        bgpvpn_id = self.kwargs['bgpvpn_id']
        try:
            router_association = bgpvpn_api.router_association_get(
                self.request, bgpvpn_id, router_association_id)
            return router_association
        except Exception:
            router_association = []
            msg = _('Unable to retrieve router association details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        return router_association

    def get_tabs(self, request, *args, **kwargs):
        router_association = self.get_data()
        return self.tab_group_class(
            request, router_association=router_association, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse('horizon:project:bgpvpn:index')
