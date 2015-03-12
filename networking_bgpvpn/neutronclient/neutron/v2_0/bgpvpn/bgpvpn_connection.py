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
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20


class BGPVPNConnection(extension.NeutronClientExtension):
    resource = 'bgpvpn_connection'
    path = 'bgpvpn-connections'
    resource_plural = '%ss' % resource
    object_path = '/bgpvpn/%s' % path
    resource_path = '/bgpvpn/%s/%%s' % path
    versions = ['2.0']


class BGPVPNConnectionCreate(extension.ClientExtensionCreate,
                             BGPVPNConnection):
    shell_command = 'bgpvpn-connection-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name',
            help=_('Name of the BGP VPN connection'))
        parser.add_argument(
            '--type',
            default='l3', choices=['l2', 'l3'],
            help=_('BGP VPN connection type selection between L3VPN (l3) and '
                   'EVPN (l2), default:l3'))
        parser.add_argument(
            '--route-targets',
            help=_('Route Targets list to import/export for this BGP '
                   'VPN connection. Usage: -- --route-targets '
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
            '--network-id', metavar='NETWORK',
            default=None,
            help=_('Id of the network associated with this '
                   'BGP VPN connection'))
        parser.add_argument(
            '--no-aggregate',
            dest='auto_aggregate', action='store_false',
            help=_('Disable auto aggregation (only for '
                   'L3VPN connection type)'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {},
        }

        if parsed_args.network_id:
            _network_id = neutronv20.find_resourceid_by_name_or_id(
                self.get_client(), 'network',
                parsed_args.network_id)
            body[self.resource]['network_id'] = _network_id

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['name', 'tenant_id', 'type', 'route_targets',
                                'import_targets', 'export_targets',
                                'auto_aggregate'])

        return body


class BGPVPNConnectionUpdate(extension.ClientExtensionUpdate,
                             BGPVPNConnection):
    shell_command = 'bgpvpn-connection-update'


class BGPVPNConnectionDelete(extension.ClientExtensionDelete,
                             BGPVPNConnection):
    shell_command = 'bgpvpn-connection-delete'


class BGPVPNConnectionList(extension.ClientExtensionList,
                           BGPVPNConnection):
    shell_command = 'bgpvpn-connection-list'
    list_columns = [
        'id', 'name', 'type', 'route_targets', 'import_targets',
        'export_targets', 'network_id', 'auto_aggregate', 'tenant_id']
    pagination_support = True
    sorting_support = True


class BGPVPNConnectionShow(extension.ClientExtensionShow,
                           BGPVPNConnection):
    shell_command = 'bgpvpn-connection-show'
