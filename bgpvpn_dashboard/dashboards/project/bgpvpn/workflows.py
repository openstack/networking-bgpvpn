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
import logging

from django.utils.translation import gettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api

LOG = logging.getLogger(__name__)


class AddRouterParametersInfoAction(workflows.Action):

    advertise_extra_routes = forms.BooleanField(
        label=_("Advertise Extra Routes"),
        initial=True,
        required=False,
        help_text="Boolean flag controlling whether or not the routes "
                  "specified in the routes attribute of the router will be "
                  "advertised to the BGPVPN (default: true).")

    class Meta(object):
        name = _("Optional Parameters")
        slug = "add_router_parameters"

    def __init__(self, request, context, *args, **kwargs):
        super(AddRouterParametersInfoAction, self).__init__(
            request, context, *args, **kwargs)
        if 'with_parameters' in context:
            self.fields['with_parameters'] = forms.BooleanField(
                initial=context['with_parameters'],
                required=False,
                widget=forms.HiddenInput()
            )


class CreateRouterAssociationInfoAction(workflows.Action):

    router_resource = forms.ChoiceField(
        label=_("Associate Router"),
        widget=forms.ThemableSelectWidget(
            data_attrs=('name', 'id'),
            transform=lambda x: "%s" % x.name_or_id))

    class Meta(object):
        name = _("Create Association")
        help_text = _("Create a new router association.")
        slug = "create_router_association"

    def __init__(self, request, context, *args, **kwargs):
        super(CreateRouterAssociationInfoAction, self).__init__(
            request, context, *args, **kwargs)

        # when an admin user uses the project panel BGPVPN, there is no
        # tenant_id in context because bgpvpn_get doesn't return it
        if request.user.is_superuser and context.get("project_id"):
            tenant_id = context.get("project_id")
        else:
            tenant_id = self.request.user.tenant_id

        try:
            routers = api.neutron.router_list(request, tenant_id=tenant_id)
            if routers:
                choices = [('', _("Choose a router"))] + [(r.id, r) for r in
                                                          routers]
                self.fields['router_resource'].choices = choices
            else:
                self.fields['router_resource'].choices = [('', _("No router"))]
        except Exception:
            exceptions.handle(request, _("Unable to retrieve routers"))

        if api.neutron.is_extension_supported(request,
                                              'bgpvpn-routes-control'):
            self.fields['with_parameters'] = forms.BooleanField(
                label=_("Optional parameters"),
                initial=False,
                required=False,
                widget=forms.CheckboxInput(attrs={
                    'class': 'switchable',
                    'data-hide-tab': 'router_association__'
                                     'add_router_parameters',
                    'data-hide-on-checked': 'false'
                }))


class AddRouterParametersInfo(workflows.Step):
    action_class = AddRouterParametersInfoAction
    depends_on = ("bgpvpn_id", "name")
    contributes = ("advertise_extra_routes",)


class CreateRouterAssociationInfo(workflows.Step):
    action_class = CreateRouterAssociationInfoAction
    contributes = ("router_resource", "with_parameters")


class RouterAssociation(workflows.Workflow):
    slug = "router_association"
    name = _("Associate a BGPVPN to a Router")
    finalize_button_name = _("Create")
    success_message = _('Router association with "%s" created.')
    failure_message = _('Unable to create a router association with "%s".')
    success_url = "horizon:project:bgpvpn:index"
    default_steps = (CreateRouterAssociationInfo,
                     AddRouterParametersInfo)
    wizard = True

    def format_status_message(self, message):
        name = self.context['name'] or self.context['bgpvpn_id']
        return message % name

    def handle(self, request, context):
        bgpvpn_id = context['bgpvpn_id']
        router_id = context["router_resource"]
        msg_error = _("Unable to associate router %s") % router_id
        try:
            router_association = bgpvpn_api.router_association_create(
                request, bgpvpn_id, router_id=router_id)
        except Exception:
            exceptions.handle(request, msg_error)
            return False
        if not context["with_parameters"]:
            return True
        asso_id = router_association['router_association']['id']
        try:
            bgpvpn_api.router_association_update(
                request, bgpvpn_id, asso_id,
                advertise_extra_routes=context['advertise_extra_routes'])
            return True
        except exceptions:
            bgpvpn_api.router_association_delete(request, asso_id, bgpvpn_id)
            exceptions.handle(request, msg_error)
            return False
