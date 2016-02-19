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

from heat.common import exception
from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import properties
from heat.engine.resources.openstack.neutron import neutron


class BGPVPN(neutron.NeutronResource):
    """A resource for BGPVPN service in neutron.

    """

    PROPERTIES = (
        NAME, TYPE, DESCRIPTION, ROUTE_DISTINGUISHERS,
        IMPORT_TARGETS, EXPORT_TARGETS, ROUTE_TARGETS,
        TENANT_ID
    ) = (
        'name', 'type', 'description',
        'route_distinguishers', 'import_targets',
        'export_targets', 'route_targets',
        'tenant_id'
    )

    ATTRIBUTES = (
        SHOW, STATUS
    ) = (
        'show', 'status'
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name for the bgpvpn.'),
        ),
        TYPE: properties.Schema(
            properties.Schema.STRING,
            _('BGP VPN type selection between L3VPN (l3) and '
              'EVPN (l2), default:l3'),
            required=False,
            default='l3'
        ),
        DESCRIPTION: properties.Schema(
            properties.Schema.STRING,
            _('Description for the bgpvpn.'),
            required=False,
        ),
        TENANT_ID: properties.Schema(
            properties.Schema.STRING,
            _('Tenant id this bgpvpn belongs to.'),
            required=False,
        ),
        ROUTE_DISTINGUISHERS: properties.Schema(
            properties.Schema.LIST,
            _('List of RDs that will be used to advertize BGPVPN routes.'),
            required=False,
        ),
        IMPORT_TARGETS: properties.Schema(
            properties.Schema.LIST,
            _('List of additional Route Targets to import from.'),
            required=False,
        ),
        EXPORT_TARGETS: properties.Schema(
            properties.Schema.LIST,
            _('List of additional Route Targets to export to.'),
            required=False,
        ),
        ROUTE_TARGETS: properties.Schema(
            properties.Schema.LIST,
            _('Route Targets list to import/export for this BGPVPN.'),
            required=False,
        ),
    }

    attributes_schema = {
        STATUS: attributes.Schema(
            _('Status of bgpvpn.'),
        ),
        SHOW: attributes.Schema(
            _('All attributes.')
        ),
    }

    def validate(self):
        super(BGPVPN, self).validate()

    def handle_create(self):
        props = self.prepare_properties(
            self.properties,
            self.physical_resource_name())
        bgpvpn = self.neutron().create_bgpvpn({'bgpvpn': props})
        self.resource_id_set(bgpvpn['bgpvpn']['id'])

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        raise NotImplemented()

    def handle_delete(self):
        try:
            self.neutron().delete_bgpvpn(self.resource_id)
        except Exception as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return True

    def _confirm_delete(self):
        while True:
            try:
                yield self._show_resource()
            except exception.NotFound:
                return

    def _show_resource(self):
        return self.neutron().show_bgpvpn(self.resource_id)


class BGPVPNNetAssoc(neutron.NeutronResource):

    """A resource for BGPVPNNetAssoc in neutron.

    """

    PROPERTIES = (
        BGPVPN_ID, NETWORK_ID
    ) = (
        'bgpvpn_id', 'network_id'
    )

    ATTRIBUTES = (
        SHOW, STATUS
    ) = (
        'show', 'status'
    )

    properties_schema = {
        BGPVPN_ID: properties.Schema(
            properties.Schema.STRING,
            _('ID for the bgpvpn.'),
            required=True,
        ),
        NETWORK_ID: properties.Schema(
            properties.Schema.STRING,
            _('Network which shall be associated with the BGPVPN.'),
            required=True,
        )
    }

    attributes_schema = {
        STATUS: attributes.Schema(
            _('Status of bgpvpn.'),
        ),
        SHOW: attributes.Schema(
            _('All attributes.')
        ),
    }

    def validate(self):
        super(BGPVPNNetAssoc, self).validate()

    def handle_create(self):
        self.props = self.prepare_properties(self.properties,
                                             self.physical_resource_name())

        body = self.props.copy()
        body.pop('bgpvpn_id')

        net_assoc = self.neutron().create_network_association(
            self.props['bgpvpn_id'],
            {'network_association': body})
        self.resource_id_set(net_assoc['network_association']['id'])

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        raise NotImplemented()

    def handle_delete(self):
        try:
            self.neutron().delete_network_association(
                self.resource_id, self.properties['bgpvpn_id'])
        except Exception as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return True

    def _confirm_delete(self):
        while True:
            try:
                self._show_resource()
            except exception.NotFound:
                return

    def _show_resource(self):
        return self.neutron().show_network_association(
            self.resource_id, self.properties['bgpvpn_id'])


class BGPVPNRouterAssoc(neutron.NeutronResource):

    """A resource for BGPVPNRouterAssoc in neutron.

    """

    PROPERTIES = (
        BGPVPN_ID, ROUTER_ID
    ) = (
        'bgpvpn_id', 'router_id'
    )

    ATTRIBUTES = (
        SHOW, STATUS
    ) = (
        'show', 'status'
    )

    properties_schema = {
        BGPVPN_ID: properties.Schema(
            properties.Schema.STRING,
            _('ID for the bgpvpn.'),
            required=True,
        ),
        ROUTER_ID: properties.Schema(
            properties.Schema.STRING,
            _('Router which shall be associated with the BGPVPN.'),
            required=True,
        )
    }

    attributes_schema = {
        STATUS: attributes.Schema(
            _('Status of bgpvpn.'),
        ),
        SHOW: attributes.Schema(
            _('All attributes.')
        ),
    }

    def validate(self):
        super(BGPVPNRouterAssoc, self).validate()

    def handle_create(self):
        self.props = self.prepare_properties(self.properties,
                                             self.physical_resource_name())

        body = self.props.copy()
        body.pop('bgpvpn_id')

        router_assoc = self.neutron().create_router_association(
            self.props['bgpvpn_id'],
            {'router_association': body})
        self.resource_id_set(router_assoc['router_association']['id'])

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        raise NotImplemented()

    def handle_delete(self):
        try:
            self.neutron().delete_router_association(
                self.resource_id, self.properties['bgpvpn_id'])
        except Exception as ex:
            self.client_plugin().ignore_not_found(ex)
        else:
            return True

    def _confirm_delete(self):
        while True:
            try:
                self._show_resource()
            except exception.NotFound:
                return

    def _show_resource(self):
        return self.neutron().show_router_association(
            self.resource_id, self.properties['bgpvpn_id'])


def resource_mapping():
    return {
        'OS::Neutron::BGPVPN': BGPVPN,
        'OS::Neutron::BGPVPN-NET-ASSOCIATION': BGPVPNNetAssoc,
        'OS::Neutron::BGPVPN-ROUTER-ASSOCIATION': BGPVPNRouterAssoc,
    }
