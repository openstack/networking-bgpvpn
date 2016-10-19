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
from networking_bgpvpn.osc.bgpvpn import resource as bgpvpn_resource

LOG = logging.getLogger(__name__)


def _get_attr_names(resources, columns_map):
    attr_names = []
    for dummy_header, attr_name in columns_map:
        for resource in resources:
            if resource.get(attr_name, None):
                attr_names.append(attr_name)
                break
    return attr_names


def _get_headers(resources, columns_map):
    headers = []
    for header, attr_name in columns_map:
        for resource in resources:
            if resource.get(attr_name, None):
                headers.append(header)
                break
    return headers


class CreateBgpvpnResAssoc(command.ShowOne):
    """Create a BGP VPN resource association."""

    def get_parser(self, prog_name):
        parser = super(CreateBgpvpnResAssoc, self).get_parser(prog_name)
        parser.add_argument(
            '--project',
            metavar='<project>',
            help=_("Owner's project (name or ID)")
        )
        identity_common.add_project_domain_option_to_parser(parser)
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of the BGP VPN."))
        parser.add_argument(
            'resource',
            metavar="<%s>" % self._assoc_res_name,
            help=(_("ID or name of the %s.") % self._assoc_res_name))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        bgpvpn = client.find_resource(bgpvpn_resource, parsed_args.bgpvpn)
        assoc_res = client.find_resource(self._assoc_res_name,
                                         parsed_args.resource)
        body = {
            self._resource: {
                '%s_id' % self._assoc_res_name: assoc_res['id'],
            },
        }
        if 'project' in parsed_args and parsed_args.project is not None:
            identity_client = self.app.client_manager.identity
            project_id = identity_common.find_project(
                identity_client,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
            body[self._resource]['tenant_id'] = project_id
        obj = client.create_ext(self._object_path % bgpvpn['id'], body)
        columns = _get_attr_names([obj[self._resource]], self._columns_map)
        data = utils.get_dict_properties(obj[self._resource], columns)
        return columns, data


class UpdateBgpvpnResAssoc(command.Command):
    """Update a BGP VPN resource association."""

    def get_parser(self, prog_name):
        parser = super(UpdateBgpvpnResAssoc, self).get_parser(prog_name)
        parser.add_argument(
            'resource_association',
            metavar="<%s association>" % self._assoc_res_name,
            help=(_("ID of the %s association to update.") %
                  self._assoc_res_name))
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of BGP VPN."))
        return parser

    def take_action(self, parsed_args):
        msg = _("Current BGP VPN API does not permit to update any %s "
                "association attributes") % self._assoc_res_name
        raise exceptions.UnsupportedVersion(msg)
        # client = self.app.client_manager.neutronclient
        # bgpvpn = client.find_resource(bgpvpn_resource, parsed_args.bgpvpn)
        # client.update_ext(self._resource_path % bgpvpn['id'],
        #                   parsed_args.resource_association, {})


class DeleteBgpvpnResAssoc(command.Command):
    """Delete a given BGP VPN resource association."""

    def get_parser(self, prog_name):
        parser = super(DeleteBgpvpnResAssoc, self).get_parser(prog_name)
        parser.add_argument(
            'resource_associations',
            metavar="<%s association>" % self._assoc_res_name,
            nargs="+",
            help=(_("ID(s) of the %s association(s) to delete.") %
                  self._assoc_res_name))
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of BGP VPN."))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        bgpvpn = client.find_resource(bgpvpn_resource, parsed_args.bgpvpn)
        fails = 0
        for id in parsed_args.resource_associations:
            try:
                client.delete_ext(self._resource_path % bgpvpn['id'], id)
                LOG.warn(_LW("%(assoc_res_name)s association %(id)s deleted"),
                         {'assoc_res_name': self._assoc_res_name.capitalize(),
                          'id': id})
            except Exception as e:
                fails += 1
                LOG.error(_LE("Failed to delete %(assoc_res_name)s "
                              "association with ID '%(id)s': %(e)s"),
                          {'assoc_res_name': self._assoc_res_name,
                           'id': id,
                           'e': e})
        if fails > 0:
            msg = (_("Failed to delete %(fails)s of %(total)s "
                     "%(assoc_res_name)s BGP VPN association(s).") %
                   {'fails': fails,
                    'total': len(parsed_args.resource_associations),
                    'assoc_res_name': self._assoc_res_name})
            raise exceptions.CommandError(msg)


class ListBgpvpnResAssoc(command.Lister):
    """List BGP VPN resource associations for a given BGP VPN."""

    def get_parser(self, prog_name):
        parser = super(ListBgpvpnResAssoc, self).get_parser(prog_name)
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of BGP VPN."))
        parser.add_argument(
            '--property',
            metavar='<key=value>',
            default=dict(),
            help=_('Filter property to apply on returned bgpvpns (repeat to '
                   'filter on multiple properties)'),
            action=KeyValueAction)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        bgpvpn = client.find_resource(bgpvpn_resource, parsed_args.bgpvpn)
        data = client.list_ext(collection=self._resource_plural,
                               path=self._object_path % bgpvpn['id'],
                               retrieve_all=True,
                               **parsed_args.property)[self._resource_plural]
        columns = _get_attr_names(data, self._columns_map)
        headers = _get_headers(data, self._columns_map)
        return (headers, (utils.get_dict_properties(s, columns) for s in data))


class ShowBgpvpnResAssoc(command.ShowOne):
    """Show information of a given BGP VPN resource association."""

    def get_parser(self, prog_name):
        parser = super(ShowBgpvpnResAssoc, self).get_parser(prog_name)
        parser.add_argument(
            'resource_association',
            metavar="<%s association>" % self._assoc_res_name,
            help=(_("ID of the %s association to look up.") %
                  self._assoc_res_name))
        parser.add_argument(
            'bgpvpn',
            metavar="<bgpvpn>",
            help=_("ID or name of BGP VPN."))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.neutronclient
        bgpvpn = client.find_resource(bgpvpn_resource, parsed_args.bgpvpn)
        obj = client.show_ext(self._resource_path % bgpvpn['id'],
                              parsed_args.resource_association)
        columns = _get_attr_names([obj[self._resource]], self._columns_map)
        data = utils.get_dict_properties(obj[self._resource], columns)
        return columns, data
