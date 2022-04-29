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

from django.urls import re_path

from bgpvpn_dashboard.dashboards.project.bgpvpn.network_associations \
    import views as bgpvpn_network_associations_views

NETWORK_ASSO = r'^(?P<bgpvpn_id>[^/]+)/network_assos/' \
               r'(?P<network_association_id>[^/]+)/%s$'

urlpatterns = [
    re_path(NETWORK_ASSO % 'detail',
            bgpvpn_network_associations_views.DetailView.as_view(),
            name='detail'),
]
