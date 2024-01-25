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
#
import logging

from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms


from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

LOG = logging.getLogger(__name__)


class UpdateRouterAssociation(forms.SelfHandlingForm):
    bgpvpn_id = forms.CharField(widget=forms.HiddenInput())
    router_association_id = forms.CharField(
        label=_("ID"), widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    router_id = forms.CharField(
        label=_("Router"),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    advertise_extra_routes = forms.BooleanField(
        label=_("Advertise Extra Routes"),
        initial=True,
        required=False,
        help_text="Boolean flag controlling whether or not the routes "
                  "specified in the routes attribute of the router will be "
                  "advertised to the BGPVPN (default: true).")

    def __init__(self, request, *args, **kwargs):
        super(UpdateRouterAssociation, self).__init__(request, *args, **kwargs)
        self.action = 'update'

    def handle(self, request, data):
        router_association_id = data['router_association_id']
        bgpvpn_id = data['bgpvpn_id']
        try:
            bgpvpn_api.router_association_update(
                request, bgpvpn_id, router_association_id,
                advertise_extra_routes=data['advertise_extra_routes'])
            return True
        except exceptions as e:
            exceptions.handle(
                request,
                "Unable to update bgpvpn router association %s:" % str(e))
            return False
