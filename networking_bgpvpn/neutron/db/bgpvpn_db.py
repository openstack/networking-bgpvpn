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

from neutron.db import common_db_mixin
from neutron.db import model_base
from neutron.db import models_v2

from neutron.i18n import _LI
from neutron.i18n import _LW

from oslo_db import exception as db_exc
from oslo_log import log
from oslo_utils import uuidutils

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import utils

LOG = log.getLogger(__name__)


class BGPVPNNetAssociation(model_base.BASEV2, models_v2.HasId,
                           models_v2.HasTenant):
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


class BGPVPNRouterAssociation(model_base.BASEV2, models_v2.HasId,
                              models_v2.HasTenant):
    """Represents the association between a bgpvpn and a router."""
    __tablename__ = 'bgpvpn_router_associations'

    bgpvpn_id = sa.Column(sa.String(36),
                          sa.ForeignKey('bgpvpns.id'),
                          nullable=False)
    router_id = sa.Column(sa.String(36),
                          sa.ForeignKey('routers.id'),
                          nullable=False)
    sa.UniqueConstraint(bgpvpn_id, router_id)
    router = orm.relationship("Router",
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
    network_associations = orm.relationship("BGPVPNNetAssociation",
                                            backref="bgpvpn",
                                            lazy='joined',
                                            cascade='all, delete-orphan')
    router_associations = orm.relationship("BGPVPNRouterAssociation",
                                           backref="bgpvpn",
                                           lazy='joined',
                                           cascade='all, delete-orphan')


class BGPVPNPluginDb(common_db_mixin.CommonDbMixin):
    """BGPVPN service plugin database class using SQLAlchemy models."""

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
        router_list = [router_assocs.router_id for router_assocs in
                       bgpvpn_db.router_associations]
        res = {
            'id': bgpvpn_db['id'],
            'tenant_id': bgpvpn_db['tenant_id'],
            'networks': net_list,
            'routers': router_list,
            'name': bgpvpn_db['name'],
            'type': bgpvpn_db['type'],
            'route_targets':
                utils.rtrd_str2list(bgpvpn_db['route_targets']),
            'route_distinguishers':
                utils.rtrd_str2list(bgpvpn_db['route_distinguishers']),
            'import_targets':
                utils.rtrd_str2list(bgpvpn_db['import_targets']),
            'export_targets':
                utils.rtrd_str2list(bgpvpn_db['export_targets'])
        }
        return self._fields(res, fields)

    def create_bgpvpn(self, context, bgpvpn):
        rt = utils.rtrd_list2str(bgpvpn['route_targets'])
        i_rt = utils.rtrd_list2str(bgpvpn['import_targets'])
        e_rt = utils.rtrd_list2str(bgpvpn['export_targets'])
        rd = utils.rtrd_list2str(bgpvpn.get('route_distinguishers', ''))

        with context.session.begin(subtransactions=True):
            bgpvpn_db = BGPVPN(
                id=uuidutils.generate_uuid(),
                tenant_id=bgpvpn['tenant_id'],
                name=bgpvpn['name'],
                type=bgpvpn['type'],
                route_targets=rt,
                import_targets=i_rt,
                export_targets=e_rt,
                route_distinguishers=rd
            )
            context.session.add(bgpvpn_db)

        return self._make_bgpvpn_dict(bgpvpn_db)

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self._get_collection(context, BGPVPN, self._make_bgpvpn_dict,
                                    filters=filters, fields=fields)

    def _get_bgpvpn(self, context, id):
        try:
            return self._get_by_id(context, BGPVPN, id)
        except exc.NoResultFound:
            raise bgpvpn_ext.BGPVPNNotFound(id=id)

    def get_bgpvpn(self, context, id, fields=None):
        bgpvpn_db = self._get_bgpvpn(context, id)
        return self._make_bgpvpn_dict(bgpvpn_db, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        fields = None
        with context.session.begin(subtransactions=True):
            bgpvpn_db = self._get_bgpvpn(context, id)
            if bgpvpn:
                # Format Route Target lists to string
                if 'route_targets' in bgpvpn:
                    rt = utils.rtrd_list2str(bgpvpn['route_targets'])
                    bgpvpn['route_targets'] = rt
                if 'import_targets' in bgpvpn:
                    i_rt = utils.rtrd_list2str(bgpvpn['import_targets'])
                    bgpvpn['import_targets'] = i_rt
                if 'export_targets' in bgpvpn:
                    e_rt = utils.rtrd_list2str(bgpvpn['export_targets'])
                    bgpvpn['export_targets'] = e_rt
                if 'route_distinguishers' in bgpvpn:
                    rd = utils.rtrd_list2str(bgpvpn['route_distinguishers'])
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
               'tenant_id': net_assoc_db['tenant_id'],
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
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

    def create_net_assoc(self, context, bgpvpn_id, net_assoc):
        try:
            with context.session.begin(subtransactions=True):
                net_assoc_db = BGPVPNNetAssociation(
                    tenant_id=net_assoc['tenant_id'],
                    bgpvpn_id=bgpvpn_id,
                    network_id=net_assoc['network_id'])
                context.session.add(net_assoc_db)
            return self._make_net_assoc_dict(net_assoc_db)
        except db_exc.DBDuplicateEntry:
            LOG.warning(_LW("network %(net_id)s is already associated to "
                            "BGPVPN %(bgpvpn_id)s"),
                        {'net_id': net_assoc['network_id'],
                         'bgpvpn_id': bgpvpn_id})
            raise bgpvpn_ext.BGPVPNNetAssocAlreadyExists(
                bgpvpn_id=bgpvpn_id, net_id=net_assoc['network_id'])

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
        LOG.info(_LI("deleting network association %(id)s for "
                     "BGPVPN %(bgpvpn)s"), {'id': assoc_id,
                                            'bgpvpn': bgpvpn_id})
        with context.session.begin():
            net_assoc_db = self._get_net_assoc(context, assoc_id, bgpvpn_id)
            net_assoc = self._make_net_assoc_dict(net_assoc_db)
            context.session.delete(net_assoc_db)
        return net_assoc

    def find_bgpvpns_for_router(self, context, router_id):
        try:
            query = (context.session.query(BGPVPN).
                     join(BGPVPNRouterAssociation).
                     filter(BGPVPNRouterAssociation.router_id == router_id))
        except exc.NoResultFound:
            return

        return [self._make_bgpvpn_dict(bgpvpn)
                for bgpvpn in query.all()]

    def _make_router_assoc_dict(self, router_assoc_db, fields=None):
        res = {'id': router_assoc_db['id'],
               'tenant_id': router_assoc_db['tenant_id'],
               'bgpvpn_id': router_assoc_db['bgpvpn_id'],
               'router_id': router_assoc_db['router_id']}
        return self._fields(res, fields)

    def _get_router_assoc(self, context, assoc_id, bgpvpn_id):
        try:
            query = self._model_query(context, BGPVPNRouterAssociation)
            return query.filter(BGPVPNRouterAssociation.id == assoc_id,
                                BGPVPNRouterAssociation.bgpvpn_id == bgpvpn_id
                                ).one()
        except exc.NoResultFound:
            raise bgpvpn_ext.BGPVPNRouterAssocNotFound(id=assoc_id,
                                                       bgpvpn_id=bgpvpn_id)

    def create_router_assoc(self, context, bgpvpn_id, router_association):
        router_id = router_association['router_id']
        try:
            with context.session.begin(subtransactions=True):
                router_assoc_db = BGPVPNRouterAssociation(
                    tenant_id=router_association['tenant_id'],
                    bgpvpn_id=bgpvpn_id,
                    router_id=router_id)
                context.session.add(router_assoc_db)
            return self._make_router_assoc_dict(router_assoc_db)
        except db_exc.DBDuplicateEntry:
            LOG.warning(_LW("router %(router_id)s is already associated to "
                            "BGPVPN %(bgpvpn_id)s"),
                        {'router_id': router_id,
                         'bgpvpn_id': bgpvpn_id})
            raise bgpvpn_ext.BGPVPNRouterAssocAlreadyExists(
                bgpvpn_id=bgpvpn_id, router_id=router_association['router_id'])

    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        router_assoc_db = self._get_router_assoc(context, assoc_id, bgpvpn_id)
        return self._make_router_assoc_dict(router_assoc_db, fields)

    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        if not filters:
            filters = {}
        filters['bgpvpn_id'] = [bgpvpn_id]
        return self._get_collection(context, BGPVPNRouterAssociation,
                                    self._make_router_assoc_dict,
                                    filters, fields)

    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.info(_LI("deleting router association %(id)s for "
                     "BGPVPN %(bgpvpn)s"),
                 {'id': assoc_id, 'bgpvpn': bgpvpn_id})
        with context.session.begin():
            router_assoc_db = self._get_router_assoc(context, assoc_id,
                                                     bgpvpn_id)
            router_assoc = self._make_router_assoc_dict(router_assoc_db)
            context.session.delete(router_assoc_db)
        return router_assoc
