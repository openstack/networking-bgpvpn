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

from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard import api

from bgpvpn_dashboard.api import bgpvpn as bgpvpn_api


class UpdateAssociations(workflows.MembershipAction):
    def __init__(self, request, resource_type, *args, **kwargs):
        super(UpdateAssociations, self).__init__(request,
                                                 *args,
                                                 **kwargs)
        err_msg = _('Unable to retrieve %ss list. '
                    'Please try again later.') % resource_type
        context = args[0]

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        all_resources = self._get_resources(request, context, resource_type,
                                            err_msg)

        resources_list = [(resource.id, resource.name)
                          for resource in all_resources]

        self.fields[field_name].choices = resources_list

        bgpvpn_id = context.get('bgpvpn_id')

        try:
            if bgpvpn_id:
                associations = []
                list_method = getattr(bgpvpn_api, '%s_association_list' %
                                      resource_type)
                associations = [
                    getattr(association, '%s_id' %
                            resource_type) for association in
                    list_method(request, bgpvpn_id)
                    ]

        except Exception:
            exceptions.handle(request, err_msg)

        self.fields[field_name].initial = associations

    def _get_resources(self, request, context, resource_type, err_msg):
        """Get list of available resources."""
        # when an admin user uses the project panel BGPVPN, there is no
        # tenant_id in context because bgpvpn_get doesn't return it
        if request.user.is_superuser and context.get('tenant_id'):
            tenant_id = context.get('tenant_id')
        else:
            tenant_id = self.request.user.tenant_id
        try:
            if resource_type == 'router':
                return api.neutron.router_list(request, tenant_id=tenant_id)
            elif resource_type == 'network':
                return api.neutron.network_list_for_tenant(request, tenant_id)
            else:
                raise Exception(
                    'Resource type %s is not supported' % resource_type)
        except Exception:
            exceptions.handle(request, err_msg % resource_type)


class UpdateBgpVpnRoutersAction(UpdateAssociations):
    def __init__(self, request, *args, **kwargs):
        super(UpdateBgpVpnRoutersAction, self).__init__(request,
                                                        'router',
                                                        *args,
                                                        **kwargs)

    class Meta(object):
        name = _("Router Associations")
        slug = "update_bgpvpn_router"


class UpdateBgpVpnRouters(workflows.UpdateMembersStep):
    action_class = UpdateBgpVpnRoutersAction
    help_text = _("Select the routers to be associated.")
    available_list_title = _("All Routers")
    members_list_title = _("Selected Routers")
    no_available_text = _("No router found.")
    no_members_text = _("No router selected.")
    show_roles = False
    depends_on = ("bgpvpn_id", "name")
    contributes = ("routers_association",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['routers_association'] = data.get(member_field_name, [])
        return context


class UpdateBgpVpnNetworksAction(UpdateAssociations):
    def __init__(self, request, *args, **kwargs):
        super(UpdateBgpVpnNetworksAction, self).__init__(request,
                                                         'network',
                                                         *args,
                                                         **kwargs)

    class Meta(object):
        name = _("Network Associations")
        slug = "update_bgpvpn_network"


class UpdateBgpVpnNetworks(workflows.UpdateMembersStep):
    action_class = UpdateBgpVpnNetworksAction
    help_text = _("Select the networks to be associated.")
    available_list_title = _("All Networks")
    members_list_title = _("Selected Networks")
    no_available_text = _("No network found.")
    no_members_text = _("No network selected.")
    show_roles = False
    depends_on = ("bgpvpn_id", "name")
    contributes = ("networks_association",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['networks_association'] = data.get(member_field_name, [])
        return context


class UpdateBgpVpnAssociations(workflows.Workflow):
    slug = "update_bgpvpn_associations"
    name = _("Edit BGPVPN associations")
    finalize_button_name = _("Save")
    success_message = _('Modified BGPVPN associations "%s".')
    failure_message = _('Unable to modify BGPVPN associations "%s".')
    success_url = "horizon:project:bgpvpn:index"
    default_steps = (UpdateBgpVpnNetworks,
                     UpdateBgpVpnRouters)

    def format_status_message(self, message):
        return message % self.context['name']

    def _handle_type(self, request, data, association_type):
        list_method = getattr(bgpvpn_api,
                              '%s_association_list' % association_type)
        associations = data["%ss_association" % association_type]
        try:
            old_associations = [
                getattr(association,
                        '%s_id' % association_type) for association in
                list_method(request, data['bgpvpn_id'])]
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve %ss associations') %
                              association_type)
            raise

        to_remove_associations = list(set(old_associations) -
                                      set(associations))
        to_add_associations = list(set(associations) -
                                   set(old_associations))

        # If new resource added to the list
        if len(to_add_associations) > 0:
            for resource in to_add_associations:
                try:
                    create_asso = getattr(bgpvpn_api,
                                          '%s_association_create' %
                                          association_type)
                    params = self._set_params(data, association_type, resource)
                    create_asso(request,
                                data['bgpvpn_id'],
                                **params)
                except Exception as e:
                    exceptions.handle(
                        request,
                        _('Unable to associate {} {} {}').format(
                            association_type,
                            resource, str(e)))
                    raise

        # If resource has been deleted from the list
        if len(to_remove_associations) > 0:
            for resource in to_remove_associations:
                try:
                    list_method = getattr(bgpvpn_api,
                                          '%s_association_list' %
                                          association_type)
                    asso_list = list_method(request, data['bgpvpn_id'])
                    for association in asso_list:
                        if getattr(association,
                                   '%s_id' % association_type) == resource:
                            delete_method = getattr(bgpvpn_api,
                                                    '%s_association_delete' %
                                                    association_type)
                            delete_method(request,
                                          association.id, data['bgpvpn_id'])
                except Exception:
                    exceptions.handle(
                        request,
                        _('Unable to disassociate {}s {}').format(
                            association_type,
                            resource))
                    raise

    def _set_params(self, data, association_type, resource):
        params = dict()
        params['%s_id' % association_type] = resource
        return params

    def handle(self, request, data):
        action = False
        try:
            if 'networks_association' in data:
                self._handle_type(request, data, 'network')
                action = True
            if 'routers_association' in data:
                self._handle_type(request, data, 'router')
                action = True
            if not action:
                raise Exception('Associations type is not supported')
        except Exception:
            return False
        return True
