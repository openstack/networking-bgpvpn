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

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows
from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.common import bgpvpn as bgpvpn_common
from bgpvpn_dashboard.dashboards.project.bgpvpn import forms as bgpvpn_forms
from bgpvpn_dashboard.dashboards.project.bgpvpn import tables as bgpvpn_tables
from bgpvpn_dashboard.dashboards.project.bgpvpn import tabs as bgpvpn_tabs
from bgpvpn_dashboard.dashboards.project.bgpvpn import workflows \
    as bgpvpn_workflows


class IndexView(tables.DataTableView):
    table_class = bgpvpn_tables.BgpvpnTable
    template_name = 'project/bgpvpn/index.html'
    page_title = _("BGP VPNs")

    @memoized.memoized_method
    def get_data(self):
        tenant_id = self.request.user.tenant_id
        bgpvpns_list = bgpvpn_api.bgpvpns_list(
            self.request, tenant_id=tenant_id)
        for bgpvpn in bgpvpns_list:
            bgpvpn.networks = [api.neutron.network_get(
                self.request, id, expand_subnet=False)
                for id in bgpvpn.networks]
            bgpvpn.routers = [api.neutron.router_get(self.request, id)
                              for id in bgpvpn.routers]
        return bgpvpns_list


class EditDataView(forms.ModalFormView):
    form_class = bgpvpn_forms.EditDataBgpVpn
    form_id = "edit_data_bgpvpn_form"
    modal_header = _("Edit BGPVPN")
    submit_label = _("Update Change")
    submit_url = 'horizon:project:bgpvpn:edit'
    success_url = reverse_lazy('horizon:project:bgpvpn:index')
    template_name = 'project/bgpvpn/modify.html'
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
                redirect=self.success_url)
        else:
            data = bgpvpn.to_dict()
            if self.request.user.is_superuser:
                for attribute in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
                    data[attribute] = self._join_rts(bgpvpn[attribute])
            data['bgpvpn_id'] = data.pop('id')
            return data


class GetBgpvpnMixin(object):
    def get_initial(self):
        bgpvpn_id = self.kwargs['bgpvpn_id']
        try:
            # Get initial bgpvpn information
            bgpvpn = bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
            data = bgpvpn.to_dict()
            data['bgpvpn_id'] = data.pop('id')
            return data
        except Exception:
            exceptions.handle(
                self.request,
                _('Unable to retrieve BGPVPN details.'),
                redirect=self.success_url)


class CreateNetworkAssociationView(GetBgpvpnMixin, forms.ModalFormView):
    form_class = bgpvpn_forms.CreateNetworkAssociation
    form_id = "create_network_association_form"
    modal_header = _("Create Network Association")
    submit_label = _("Create")
    submit_url = 'horizon:project:bgpvpn:create-network-association'
    success_url = reverse_lazy('horizon:project:bgpvpn:index')
    template_name = 'project/bgpvpn/create_network_association.html'
    page_title = _("Create Network Association")

    def get_context_data(self, **kwargs):
        context = super(
            CreateNetworkAssociationView, self).get_context_data(**kwargs)
        args = (self.kwargs['bgpvpn_id'],)
        context["bgpvpn_id"] = self.kwargs['bgpvpn_id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context


class CreateRouterAssociationView(GetBgpvpnMixin, workflows.WorkflowView):
    workflow_class = bgpvpn_workflows.RouterAssociation
    page_title = _("Create Router associations")
    failure_url = reverse_lazy("horizon:project:bgpvpn:index")


class DetailProjectView(tabs.TabbedTableView):
    tab_group_class = bgpvpn_tabs.BgpvpnDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ bgpvpn.name }}"
    redirect_url = 'horizon:project:bgpvpn:index'

    def get_context_data(self, **kwargs):
        context = super(DetailProjectView, self).get_context_data(**kwargs)
        bgpvpn = self.get_data()
        table = bgpvpn_tables.BgpvpnTable(self.request)
        context["bgpvpn"] = bgpvpn
        context["url"] = reverse(self.redirect_url)
        context["actions"] = table.render_row_actions(bgpvpn)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            bgpvpn_id = self.kwargs['bgpvpn_id']
            return bgpvpn_api.bgpvpn_get(self.request, bgpvpn_id)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve BGPVPN details.'),
                              redirect=reverse(self.redirect_url))
