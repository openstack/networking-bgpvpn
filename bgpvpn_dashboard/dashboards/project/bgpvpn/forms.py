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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import messages

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

    def clean(self):
        cleaned_data = super(CommonData, self).clean()
        name = cleaned_data.get('name')
        bgpvpn_id = cleaned_data.get('bgpvpn_id')
        try:
            if self.request.user.is_superuser:
                for attribute in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
                    if not cleaned_data.get(attribute):
                        cleaned_data[attribute] = None
                # if an admin user use the bgpvpn panel project
                # tenant_id field doesn't exist
                if not cleaned_data.get('tenant_id'):
                    tenant_id = self.request.user.tenant_id
                else:
                    tenant_id = cleaned_data.get('tenant_id')
                bgpvpns = bgpvpn_api.bgpvpns_list(self.request,
                                                  name=name,
                                                  tenant_id=tenant_id)
            else:
                bgpvpns = bgpvpn_api.bgpvpns_list(self.request,
                                                  name=name)
        except Exception:
            msg = _('Unable to get BGPVPN with name %s') % name
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        if bgpvpns:
            if self.action == 'update':
                for bgpvpn in bgpvpns:
                    if bgpvpn.id != bgpvpn_id:
                        raise forms.ValidationError(
                            _('The name "%s" is already '
                              'used by another BGPVPN.') % name)
            else:
                raise forms.ValidationError(
                    _('The name "%s" is already '
                      'used by another BGPVPN.') % name)
        return cleaned_data

    @staticmethod
    def _del_attributes(attributes, data):
        for attribute in attributes:
            del data[attribute]

    def handle(self, request, data):
        params = {}
        if request.user.is_superuser:
            for key in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
                params[key] = bgpvpn_common.format_rt(data.pop(key))
        params.update(data)
        try:
            if self.action == 'update':
                if request.user.is_superuser and data.get('tenant_id'):
                    attributes = ('bgpvpn_id', 'type', 'tenant_id')
                else:
                    attributes = ('bgpvpn_id', 'type')
                self._del_attributes(attributes, params)
                bgpvpn = bgpvpn_api.bgpvpn_update(request,
                                                  data['bgpvpn_id'],
                                                  **params)
                success_action = 'modified'
            elif self.action == 'create':
                success_action = 'created'
                bgpvpn = bgpvpn_api.bgpvpn_create(request, **params)
            else:
                raise Exception(
                    'Action type %s is not supported' % self.action)
            msg = _('BGPVPN {name} was successfully {action}.').format(
                name=data['name'],
                action=success_action)
            LOG.debug(msg)
            messages.success(request, msg)
            return bgpvpn
        except Exception:
            msg = _('Failed to {action} BGPVPN {name}').format(
                action=self.action,
                name=data['name'])
            exceptions.handle(request, msg, redirect=self.failure_url)
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
