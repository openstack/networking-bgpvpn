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
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized
from horizon import views
from horizon import workflows
from openstack_dashboard import api

import bgpvpn_dashboard.api.bgpvpn as bgpvpn_api
from bgpvpn_dashboard.common import bgpvpn as bgpvpn_common
from bgpvpn_dashboard.dashboards.admin.bgpvpn import forms as bgpvpn_forms
from bgpvpn_dashboard.dashboards.admin.bgpvpn import tables as bgpvpn_tables
from bgpvpn_dashboard.dashboards.admin.bgpvpn import workflows \
    as bgpvpn_workflows


class IndexView(tables.DataTableView):
    table_class = bgpvpn_tables.BgpvpnTable
    template_name = 'admin/bgpvpn/index.html'
    page_title = _("BGP VPNs")

    def get_data(self):
        bgpvpns = bgpvpn_api.bgpvpns_list(self.request)
        networks = api.neutron.network_list(self.request)
        routers = api.neutron.router_list(self.request)
        for bgpvpn in bgpvpns:
            networks_list = [network for network in networks
                             if network.id in bgpvpn.networks]
            routers_list = [router for router in routers
                            if router.id in bgpvpn.routers]
            bgpvpn.tenant = api.keystone.tenant_get(self.request,
                                                    bgpvpn.tenant_id)
            bgpvpn.networks = networks_list
            bgpvpn.routers = routers_list

        return bgpvpns


class CreateView(forms.ModalFormView):
    form_class = bgpvpn_forms.CreateBgpVpn
    template_name = 'admin/bgpvpn/create.html'
    success_url = reverse_lazy('horizon:admin:bgpvpn:index')
    page_title = _("Create BGPVPN")


class EditDataView(forms.ModalFormView):
    form_class = bgpvpn_forms.EditDataBgpVpn
    form_id = "edit_data_bgpvpn_form"
    modal_header = _("Edit BGPVPN")
    submit_label = _("Save Changes")
    submit_url = 'horizon:admin:bgpvpn:edit'
    success_url = reverse_lazy('horizon:admin:bgpvpn:index')
    template_name = 'admin/bgpvpn/modify.html'
    page_title = _("Edit BGPVPN")

    @staticmethod
    def _join_rts(route_targets_list):
        return ','.join(route_targets_list)

    def get_context_data(self, **kwargs):
        context = super(EditDataView, self).get_context_data(**kwargs)
        args = (self.kwargs['bgpvpn_id'],)
        context["bgpvpn_id"] = self.kwargs['bgpvpn_id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        bgpvpn_id = self.kwargs['bgpvpn_id']
        try:
            # Get initial bgpvpn information
            bgpvpn = bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve BGPVPN details.'),
                redirect=reverse_lazy("horizon:project:bgpvpn:index"))
        data = bgpvpn.to_dict()
        for attribute in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
            data[attribute] = self._join_rts(bgpvpn[attribute])
        data['bgpvpn_id'] = data.pop('id')
        return data


class UpdateAssociationsView(workflows.WorkflowView):
    workflow_class = bgpvpn_workflows.UpdateBgpVpnAssociations
    template_name = 'admin/bgpvpn/update-associations.html'
    page_title = _("Edit BGPVPN associations")

    def get_initial(self):
        bgpvpn_id = self.kwargs['bgpvpn_id']

        try:
            # Get initial bgpvpn information
            bgpvpn = bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve BGPVPN details.'),
                redirect=reverse_lazy("horizon:admin:bgpvpn:index"))
        data = bgpvpn.to_dict()
        data['bgpvpn_id'] = data.pop('id')
        return data


class DetailProjectView(views.HorizonTemplateView):
    template_name = 'admin/bgpvpn/detail.html'
    page_title = "{{ bgpvpn.name }}"

    def get_context_data(self, **kwargs):
        context = super(DetailProjectView, self).get_context_data(**kwargs)
        bgpvpn = self.get_data()
        table = bgpvpn_tables.BgpvpnTable(self.request)
        context["bgpvpn"] = bgpvpn
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(bgpvpn)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            bgpvpn_id = self.kwargs['bgpvpn_id']
            bgpvpn = bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve BGPVPN details.'),
                              redirect=redirect)
        return bgpvpn

    def get_redirect_url(self):
        return reverse('horizon:admin:bgpvpn:index')
