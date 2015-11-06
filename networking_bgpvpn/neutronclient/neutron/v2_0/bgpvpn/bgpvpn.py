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

from __future__ import print_function

from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20

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
        parser.add_argument(
            '--no-aggregate',
            dest='auto_aggregate', action='store_false',
            help=_('Disable auto aggregation (only for '
                   'L3VPN type)'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['name', 'tenant_id', 'type', 'route_targets',
                                'import_targets', 'export_targets',
                                'route_distinguishers', 'auto_aggregate'])

        return body


class BGPVPNCreate(BGPVPNCreateUpdateCommon,
                   extension.ClientExtensionCreate):
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
    shell_command = 'bgpvpn-update'


class BGPVPNDelete(extension.ClientExtensionDelete,
                   BGPVPN):
    shell_command = 'bgpvpn-delete'


class BGPVPNList(extension.ClientExtensionList,
                 BGPVPN):
    shell_command = 'bgpvpn-list'
    list_columns = [
        'id', 'name', 'type', 'route_targets', 'import_targets',
        'export_targets', 'tenant_id', 'networks']
    pagination_support = True
    sorting_support = True


class BGPVPNShow(extension.ClientExtensionShow,
                 BGPVPN):
    shell_command = 'bgpvpn-show'


# BGPVPN  associations


def _get_bgpvpn_id(client, name_or_id):
    return neutronv20.find_resourceid_by_name_or_id(
        client, BGPVPN.resource, name_or_id)


class BGPVPNAssociation(object):

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
    shell_command = "bgpvpn-net-assoc-update"


class BGPVPNNetAssocDelete(extension.ClientExtensionDelete,
                           BGPVPNNetAssoc):
    shell_command = "bgpvpn-net-assoc-delete"


class BGPVPNNetAssocList(extension.ClientExtensionList,
                         BGPVPNNetAssoc):
    shell_command = "bgpvpn-net-assoc-list"

    list_columns = ['id', 'network_id']
    pagination_support = True
    sorting_support = True


class BGPVPNNetAssocShow(extension.ClientExtensionShow,
                         BGPVPNNetAssoc):
    shell_command = "bgpvpn-net-assoc-show"
