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

import collections
import logging

from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api
from bgpvpn_dashboard.common import bgpvpn as bgpvpn_common
from networking_bgpvpn.neutron.services.common import constants

LOG = logging.getLogger(__name__)


RT_REGEX = constants.RT_REGEX[1:-1]
RTS_REGEX = '^%s( *, *%s)*$' % (RT_REGEX, RT_REGEX)


class BgpvpnAttributes(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=False)

    route_targets = forms.CharField(
        max_length=255,
        validators=[RegexValidator(regex=RTS_REGEX,
                                   message=_("Route targets is not valid"))],
        label=_("Route targets"),
        required=False,
        help_text=bgpvpn_common.ROUTE_TARGET_HELP)

    import_targets = forms.CharField(
        max_length=255,
        validators=[RegexValidator(regex=RTS_REGEX,
                                   message=_("Import targets is not valid"))],
        label=_("Import targets"),
        required=False,
        help_text=bgpvpn_common.ROUTE_TARGET_HELP + ' To use only on import.')

    export_targets = forms.CharField(
        max_length=255,
        validators=[RegexValidator(regex=RTS_REGEX,
                                   message=_("Export targets is not valid"))],
        label=_("Export targets"),
        required=False,
        help_text=bgpvpn_common.ROUTE_TARGET_HELP + ' To use only on export.')

    def clean(self):
        cleaned_data = super(BgpvpnAttributes, self).clean()
        # Route targets can be empty
        if not cleaned_data.get('route_targets'):
            cleaned_data['route_targets'] = None
        if not cleaned_data.get('import_targets'):
            cleaned_data['import_targets'] = None
        if not cleaned_data.get('export_targets'):
            cleaned_data['export_targets'] = None
        return cleaned_data

    @staticmethod
    def handle_data(data, action):
        params = {}
        for key in bgpvpn_common.RT_FORMAT_ATTRIBUTES:
            params[key] = bgpvpn_common.format_rt(data.pop(key))
        params.update(data)
        if action == 'update':
            del params['bgpvpn_id']
            del params['type']
            del params['tenant_id']
        return params

    @staticmethod
    def order_fields(fields, fields_order):
        if 'keyOrder' in fields:
            fields.keyOrder = fields_order
        else:
            fields = collections.OrderedDict(
                (k, fields[k]) for k in fields_order)
        return fields


class CreateBgpVpn(BgpvpnAttributes):

    tenant_id = forms.ChoiceField(label=_("Project"))

    type = forms.ChoiceField(choices=[("l3", _('l3')),
                                      ("l2", _('l2'))],
                             label=_("Type"),
                             help_text=_("The type of VPN "
                                         " and the technology behind it."))

    def __init__(self, request, *args, **kwargs):
        super(CreateBgpVpn, self).__init__(request, *args, **kwargs)
        fields_order = ['name', 'tenant_id', 'type',
                        'route_targets', 'import_targets', 'export_targets']
        self.fields = self.order_fields(self.fields, fields_order)

        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

    def clean(self):
        cleaned_data = super(CreateBgpVpn, self).clean()
        name = cleaned_data.get('name')
        tenant_id = cleaned_data.get('tenant_id')
        try:
            bgpvpns = bgpvpn_api.bgpvpns_list(self.request,
                                              name=name,
                                              tenant_id=tenant_id)
        except Exception:
            msg = _('Unable to get BGPVPN with name %s') % name
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        if bgpvpns:
            raise forms.ValidationError(
                _('The name "%s" is already used by another BGPVPN.') % name)
        return cleaned_data

    def handle(self, request, data):
        try:
            params = self.handle_data(data, 'create')
            bgpvpn = bgpvpn_api.bgpvpn_create(request, **params)
            msg = _('BGPVPN %s was successfully created.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return bgpvpn
        except Exception:
            redirect = reverse('horizon:admin:bgpvpn:index')
            msg = _('Failed to create the BGPVPN %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)


class EditDataBgpVpn(BgpvpnAttributes):

    bgpvpn_id = forms.CharField(label=_("ID"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    type = forms.CharField(label=_("Type"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(EditDataBgpVpn, self).__init__(request, *args, **kwargs)
        fields_order = ['name', 'bgpvpn_id', 'tenant_id', 'type',
                        'route_targets', 'import_targets', 'export_targets']
        self.fields = self.order_fields(self.fields, fields_order)

    def clean(self):
        cleaned_data = super(EditDataBgpVpn, self).clean()
        name = cleaned_data.get('name')
        bgpvpn_id = cleaned_data.get('bgpvpn_id')
        tenant_id = cleaned_data.get('tenant_id')
        try:
            bgpvpns = bgpvpn_api.bgpvpns_list(self.request,
                                              name=name,
                                              tenant_id=tenant_id)
        except Exception:
            msg = _('Unable to get BGPVPN with name %s') % name
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        if bgpvpns:
            for bgpvpn in bgpvpns:
                if bgpvpn.id != bgpvpn_id:
                    raise forms.ValidationError(
                        _('The name "%s" is already used by another BGPVPN.') %
                        name)
        return cleaned_data

    def handle(self, request, data):
        try:
            params = self.handle_data(data, 'update')
            bgpvpn = bgpvpn_api.bgpvpn_update(request,
                                              data['bgpvpn_id'],
                                              **params)
            msg = _('BGPVPN %s was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
        except Exception:
            redirect = reverse('horizon:admin:bgpvpn:index')
            msg = _('Failed to modify BGPVPN %s') % data['name']
            exceptions.handle(request, msg, redirect=redirect)
            return False
        return bgpvpn
