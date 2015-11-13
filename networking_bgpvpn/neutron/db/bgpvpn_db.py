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
from oslo_log import log
from sqlalchemy import orm
from sqlalchemy.orm import exc

LOG = log.getLogger(__name__)


class BGPVPNNetAssociation(model_base.BASEV2, models_v2.HasId):
    """Represents the association between a bgpvpn and a network."""
    __tablename__ = 'bgpvpn_network_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id'),
                          nullable=False)
    network_id = sa.Column(sa.String(36),
                           sa.ForeignKey('networks.id'),
                           nullable=False)
    sa.UniqueConstraint(bgpvpn_id, network_id)
    network = orm.relationship("Network",
                               backref=orm.backref('bgpvpn_associations',
                                                   cascade='all'),
                               lazy='joined',)


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
    network_associations = orm.relationship("BGPVPNNetAssociation",
                                            backref="bgpvpn",
                                            lazy='joined',
                                            cascade='all, delete-orphan')


class BGPVPNNotFound(q_exc.NotFound):
    message = _("BGPVPN %(id)s could not be found")


class BGPVPNNetAssocNotFound(q_exc.NotFound):
    message = _("BGPVPN network association %(id)s could not be found"
                "for BGPVPN %(bgpvpn_id)s")


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

    def _make_bgpvpn_dict(self, bgpvpn_db, fields=None):
        net_list = [net_assocs.network_id for net_assocs in
                    bgpvpn_db.network_associations]
        res = {
            'id': bgpvpn_db['id'],
            'tenant_id': bgpvpn_db['tenant_id'],
            'networks': net_list,
            'name': bgpvpn_db['name'],
            'type': bgpvpn_db['type'],
            'route_targets':
                self._rtrd_str2list(bgpvpn_db['route_targets']),
            'route_distinguishers':
                self._rtrd_str2list(bgpvpn_db['route_distinguishers']),
            'import_targets':
                self._rtrd_str2list(bgpvpn_db['import_targets']),
            'export_targets':
                self._rtrd_str2list(bgpvpn_db['export_targets']),
            'auto_aggregate': bgpvpn_db['auto_aggregate']
        }
        return self._fields(res, fields)

    def create_bgpvpn(self, context, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']

        rt = self._rtrd_list2str(bgpvpn['route_targets'])
        i_rt = self._rtrd_list2str(bgpvpn['import_targets'])
        e_rt = self._rtrd_list2str(bgpvpn['export_targets'])
        rd = self._rtrd_list2str(bgpvpn.get('route_distinguishers', ''))

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
        return self._make_bgpvpn_dict(bgpvpn_db, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        bgpvpn = bgpvpn['bgpvpn']
        fields = None

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
        # Note : we could use added backref in the network table
        try:
            query = (context.session.query(BGPVPN).
                     join(BGPVPNNetAssociation).
                     filter(BGPVPNNetAssociation.network_id == network_id))
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_dict(bgpvpn)
                for bgpvpn in query.all()]

    def _make_net_assoc_dict(self, net_assoc_db, fields=None):
        res = {'id': net_assoc_db['id'],
               'bgpvpn_id': net_assoc_db['bgpvpn_id'],
               'network_id': net_assoc_db['network_id']}
        return self._fields(res, fields)

    def _get_net_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            query = self._model_query(context, BGPVPNNetAssociation)
            return query.filter(BGPVPNNetAssociation.id == assoc_id,
                                BGPVPNNetAssociation.bgpvpn_id == bgpvpn_id
                                ).one()
        except exc.NoResultFound:
            raise BGPVPNNetAssocNotFound(id=assoc_id, bgpvpn_id=bgpvpn_id)

    def create_net_assoc(self, context, bgpvpn_id, network_id):
        LOG.info(_LI("associating network %(net)s to bgpvpn %(bgpvpn)s"),
                 net=network_id, bgpvpn=bgpvpn_id)
        if not network_id:
            return
        with context.session.begin(subtransactions=True):
            net_assoc_db = BGPVPNNetAssociation(bgpvpn_id=bgpvpn_id,
                                                network_id=network_id)
            context.session.add(net_assoc_db)
        return self._make_net_assoc_dict(net_assoc_db)

    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        net_assoc_db = self._get_net_assoc(context, assoc_id, bgpvpn_id)
        return self._make_net_assoc_dict(net_assoc_db, fields=None)

    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        if not filters:
            filters = {}
        filters['bgpvpn_id'] = [bgpvpn_id]
        return self._get_collection(context, BGPVPNNetAssociation,
                                    self._make_net_assoc_dict,
                                    filters, fields)

    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.info(_LI("deleting network association %(id)s for"
                     "BGPVPN %(bgppvn)s"), id=assoc_id, bgpvpn=bgpvpn_id)
        with context.session.begin():
            net_assoc_db = self._get_net_assoc(context, assoc_id, bgpvpn_id)
            net_assoc = self._make_net_assoc_dict(net_assoc_db)
            context.session.delete(net_assoc_db)
        return net_assoc
