# Copyright (c) 2016 Juniper Networks Inc.
# All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import logging

from openstackclient.identity import common as identity_common
from osc_lib.cli.parseractions import KeyValueAction
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils

from networking_bgpvpn._i18n import _
from networking_bgpvpn._i18n import _LE
from networking_bgpvpn._i18n import _LW

LOG = logging.getLogger(__name__)

resource = 'bgpvpn'
_resource_plural = '%ss' % resource
_object_path = '/bgpvpn/%s' % _resource_plural
resource_path = '/bgpvpn/%s/%%s' % _resource_plural
_columns_map = (
    ('ID', 'id'),
    ('Project ID', 'tenant_id'),
    ('Name', 'name'),
    ('Type', 'type'),
    ('Route Targets', 'route_targets'),
    ('Import Targets', 'import_targets'),
    ('Export Targets', 'export_targets'),
    ('Route Distinguishers', 'route_distinguishers'),
    ('Associated Networks', 'networks'),
    ('Associated Routers', 'routers'),
)
_formatters = {
    'route_targets': utils.format_list,
    'import_targets': utils.format_list,
    'export_targets': utils.format_list,
    'route_distinguishers': utils.format_list,
    'networks': utils.format_list,
    'routers': utils.format_list,
}


def _add_create_update_common_arguments(parser):
    """Adds to parser arguments common to create and update commands."""

    parser.add_argument(
        '--name',
        metavar='<name>',
        help=_('Name of the BGP VPN'))
    parser.add_argument(
        '--route-target',
        dest='route_targets',
        action='append',
        metavar='<route-target>',
        help=_('Route Target to import/export for this BGP VPN '
               '(repeat option to set multiple Route Targets).'))
    parser.add_argument(
        '--import-target',
        dest='import_targets',
        action='append',
        metavar='<import-target>',
        help=_('Additional Route Target to import from '
               '(repeat option to set multiple Route Targets).'))
    parser.add_argument(
        '--export-target',
        dest='export_targets',
        action='append',
        metavar='<export-target>',
        help=_('Additional Route Target to export to '
               '(repeat option to set multiple Route Targets).'))
    parser.add_argument(
        '--route-distinguisher',
        dest='route_distinguishers',
        action='append',
        metavar='<route-distinguisher>',
        help=_('Set of Route Distinguisher in which the Route Distinguisher'
               'for advertized VPN routes will be picked from (repeat option '
               'to set multiple Route Distinguishers).'))


def _args2body(client_manager, parsed_args):
    attrs = {}
    if parsed_args.name is not None:
        attrs['name'] = str(parsed_args.name)
    if getattr(parsed_args, 'type', None) is not None:
        attrs['type'] = parsed_args.type
    if parsed_args.route_targets is not None:
        attrs['route_targets'] = parsed_args.route_targets
    if parsed_args.import_targets is not None:
        attrs['import_targets'] = parsed_args.import_targets
    if parsed_args.export_targets is not None:
        attrs['export_targets'] = parsed_args.export_targets
    if parsed_args.route_distinguishers is not None:
        attrs['route_distinguishers'] = parsed_args.route_distinguishers
    if 'project' in parsed_args and parsed_args.project is not None:
        project_id = identity_common.find_project(
            client_manager.identity,
            parsed_args.project,
            parsed_args.project_domain,
        ).id
        attrs['tenant_id'] = project_id
    return {resource: attrs}


def _get_attr_names(resources):
    attr_names = []
    for dummy_header, attr_name in _columns_map:
        for resource in resources:
            if resource.get(attr_name, None):
                attr_names.append(attr_name)
                break
    return attr_names


def _get_headers(resources):
    headers = []
    for header, attr_name in _columns_map:
        for resource in resources:
            if resource.get(attr_name, None):
                headers.append(header)
                break
    return headers


