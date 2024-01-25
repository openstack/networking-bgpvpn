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
#
import collections
import logging

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.common import bgpvpn as bgpvpn_common

LOG = logging.getLogger(__name__)


class CommonData(forms.SelfHandlingForm):
    fields_order = []
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)

    failure_url = reverse_lazy('horizon:project:bgpvpn:index')

    def __init__(self, request, *args, **kwargs):
        super(CommonData, self).__init__(request, *args, **kwargs)
        if 'keyOrder' in self.fields:
            self.fields.keyOrder = self.fields_order
        else:
            self.fields = collections.OrderedDict(
                (k, self.fields[k]) for k in self.fields_order)

    @staticmethod
    def _del_attributes(attributes, data):
        for attribute in attributes:
            del data[attribute]

    def handle(self, request, data):
        params = {}
        for key in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
            if key in data:
                params[key] = bgpvpn_common.format_rt(data.pop(key, None))
        params.update(data)
        error_msg = _('Something went wrong with BGPVPN %s') % data['name']
        try:
            if self.action == 'update':
                error_msg = _('Failed to update BGPVPN %s') % data['name']
                # attribute tenant_id is required in request when admin user is
                # logged and bgpvpn form from admin menu is used
                if request.user.is_superuser and data.get('tenant_id'):
                    attributes = ('bgpvpn_id', 'type', 'tenant_id')
                # attribute tenant_id does not exist in request
                # when non-admin user is logged
                else:
                    attributes = ('bgpvpn_id', 'type')
                self._del_attributes(attributes, params)
                bgpvpn = bgpvpn_api.bgpvpn_update(request,
                                                  data['bgpvpn_id'],
                                                  **params)
                msg = _('BGPVPN %s was successfully updated.') % data['name']
            elif self.action == 'create':
                error_msg = _('Failed to create BGPVPN %s') % data['name']
                bgpvpn = bgpvpn_api.bgpvpn_create(request, **params)
                msg = _('BGPVPN %s was successfully created.') % data['name']
            else:
                raise Exception(
                    _('Unsupported action type: %s') % self.action)
            LOG.debug(msg)
            messages.success(request, msg)
            return bgpvpn
        except Exception:
            exceptions.handle(request, error_msg, redirect=self.failure_url)
            return False


class EditDataBgpVpn(CommonData):
    bgpvpn_id = forms.CharField(label=_("ID"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    type = forms.CharField(label=_("Type"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    fields_order = ['name', 'bgpvpn_id', 'type']

    def __init__(self, request, *args, **kwargs):
        super(EditDataBgpVpn, self).__init__(request, *args, **kwargs)
        self.action = 'update'


class CreateNetworkAssociation(forms.SelfHandlingForm):
    bgpvpn_id = forms.CharField(widget=forms.HiddenInput())
    network_resource = forms.ChoiceField(
        label=_("Associate Network"),
        widget=forms.ThemableSelectWidget(
            data_attrs=('name', 'id'),
            transform=lambda x: "%s" % x.name_or_id))

    def __init__(self, request, *args, **kwargs):
        super(CreateNetworkAssociation, self).__init__(
            request, *args, **kwargs)

        # when an admin user uses the project panel BGPVPN, there is no
        # project in data because bgpvpn_get doesn't return it
        project_id = kwargs.get('initial', {}).get("project_id", None)
        if request.user.is_superuser and project_id:
            tenant_id = project_id
        else:
            tenant_id = self.request.user.tenant_id

        try:
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
            if networks:
                choices = [('', _("Choose a network"))] + [(n.id, n) for n in
                                                           networks]
                self.fields['network_resource'].choices = choices
            else:
                self.fields['network_resource'].choices = [('',
                                                            _("No network"))]
        except Exception:
            exceptions.handle(
                request, _("Unable to retrieve networks."))

    def handle(self, request, data):
        try:
            params = self._set_params(data)
            bgpvpn_api.network_association_create(
                request, data['bgpvpn_id'], **params)
            return True
        except Exception:
            exceptions.handle(request, (_('Unable to associate network "%s".')
                                        % data["network_resource"]))
            return False

    def _set_params(self, data):
        params = dict()
        params['network_id'] = data['network_resource']
        return params
