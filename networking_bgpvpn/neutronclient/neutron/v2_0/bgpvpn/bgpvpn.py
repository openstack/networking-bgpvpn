# Copyright (c) 2015 Orange.
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

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronv20

from networking_bgpvpn._i18n import _

# To understand how neutronclient extensions work
# read neutronclient/v2.0/client.py (extend_* methods and _register_extension)


class BGPVPN(extension.NeutronClientExtension):
    resource = 'bgpvpn'
    resource_plural = '%ss' % resource

    object_path = '/bgpvpn/%s' % resource_plural
    resource_path = '/bgpvpn/%s/%%s' % resource_plural

    versions = ['2.0']


class BGPVPNCreateUpdateCommon(BGPVPN):

    def add_known_arguments(self, parser):
        """Adds to parser arguments common to create and update commands."""

        parser.add_argument(
            '--name',
            help=_('Name of the BGP VPN'))
        parser.add_argument(
            '--route-targets',
            help=_('Route Targets list to import/export for this BGP '
                   'VPN. Usage: -- --route-targets '
                   'list=true <asn1>:<nn1> <asn2>:<nn2> ...'))
        parser.add_argument(
            '--import-targets',
            help=_('List of additional Route Targets to import from.'
                   ' Usage: -- --import-targets list=true '
                   '<asn1>:<nn1> <asn2>:<nn2> ...'))
        parser.add_argument(
            '--export-targets',
            help=_('List of additional Route Targets to export to. Usage: -- '
                   '--export-targets list=true <asn1>:<nn1> <asn2>:<nn2> ...'))
        parser.add_argument(
            '--route-distinguishers',
            help=_('List of RDs that will be used to advertize VPN routes.'
                   'Usage: -- --route-distinguishers list=true '
                   '<asn1>:<nn1> <asn2>:<nn2> ...'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['name', 'tenant_id', 'type', 'route_targets',
                                'import_targets', 'export_targets',
                                'route_distinguishers'])

        return body


class BGPVPNCreate(BGPVPNCreateUpdateCommon,
                   extension.ClientExtensionCreate):
    """Create a BGPVPN."""
    shell_command = 'bgpvpn-create'

    def add_known_arguments(self, parser):

        BGPVPNCreateUpdateCommon.add_known_arguments(self, parser)

        # type is read-only, hence specific to create
        parser.add_argument(
            '--type',
            default='l3', choices=['l2', 'l3'],
            help=_('BGP VPN type selection between L3VPN (l3) and '
                   'EVPN (l2), default:l3'))


class BGPVPNUpdate(BGPVPNCreateUpdateCommon,
                   extension.ClientExtensionUpdate):
    """Update a given BGPVPN."""
    shell_command = 'bgpvpn-update'


class BGPVPNDelete(extension.ClientExtensionDelete,
                   BGPVPN):
    """Delete a given BGPVPN."""
    shell_command = 'bgpvpn-delete'


class BGPVPNList(extension.ClientExtensionList,
                 BGPVPN):
    """List BGPVPNs that belong to a given tenant."""
    shell_command = 'bgpvpn-list'
    list_columns = [
        'id', 'name', 'type', 'route_targets', 'import_targets',
        'export_targets', 'tenant_id', 'networks', 'routers']
    pagination_support = True
    sorting_support = True


class BGPVPNShow(extension.ClientExtensionShow,
                 BGPVPN):
    """Show a given BGPVPN."""
    shell_command = 'bgpvpn-show'


# BGPVPN  associations


def _get_bgpvpn_id(client, name_or_id):
    return neutronv20.find_resourceid_by_name_or_id(
        client, BGPVPN.resource, name_or_id)


class BGPVPNAssociation():

    def add_known_arguments(self, parser):
        parser.add_argument('bgpvpn', metavar='BGPVPN',
                            help=_('ID or name of the BGPVPN.'))

    def set_extra_attrs(self, parsed_args):
        self.parent_id = _get_bgpvpn_id(self.get_client(), parsed_args.bgpvpn)


# BGPVPN Network associations


class BGPVPNNetAssoc(BGPVPNAssociation,
                     extension.NeutronClientExtension):

    resource = 'network_association'
    resource_plural = '%ss' % resource

    # (parent_resource set to True so that the
    # first %s in *_path will be replaced with parent_id)
    parent_resource = True

    object_path = '%s/%s' % (BGPVPN.resource_path, resource_plural)
    resource_path = '%s/%s/%%%%s' % (BGPVPN.resource_path, resource_plural)

    versions = ['2.0']

    allow_names = False  # network associations have no name


class BGPVPNNetAssocCreate(BGPVPNNetAssoc,
                           extension.ClientExtensionCreate):
    """Create a BGPVPN-Network association."""
    shell_command = "bgpvpn-net-assoc-create"

    def add_known_arguments(self, parser):

        BGPVPNNetAssoc.add_known_arguments(self, parser)

        parser.add_argument(
            '--network', required=True,
            help=_('ID or name of the network.'))

    def args2body(self, parsed_args):

        body = {
            self.resource: {},
        }

        net = neutronv20.find_resourceid_by_name_or_id(self.get_client(),
                                                       'network',
                                                       parsed_args.network)

        body[self.resource]['network_id'] = net
        neutronv20.update_dict(parsed_args, body[self.resource], ['tenant_id'])

        return body


class BGPVPNNetAssocUpdate(extension.ClientExtensionUpdate,
                           BGPVPNNetAssoc):
    """Update a given BGPVPN-Network association."""
    shell_command = "bgpvpn-net-assoc-update"


class BGPVPNNetAssocDelete(extension.ClientExtensionDelete,
                           BGPVPNNetAssoc):
    """Delete a given BGPVPN-Network association."""
    shell_command = "bgpvpn-net-assoc-delete"


class BGPVPNNetAssocList(extension.ClientExtensionList,
                         BGPVPNNetAssoc):
    """List BGPVPN-Network associations for a given BGPVPN."""
    shell_command = "bgpvpn-net-assoc-list"

    list_columns = ['id', 'network_id']
    pagination_support = True
    sorting_support = True


class BGPVPNNetAssocShow(extension.ClientExtensionShow,
                         BGPVPNNetAssoc):
    """Show a given BGPVPN-Network association."""
    shell_command = "bgpvpn-net-assoc-show"


# BGPVPN Router associations


class BGPVPNRouterAssoc(BGPVPNAssociation,
                        extension.NeutronClientExtension):

    resource = 'router_association'
    resource_plural = '%ss' % resource
    parent_resource = True

    object_path = '%s/%s' % (BGPVPN.resource_path, resource_plural)
    resource_path = '%s/%s/%%%%s' % (BGPVPN.resource_path, resource_plural)

    versions = ['2.0']

    allow_names = False


class BGPVPNRouterAssocCreate(BGPVPNRouterAssoc,
                              extension.ClientExtensionCreate):
    """Create a BGPVPN-Router association."""
    shell_command = "bgpvpn-router-assoc-create"

    def add_known_arguments(self, parser):
        BGPVPNRouterAssoc.add_known_arguments(self, parser)
        parser.add_argument(
            '--router', required=True,
            help=_('ID or name of the router.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }
        router = neutronv20.find_resourceid_by_name_or_id(self.get_client(),
                                                          'router',
                                                          parsed_args.router)
        body[self.resource]['router_id'] = router
        neutronv20.update_dict(parsed_args, body[self.resource], ['tenant_id'])
        return body


class BGPVPNRouterAssocUpdate(extension.ClientExtensionUpdate,
                              BGPVPNRouterAssoc):
    """Update a given BGPVPN-Router association."""
    shell_command = "bgpvpn-router-assoc-update"


class BGPVPNRouterAssocDelete(extension.ClientExtensionDelete,
                              BGPVPNRouterAssoc):
    """Delete a given BGPVPN-Router association."""
    shell_command = "bgpvpn-router-assoc-delete"


class BGPVPNRouterAssocList(extension.ClientExtensionList,
                            BGPVPNRouterAssoc):
    """List BGPVPN-Router associations for a given BGPVPN."""
    shell_command = "bgpvpn-router-assoc-list"

    list_columns = ['id', 'router_id']
    pagination_support = True
    sorting_support = True


class BGPVPNRouterAssocShow(extension.ClientExtensionShow,
                            BGPVPNRouterAssoc):
    """Show a given BGPVPN-Router association."""
    shell_command = "bgpvpn-router-assoc-show"
