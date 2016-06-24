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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import forms
from horizon.utils import memoized
from openstack_dashboard import api

import bgpvpn_dashboard.api.bgpvpn as bgpvpn_api
from bgpvpn_dashboard.dashboards.admin.bgpvpn import forms as bgpvpn_forms
from bgpvpn_dashboard.dashboards.admin.bgpvpn import tables as bgpvpn_tables
from bgpvpn_dashboard.dashboards.admin.bgpvpn import workflows \
    as bgpvpn_workflows
from bgpvpn_dashboard.dashboards.project.bgpvpn import views as project_views


class IndexView(project_views.IndexView):
    table_class = bgpvpn_tables.BgpvpnTable

    @memoized.memoized_method
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


class EditDataView(project_views.EditDataView):
    form_class = bgpvpn_forms.EditDataBgpVpn
    submit_url = 'horizon:admin:bgpvpn:edit'
    success_url = reverse_lazy('horizon:admin:bgpvpn:index')


class UpdateAssociationsView(project_views.UpdateAssociationsView):
    workflow_class = bgpvpn_workflows.UpdateBgpVpnAssociations
    page_title = _("Edit BGPVPN associations")
    failure_url = reverse_lazy("horizon:admin:bgpvpn:index")


class DetailProjectView(project_views.DetailProjectView):
    template_name = 'admin/bgpvpn/detail.html'
    redirect_url = 'horizon:admin:bgpvpn:index'
