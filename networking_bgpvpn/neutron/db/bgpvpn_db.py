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

from oslo_utils import uuidutils

from neutron.common import exceptions as q_exc
from neutron.db import common_db_mixin
from neutron.db import model_base
from neutron.db import models_v2

from neutron.i18n import _
from neutron.i18n import _LI
from neutron.i18n import _LW

from oslo_log import log
from sqlalchemy import orm
from sqlalchemy.orm import exc

LOG = log.getLogger(__name__)


class BGPVPNNetAssociation(model_base.BASEV2):
    """Represents the association between a bgpvpn and a network."""
    __tablename__ = 'bgpvpn_net_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id', ondelete="CASCADE"),
                          primary_key=True)
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id', ondelete="CASCADE"),
                           primary_key=True)


class BGPVPN(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    """Represents a BGPVPN Object."""
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.Enum("l2", "l3",
                             name="bgpvpn_type"),
                     nullable=False)
    route_targets = sa.Column(sa.String(255), nullable=False)
    import_targets = sa.Column(sa.String(255), nullable=False)
    export_targets = sa.Column(sa.String(255), nullable=False)
    route_distinguishers = sa.Column(sa.String(255), nullable=False)
    auto_aggregate = sa.Column(sa.Boolean(), nullable=False)
    networks = orm.relationship(models_v2.Network,
                                secondary=BGPVPNNetAssociation.__tablename__,
                                lazy='joined')


class BGPVPNNotFound(q_exc.NotFound):
    message = _("BGPVPN %(id)s could not be found")


class BGPVPNMissingRouteTarget(q_exc.BadRequest):
    message = _("BGPVPN could not be created. Missing one of"
                " route_targets, import_targets or export_targets attribute")


