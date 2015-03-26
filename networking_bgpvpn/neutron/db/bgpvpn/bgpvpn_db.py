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

import sqlalchemy as sa

from neutron.common import exceptions as q_exc
from neutron.db import common_db_mixin
from neutron.db import model_base
from neutron.db import models_v2
from neutron.openstack.common import log
from neutron.openstack.common import uuidutils
from sqlalchemy import orm
from sqlalchemy.orm import exc

from networking_bgpvpn.neutron.extensions.bgpvpn.bgpvpn import BGPVPNPluginBase


LOG = log.getLogger(__name__)


class BGPVPNConnection(model_base.BASEV2,
                       models_v2.HasId,
                       models_v2.HasTenant):
    """Represents a BGPVPNConnection Object."""
    __tablename__ = 'bgpvpn_connections'
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.Enum("l2", "l3",
                             name="bgpvpn_type"),
                     nullable=False)
    route_targets = sa.Column(sa.String(255), nullable=False)
    import_targets = sa.Column(sa.String(255), nullable=False)
    export_targets = sa.Column(sa.String(255), nullable=False)
    auto_aggregate = sa.Column(sa.Boolean(), nullable=False)
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id'))
    network = orm.relationship(models_v2.Network)


class BGPVPNConnectionNotFound(q_exc.NotFound):
    message = _("BgpVpnConnection %(conn_id)s could not be found")


class BGPVPNConnectionMissingRouteTarget(q_exc.BadRequest):
    message = _("BgpVpnConnection could not be created. Missing one of"
                " route_targets, import_targets or export_targets attribute")


class BGPVPNNetworkInUse(q_exc.NetworkInUse):
    message = _("Unable to complete operation on network %(network_id)s. "
                "There are one or more BGP VPN connections associated"
                " to the network.")