class CreateBgpvpn(command.ShowOne):
    """Create BGP VPN resource."""

    def get_parser(self, prog_name):
        parser = super(CreateBgpvpn, self).get_parser(prog_name)
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_("Owner's project (name or ID)")
        )
        identity_common.add_project_domain_option_to_parser(parser)
        _add_create_update_common_arguments(parser)
        parser.add_argument(
            '--type',
            default='l3',
            choices=['l2', 'l3'],
            help=_('BGP VPN type selection between IP VPN (l3) and Ethernet '
                   'VPN (l2) (default:%(default)s)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        body = _args2body(self.app.client_manager, parsed_args)
        obj = client.create_ext(_object_path, body)
        columns = _get_attr_names([obj[resource]])
        data = utils.get_dict_properties(obj[resource], columns,
                                         formatters=_formatters)
        return columns, data


class UpdateBgpvpn(command.Command):
    """Update BGP VPN resource."""

    def get_parser(self, prog_name):
        parser = super(UpdateBgpvpn, self).get_parser(prog_name)
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of BGP VPN to update."))
        _add_create_update_common_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        body = _args2body(self.app.client_manager, parsed_args)
        id = client.find_resource(resource, parsed_args.bgpvpn)['id']
        client.update_ext(resource_path, id, body)


class DeleteBgpvpn(command.Command):
    """Delete BGP VPN resource(s)."""

    def get_parser(self, prog_name):
        parser = super(DeleteBgpvpn, self).get_parser(prog_name)
        parser.add_argument(
            'bgpvpns',
            metavar="<bgpvpn>",
            nargs="+",
            help=_("BGP VPN(s) to delete (name or ID)"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        fails = 0
        for id_or_name in parsed_args.bgpvpns:
            try:
                id = client.find_resource(resource, id_or_name)['id']
                client.delete_ext(resource_path, id)
                LOG.warn(_LW("BGP VPN %(id)s deleted"), {'id': id})
            except Exception as e:
                fails += 1
                LOG.error(_LE("Failed to delete BGP VPN with name or ID "
                              "'%(id_or_name)s': %(e)s"),
                          {'id_or_name': id_or_name, 'e': e})
        if fails > 0:
            msg = (_("Failed to delete %(fails)s of %(total)s BGP VPN.") %
                   {'fails': fails, 'total': len(parsed_args.bgpvpns)})
            raise exceptions.CommandError(msg)


class ListBgpvpn(command.Lister):
    """List BGP VPN resources."""

    def get_parser(self, prog_name):
        parser = super(ListBgpvpn, self).get_parser(prog_name)
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_("Owner's project (name or ID)"))
        identity_common.add_project_domain_option_to_parser(parser)
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            default=dict(),
            help=_('Filter property to apply on returned BGP VPNs (repeat to '
                   'filter on multiple properties)'),
            action=KeyValueAction)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        params = {}
        if parsed_args.project is not None:
            project_id = identity_common.find_project(
                self.app.client_manager.identity,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
            params['tenant_id'] = project_id
        if parsed_args.property:
            params.update(parsed_args.property)
        data = client.list_ext(collection=_resource_plural,
                               path=_object_path,
                               retrieve_all=True,
                               **params)[_resource_plural]
        headers = _get_headers(data)
        columns = _get_attr_names(data)
        return (
            headers,
            (utils.get_dict_properties(res, columns, formatters=_formatters)
                for res in data),
        )


class ShowBgpvpn(command.ShowOne):
    """Show information of a given BGP VPN."""

    def get_parser(self, prog_name):
        parser = super(ShowBgpvpn, self).get_parser(prog_name)
        parser.add_argument(
            'bgpvpn',
            help=_("ID or name of BGP VPN to display."))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        id = client.find_resource(resource, parsed_args.bgpvpn)['id']
        obj = client.show_ext(resource_path, id)
        columns = _get_attr_names([obj[resource]])
        data = utils.get_dict_properties(obj[resource], columns,
                                         formatters=_formatters)
        return columns, data
