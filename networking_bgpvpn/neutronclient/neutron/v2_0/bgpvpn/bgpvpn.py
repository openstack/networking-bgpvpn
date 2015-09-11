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


class BGPVPN(extension.NeutronClientExtension):
    resource = 'bgpvpn'
    path = 'bgpvpns'
    resource_plural = '%ss' % resource
    object_path = '/bgpvpn/%s' % path
    resource_path = '/bgpvpn/%s/%%s' % path
    versions = ['2.0']


class BGPVPNCommandsCommonMixin(object):

    def add_common_known_args(self, parser):
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


class BGPVPNCreate(extension.ClientExtensionCreate,
                   BGPVPN,
                   BGPVPNCommandsCommonMixin
                   ):
    shell_command = 'bgpvpn-create'

    def add_known_arguments(self, parser):

        BGPVPNCommandsCommonMixin.add_common_known_args(self, parser)

        parser.add_argument(
            '--type',
            default='l3', choices=['l2', 'l3'],
            help=_('BGP VPN type selection between L3VPN (l3) and '
                   'EVPN (l2), default:l3'))


class BGPVPNConnectionUpdate(extension.ClientExtensionUpdate,
                             BGPVPN,
                             BGPVPNCommandsCommonMixin):
    shell_command = 'bgpvpn-update'


class BGPVPNConnectionDelete(extension.ClientExtensionDelete,
                             BGPVPN):
    shell_command = 'bgpvpn-delete'


class BGPVPNConnectionList(extension.ClientExtensionList,
                           BGPVPN):
    shell_command = 'bgpvpn-list'
    list_columns = [
        'id', 'name', 'type', 'route_targets', 'import_targets',
        'export_targets', 'tenant_id']
    pagination_support = True
    sorting_support = True


class BGPVPNConnectionShow(extension.ClientExtensionShow,
                           BGPVPN):
    shell_command = 'bgpvpn-show'


class BGPVPNNetAssociationCommand(BGPVPN, neutronv20.NeutronCommand):

    path_action = None

    def success_message(self, bgpvpn_id, network_id):
        raise NotImplementedError()

    def call_api(self, neutron_client, bgpvpn_id, network_id):
        if not self.path_action:
            raise NotImplementedError()

        body = {'network_id': network_id}

        return neutron_client.put("%s/%s" % ((self.resource_path % bgpvpn_id),
                                             self.path_action),
                                  body=body)

    def get_parser(self, prog_name):
        parser = super(BGPVPNNetAssociationCommand, self).get_parser(prog_name)
        parser.add_argument(
            'bgpvpn',
            help=_('ID or name of the BGPVPN.'))
        parser.add_argument(
            '--network', required=True,
            help=_('ID or name of the network.'))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format

        _bgpvpn_id = neutronv20.find_resourceid_by_name_or_id(
            neutron_client, self.resource, parsed_args.bgpvpn)

        _network_id = neutronv20.find_resourceid_by_name_or_id(
            neutron_client, 'network', parsed_args.network)

        out = self.call_api(neutron_client, _bgpvpn_id, _network_id)
        self.log.debug("out: %s", out)

        print(self.success_message(parsed_args.bgpvpn, parsed_args.network),
              file=self.app.stdout)


class BGPVPNNetAssociate(BGPVPNNetAssociationCommand):
    shell_command = 'bgpvpn-network-associate'
    path_action = 'associate_network'

    def success_message(self, bgpvpn_id, network_id):
        return (_('Associated network %(network)s to BGPVPN %(bgpvpn)s.') %
                {'network': network_id, 'bgpvpn': bgpvpn_id})


class BGPVPNNetDisassociate(BGPVPNNetAssociationCommand):
    shell_command = 'bgpvpn-network-disassociate'
    path_action = 'disassociate_network'

    def success_message(self, bgpvpn_id, network_id):
        return (_('Disassociated network %(network)s to BGPVPN %(bgpvpn)s.') %
                {'network': network_id, 'bgpvpn': bgpvpn_id})
