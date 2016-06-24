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

from bgpvpn_dashboard.dashboards.project.bgpvpn import workflows \
    as project_workflows


class UpdateBgpVpnRouters(project_workflows.UpdateBgpVpnRouters):
    action_class = project_workflows.UpdateBgpVpnRoutersAction
    depends_on = ("bgpvpn_id", "tenant_id", "name")


class UpdateBgpVpnNetworks(project_workflows.UpdateBgpVpnNetworks):
    action_class = project_workflows.UpdateBgpVpnNetworksAction
    depends_on = ("bgpvpn_id", "tenant_id", "name")


class UpdateBgpVpnAssociations(project_workflows.UpdateBgpVpnAssociations):
    success_url = "horizon:admin:bgpvpn:index"
    default_steps = (UpdateBgpVpnNetworks,
                     UpdateBgpVpnRouters)

    def _set_params(self, data, association_type, resource):
        params = super(
            UpdateBgpVpnAssociations, self)._set_params(data,
                                                        association_type,
                                                        resource)
        params['tenant_id'] = data['tenant_id']
        return params
