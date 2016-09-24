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
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from horizon import forms
from openstack_dashboard import api

from bgpvpn_dashboard.common import bgpvpn as bgpvpn_common
from networking_bgpvpn.neutron.services.common import constants

from bgpvpn_dashboard.dashboards.project.bgpvpn import forms \
    as project_forms


RT_REGEX = constants.RT_REGEX[1:-1]
RTS_REGEX = '^%s( *, *%s)*$' % (RT_REGEX, RT_REGEX)


class CommonData(project_forms.CommonData):
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

    failure_url = reverse_lazy('horizon:admin:bgpvpn:index')

    def __init__(self, request, *args, **kwargs):
        super(CommonData, self).__init__(request, *args, **kwargs)


class CreateBgpVpn(CommonData):
    tenant_id = forms.ChoiceField(label=_("Project"))

    type = forms.ChoiceField(choices=[("l3", _('l3')),
                                      ("l2", _('l2'))],
                             label=_("Type"),
                             help_text=_("The type of VPN "
                                         " and the technology behind it."))

    fields_order = ['name', 'tenant_id', 'type',
                    'route_targets', 'import_targets', 'export_targets']

    def __init__(self, request, *args, **kwargs):
        super(CreateBgpVpn, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, has_more = api.keystone.tenant_list(request)
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices
        self.action = 'create'


class EditDataBgpVpn(CommonData):
    bgpvpn_id = forms.CharField(label=_("ID"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    type = forms.CharField(label=_("Type"), widget=forms.TextInput(
        attrs={'readonly': 'readonly'}))
    tenant_id = forms.CharField(widget=forms.HiddenInput())

    fields_order = ['name', 'bgpvpn_id', 'tenant_id', 'type',
                    'route_targets', 'import_targets', 'export_targets']

    def __init__(self, request, *args, **kwargs):
        super(EditDataBgpVpn, self).__init__(request, *args, **kwargs)
        self.action = 'update'