class BGPVPNPluginDb(BGPVPNPluginBase,
                     common_db_mixin.CommonDbMixin):
    """BGP VPN service plugin database class using SQLAlchemy models."""

    USER_READABLE_ATTRIBUTES = ['id', 'name', 'type',
                                'network_id', 'tenant_id']
    USER_WRITABLE_ATTRIBUTES = ['name', 'network_id']

    def _get_resource(self, context, model, id):
        return self._get_by_id(context, model, id)

    def _rt_list2str(self, list):
        """Format Route Target list to string"""
        if not list:
            return ''

        return ','.join(list)

    def _rt_str2list(self, str):
        """Format Route Target string to list"""
        if not str:
            return []

        return str.split(',')

    def _get_bgpvpn_connections_for_tenant(self, session, tenant_id, fields):
        try:
            qry = session.query(BGPVPNConnection)
            bgpvpn_connections = qry.filter_by(tenant_id=tenant_id)
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_connection_dict(bvc, fields=fields)
                for bvc in bgpvpn_connections]

    def _get_user_readable_fields(self, fields):
        if fields is not None and fields:
            return list(set(fields) & set(self.USER_READABLE_ATTRIBUTES))
        else:
            return self.USER_READABLE_ATTRIBUTES

    def _make_bgpvpn_connection_dict(self,
                                     bgpvpn_connection,
                                     fields=None):
        res = {
            'id': bgpvpn_connection['id'],
            'tenant_id': bgpvpn_connection['tenant_id'],
            'network_id': bgpvpn_connection['network_id'],
            'name': bgpvpn_connection['name'],
            'type': bgpvpn_connection['type'],
            'route_targets':
                self._rt_str2list(bgpvpn_connection['route_targets']),
            'import_targets':
                self._rt_str2list(bgpvpn_connection['import_targets']),
            'export_targets':
                self._rt_str2list(bgpvpn_connection['export_targets']),
            'auto_aggregate': bgpvpn_connection['auto_aggregate']
        }
        return self._fields(res, fields)

    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        bgpvpn_conn = bgpvpn_connection['bgpvpn_connection']

        # Check that route_targets is not empty
        if (not bgpvpn_conn['route_targets']):
            raise BGPVPNConnectionMissingRouteTarget
        else:
            rt = self._rt_list2str(bgpvpn_conn['route_targets'])
            i_rt = self._rt_list2str(bgpvpn_conn['import_targets'])
            e_rt = self._rt_list2str(bgpvpn_conn['export_targets'])

        tenant_id = self._get_tenant_id_for_create(context, bgpvpn_conn)

        with context.session.begin(subtransactions=True):
            bgpvpn_conn_db = BGPVPNConnection(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant_id,
                name=bgpvpn_conn['name'],
                type=bgpvpn_conn['type'],
                route_targets=rt,
                import_targets=i_rt,
                export_targets=e_rt,
                network_id=bgpvpn_conn['network_id'],
                auto_aggregate=bgpvpn_conn['auto_aggregate']
            )
            context.session.add(bgpvpn_conn_db)

        return self._make_bgpvpn_connection_dict(bgpvpn_conn_db)

    def get_bgpvpn_connections(self, context, filters=None, fields=None):
        if context.is_admin:
            return self._get_collection(context, BGPVPNConnection,
                                        self._make_bgpvpn_connection_dict,
                                        filters=filters, fields=fields)
        else:
            readable_fields = self._get_user_readable_fields(fields)
            LOG.debug("get_bgpvpn_connections called for user, "
                      "readable fields = %s" % readable_fields)
            return self._get_bgpvpn_connections_for_tenant(context.session,
                                                           context.tenant_id,
                                                           readable_fields)

    def _get_bgpvpn_connection(self, context, id):
        try:
            if context.is_admin:
                return self._get_resource(context, BGPVPNConnection, id)
            else:
                qry = context.session.query(BGPVPNConnection)
                return qry.filter_by(id=id, tenant_id=context.tenant_id).one()
        except exc.NoResultFound:
            raise BGPVPNConnectionNotFound(conn_id=id)

    def get_bgpvpn_connection(self, context, id, fields=None):
        bgpvpn_connection_db = self._get_bgpvpn_connection(context, id)
        LOG.debug("get_bgpvpn_connection called with fields = %s" % fields)

        if not context.is_admin:
            fields = self._get_user_readable_fields(fields)
            LOG.debug("get_bgpvpn_connection called for user,"
                      "readable fields = %s" % fields)

        return self._make_bgpvpn_connection_dict(bgpvpn_connection_db, fields)

    def update_bgpvpn_connection(self, context, id, bgpvpn_connection):
        bgpvpn_conn = bgpvpn_connection['bgpvpn_connection']
        fields = None

        LOG.debug("update_bgpvpn_connection called with %s for %s"
                  % (bgpvpn_connection, id))

        with context.session.begin(subtransactions=True):
            bgpvpn_connection_db = self._get_bgpvpn_connection(context, id)

            if bgpvpn_conn:
                # Filter only user writable attributes
                if not context.is_admin:
                    bgpvpn_conn = {
                        user_attr: bgpvpn_conn[user_attr]
                        for user_attr in self.USER_WRITABLE_ATTRIBUTES
                        if user_attr in bgpvpn_conn}
                    fields = self.USER_READABLE_ATTRIBUTES
                else:
                    # Format Route Target list to string
                    rt = self._rt_list2str(bgpvpn_conn['route_targets'])
                    if 'route_targets' in bgpvpn_conn:
                        bgpvpn_conn['route_targets'] = rt
                    if 'import_targets' in bgpvpn_conn:
                        i_rt = self._rt_list2str(bgpvpn_conn['import_targets'])
                        bgpvpn_conn['import_targets'] = i_rt
                    if 'export_targets' in bgpvpn_conn:
                        e_rt = self._rt_list2str(bgpvpn_conn['export_targets'])
                        bgpvpn_conn['export_targets'] = e_rt

                bgpvpn_connection_db.update(bgpvpn_conn)

        return self._make_bgpvpn_connection_dict(bgpvpn_connection_db, fields)

    def delete_bgpvpn_connection(self, context, id):
        with context.session.begin(subtransactions=True):
            bgpvpn_connection_db = self._get_resource(
                context,
                BGPVPNConnection,
                id)

            context.session.delete(bgpvpn_connection_db)

        return bgpvpn_connection_db

    def find_bgpvpn_connections_for_network(self, context, network_id):
        LOG.debug("get_bgpvpn_connections_for_network() called for "
                  "network %s" %
                  network_id)

        try:
            bgpvpn_connections = (context.session.query(BGPVPNConnection).
                                  filter(BGPVPNConnection.network_id ==
                                         network_id).
                                  all())
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_connection_dict(bvc)
                for bvc in bgpvpn_connections]