class BGPVPNPluginDb(common_db_mixin.CommonDbMixin):
    """BGPVPN service plugin database class using SQLAlchemy models."""

    def _rtrd_list2str(self, list):
        """Format Route Target list to string"""
        if not list:
            return ''

        return ','.join(list)

    def _rtrd_str2list(self, str):
        """Format Route Target string to list"""
        if not str:
            return []

        return str.split(',')

    def _get_bgpvpns_for_tenant(self, session, tenant_id, fields):
        try:
            qry = session.query(BGPVPN)
            bgpvpns = qry.filter_by(tenant_id=tenant_id)
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_dict(bgpvpn, fields=fields)
                for bgpvpn in bgpvpns]

    def _make_bgpvpn_dict(self, bgpvpn, fields=None):
        net_list = [net.id for net in bgpvpn['networks']]
        res = {
            'id': bgpvpn['id'],
            'tenant_id': bgpvpn['tenant_id'],
            'networks': net_list,
            'name': bgpvpn['name'],
            'type': bgpvpn['type'],
            'route_targets':
                self._rtrd_str2list(bgpvpn['route_targets']),
            'route_distinguishers':
                self._rtrd_str2list(bgpvpn['route_distinguishers']),
            'import_targets':
                self._rtrd_str2list(bgpvpn['import_targets']),
            'export_targets':
                self._rtrd_str2list(bgpvpn['export_targets']),
            'auto_aggregate': bgpvpn['auto_aggregate']
        }
        return self._fields(res, fields)

    def create_bgpvpn(self, context, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']

        # Check that route_targets is not empty
        if (not bgpvpn['route_targets']):
            raise BGPVPNMissingRouteTarget
        else:
            rt = self._rtrd_list2str(bgpvpn['route_targets'])
            i_rt = self._rtrd_list2str(bgpvpn['import_targets'])
            e_rt = self._rtrd_list2str(bgpvpn['export_targets'])
            rd = self._rtrd_list2str(
                bgpvpn.get('route_distinguishers', ''))

        tenant_id = self._get_tenant_id_for_create(context, bgpvpn)

        with context.session.begin(subtransactions=True):
            bgpvpn_db = BGPVPN(
                id=uuidutils.generate_uuid(),
                tenant_id=tenant_id,
                name=bgpvpn['name'],
                type=bgpvpn['type'],
                route_targets=rt,
                import_targets=i_rt,
                export_targets=e_rt,
                route_distinguishers=rd,
                auto_aggregate=bgpvpn['auto_aggregate']
            )
            context.session.add(bgpvpn_db)

        return self._make_bgpvpn_dict(bgpvpn_db)

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self._get_collection(context, BGPVPN,
                                    self._make_bgpvpn_dict,
                                    filters=filters, fields=fields)

    def _get_bgpvpn(self, context, id):
        try:
            return self._get_by_id(context, BGPVPN, id)
        except exc.NoResultFound:
            raise BGPVPNNotFound(id=id)

    def get_bgpvpn(self, context, id, fields=None):
        bgpvpn_db = self._get_bgpvpn(context, id)
        LOG.debug("get_bgpvpn called with fields = %s" % fields)
        return self._make_bgpvpn_dict(bgpvpn_db, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']
        fields = None

        LOG.debug("update_bgpvpn called with %s for %s"
                  % (bgpvpn, id))
        with context.session.begin(subtransactions=True):
            bgpvpn_db = self._get_bgpvpn(context, id)
            if bgpvpn:
                # Format Route Target lists to string
                if 'route_targets' in bgpvpn:
                    rt = self._rtrd_list2str(bgpvpn['route_targets'])
                    bgpvpn['route_targets'] = rt
                if 'import_targets' in bgpvpn:
                    i_rt = self._rtrd_list2str(bgpvpn['import_targets'])
                    bgpvpn['import_targets'] = i_rt
                if 'export_targets' in bgpvpn:
                    e_rt = self._rtrd_list2str(bgpvpn['export_targets'])
                    bgpvpn['export_targets'] = e_rt
                if 'route_distinguishers' in bgpvpn:
                    rd = self._rtrd_list2str(
                        bgpvpn['route_distinguishers'])
                    bgpvpn['route_distinguishers'] = rd

                bgpvpn_db.update(bgpvpn)
        return self._make_bgpvpn_dict(bgpvpn_db, fields)

    def delete_bgpvpn(self, context, id):
        with context.session.begin(subtransactions=True):
            bgpvpn_db = self._get_bgpvpn(context, id)
            bgpvpn = self._make_bgpvpn_dict(bgpvpn_db)
            context.session.delete(bgpvpn_db)
        return bgpvpn

    def find_bgpvpns_for_network(self, context, network_id):
        LOG.debug("find_bgpvpns_for_network() called for "
                  "network %s" % network_id)
        try:
            query = (context.session.query(BGPVPN).
                     join(BGPVPNNetAssociation).
                     filter(BGPVPNNetAssociation.network_id == network_id))
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_dict(bvc)
                for bvc in query.all()]

    def associate_network(self, context, bgpvpn_id, network_id):
        LOG.info(_LI("associating network %s"), network_id)
        if not network_id:
            return
        with context.session.begin(subtransactions=True):
            net_assoc = BGPVPNNetAssociation(bgpvpn_id=bgpvpn_id,
                                             network_id=network_id)
            context.session.add(net_assoc)

    def disassociate_network(self, context, bgpvpn_id, network_id):
        LOG.info(_LI("disassociating network %s"), network_id)
        if not network_id:
            return
        with context.session.begin():
            try:
                assocs = (context.session.query(BGPVPNNetAssociation).
                          filter(BGPVPNNetAssociation.network_id ==
                                 network_id))
            except exc.NoResultFound:
                LOG.warning(_LW("network %(net_id)s was not associated to"
                                " bgpvpn %(bgpvpn_id)s"),
                            {'net_id': network_id,
                             'bgpvpn_id': bgpvpn_id})
                return
            assocs.delete()
