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

from django.conf.urls import url

import bgpvpn_dashboard.dashboards.admin.bgpvpn.views as bgpvpn_views

BGPVPN = r'^(?P<bgpvpn_id>[^/]+)/%s$'

urlpatterns = [
    url(r'^$', bgpvpn_views.IndexView.as_view(), name='index'),
    url(r'^create/$', bgpvpn_views.CreateView.as_view(), name='create'),
    url(BGPVPN % 'edit', bgpvpn_views.EditDataView.as_view(), name='edit'),
    url(BGPVPN % 'create-network-association',
        bgpvpn_views.CreateNetworkAssociationView.as_view(),
        name='create-network-association'),
    url(BGPVPN % 'create-router-association',
        bgpvpn_views.CreateRouterAssociationView.as_view(),
        name='create-router-association'),
    url(r'^(?P<bgpvpn_id>[^/]+)/detail/$',
        bgpvpn_views.DetailProjectView.as_view(), name='detail'),
]
