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

import abc
import copy
import six

from neutron.db import api as db_api

from networking_bgpvpn.neutron.db import bgpvpn_db
from networking_bgpvpn.neutron.extensions \
    import bgpvpn_routes_control as bgpvpn_rc


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverBase(object):
    """BGPVPNDriver interface for driver

    That driver interface does not persist BGPVPN data in any database. The
    driver needs to do it by itself.
    """
    more_supported_extension_aliases = []

    def __init__(self, service_plugin):
        self.service_plugin = service_plugin

    @property
    def service_type(self):
        pass

    @abc.abstractmethod
    def create_bgpvpn(self, context, bgpvpn):
        pass

    @abc.abstractmethod
    def get_bgpvpns(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn(self, context, id, bgpvpn):
        pass

    @abc.abstractmethod
    def delete_bgpvpn(self, context, id):
        pass

    @abc.abstractmethod
    def create_net_assoc(self, bgpvpn_id, network_association):
        pass

    @abc.abstractmethod
    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        pass

    @abc.abstractmethod
    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        pass

    @abc.abstractmethod
    def create_router_assoc(self, context, bgpvpn_id, router_association):
        pass

    @abc.abstractmethod
    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        pass

    @abc.abstractmethod
    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        pass


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverDBMixin(BGPVPNDriverBase):
    """BGPVPNDriverDB Mixin to provision the database on behalf of the driver

    That driver interface persists BGPVPN data in its database and forwards
    the result to postcommit methods
    """

    def __init__(self, *args, **kwargs):
        super(BGPVPNDriverDBMixin, self).__init__(*args, **kwargs)
        self.bgpvpn_db = bgpvpn_db.BGPVPNPluginDb()

    def create_bgpvpn(self, context, bgpvpn):
        with db_api.context_manager.writer.using(context):
            bgpvpn = self.bgpvpn_db.create_bgpvpn(
                context, bgpvpn)
            self.create_bgpvpn_precommit(context, bgpvpn)
        self.create_bgpvpn_postcommit(context, bgpvpn)
        return bgpvpn

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self.bgpvpn_db.get_bgpvpns(context, filters, fields)

    def get_bgpvpn(self, context, id, fields=None):
        return self.bgpvpn_db.get_bgpvpn(context, id, fields)

    def update_bgpvpn(self, context, id, bgpvpn_delta):
        old_bgpvpn = self.get_bgpvpn(context, id)
        with db_api.context_manager.writer.using(context):
            new_bgpvpn = copy.deepcopy(old_bgpvpn)
            new_bgpvpn.update(bgpvpn_delta)
            self.update_bgpvpn_precommit(context, old_bgpvpn, new_bgpvpn)
            bgpvpn = self.bgpvpn_db.update_bgpvpn(context, id, bgpvpn_delta)
        self.update_bgpvpn_postcommit(context, old_bgpvpn, bgpvpn)
        return bgpvpn

    def delete_bgpvpn(self, context, id):
        with db_api.context_manager.writer.using(context):
            bgpvpn = self.bgpvpn_db.get_bgpvpn(context, id)
            self.delete_bgpvpn_precommit(context, bgpvpn)
            self.bgpvpn_db.delete_bgpvpn(context, id)
        self.delete_bgpvpn_postcommit(context, bgpvpn)

    def create_net_assoc(self, context, bgpvpn_id, network_association):
        with db_api.context_manager.writer.using(context):
            assoc = self.bgpvpn_db.create_net_assoc(context,
                                                    bgpvpn_id,
                                                    network_association)
            self.create_net_assoc_precommit(context, assoc)
        self.create_net_assoc_postcommit(context, assoc)
        return assoc

    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        return self.bgpvpn_db.get_net_assoc(context, assoc_id, bgpvpn_id,
                                            fields)

    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        return self.bgpvpn_db.get_net_assocs(context, bgpvpn_id,
                                             filters, fields)

    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        with db_api.context_manager.writer.using(context):
            net_assoc = self.bgpvpn_db.get_net_assoc(context,
                                                     assoc_id,
                                                     bgpvpn_id)

            self.delete_net_assoc_precommit(context, net_assoc)
            self.bgpvpn_db.delete_net_assoc(context,
                                            assoc_id,
                                            bgpvpn_id)
        self.delete_net_assoc_postcommit(context, net_assoc)

    def create_router_assoc(self, context, bgpvpn_id, router_association):
        with db_api.context_manager.writer.using(context):
            assoc = self.bgpvpn_db.create_router_assoc(context, bgpvpn_id,
                                                       router_association)
            self.create_router_assoc_precommit(context, assoc)
        self.create_router_assoc_postcommit(context, assoc)
        return assoc

    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        return self.bgpvpn_db.get_router_assoc(context, assoc_id,
                                               bgpvpn_id, fields)

    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        return self.bgpvpn_db.get_router_assocs(context, bgpvpn_id,
                                                filters, fields)

    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        with db_api.context_manager.writer.using(context):
            router_assoc = self.bgpvpn_db.get_router_assoc(context,
                                                           assoc_id,
                                                           bgpvpn_id)
            self.delete_router_assoc_precommit(context, router_assoc)
            self.bgpvpn_db.delete_router_assoc(context,
                                               assoc_id,
                                               bgpvpn_id)

        self.delete_router_assoc_postcommit(context, router_assoc)

    @abc.abstractmethod
    def create_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    @abc.abstractmethod
    def create_bgpvpn_precommit(self, context, bgpvpn):
        pass

    @abc.abstractmethod
    def update_bgpvpn_postcommit(self, context, old_bgpvpn, new_bgpvpn):
        pass

    @abc.abstractmethod
    def update_bgpvpn_precommit(self, context, old_bgpvpn, new_bgpvpn):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    @abc.abstractmethod
    def create_net_assoc_precommit(self, context, net_assoc):
        pass

    @abc.abstractmethod
    def create_net_assoc_postcommit(self, context, net_assoc):
        pass

    @abc.abstractmethod
    def delete_net_assoc_precommit(self, context, net_assoc):
        pass

    @abc.abstractmethod
    def delete_net_assoc_postcommit(self, context, net_assoc):
        pass

    @abc.abstractmethod
    def create_router_assoc_precommit(self, context, router_assoc):
        pass

    @abc.abstractmethod
    def create_router_assoc_postcommit(self, context, router_assoc):
        pass

    @abc.abstractmethod
    def delete_router_assoc_precommit(self, context, router_assoc):
        pass

    @abc.abstractmethod
    def delete_router_assoc_postcommit(self, context, router_assoc):
        pass


class BGPVPNDriver(BGPVPNDriverDBMixin):
    """BGPVPNDriver interface for driver with database.

    Each bgpvpn driver that needs a database persistency should inherit
    from this driver.
    It can overload needed methods from the following pre/postcommit methods.
    Any exception raised during a precommit method will result in not having
    related records in the databases.
    """

    def create_bgpvpn_precommit(self, context, bgpvpn):
        pass

    def create_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    def update_bgpvpn_precommit(self, context, old_bgpvpn, new_bgpvpn):
        pass

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, new_bgpvpn):
        pass

    def delete_bgpvpn_precommit(self, context, bgpvpn):
        pass

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    def create_net_assoc_precommit(self, context, net_assoc):
        pass

    def create_net_assoc_postcommit(self, context, net_assoc):
        pass

    def delete_net_assoc_precommit(self, context, net_assoc):
        pass

    def delete_net_assoc_postcommit(self, context, net_assoc):
        pass

    def create_router_assoc_precommit(self, context, router_assoc):
        pass

    def create_router_assoc_postcommit(self, context, router_assoc):
        pass

    def delete_router_assoc_precommit(self, context, router_assoc):
        pass

    def delete_router_assoc_postcommit(self, context, router_assoc):
        pass


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverRCBase(BGPVPNDriverBase):
    """Base class for drivers implementing the bgpvpn-routes-control API ext"""

    more_supported_extension_aliases = [
        bgpvpn_rc.Bgpvpn_routes_control.get_alias()]

    def __init__(self, *args, **kwargs):
        super(BGPVPNDriverRCBase, self).__init__(*args, **kwargs)

    @abc.abstractmethod
    def update_router_assoc(self, context, assoc_id, router_association):
        pass

    @abc.abstractmethod
    def create_port_assoc(self, bgpvpn_id, port_association):
        pass

    @abc.abstractmethod
    def get_port_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        pass

    @abc.abstractmethod
    def get_port_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def update_port_assoc(self, context, assoc_id, port_association):
        pass

    @abc.abstractmethod
    def delete_port_assoc(self, context, assoc_id, bgpvpn_id):
        pass


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverRCDBMixin(BGPVPNDriverRCBase, BGPVPNDriverDBMixin):
    """BGPVPNDriverDBMixin with DB operations for bgpvpn-route-control ext."""

    def __init__(self, *args, **xargs):
        BGPVPNDriverDBMixin.__init__(self, *args, **xargs)

    def update_router_assoc(self, context, assoc_id, bgpvpn_id, router_assoc):
        old_router_assoc = self.get_router_assoc(context, assoc_id, bgpvpn_id)
        with db_api.context_manager.writer.using(context):
            router_assoc = self.bgpvpn_db.update_router_assoc(context,
                                                              assoc_id,
                                                              bgpvpn_id,
                                                              router_assoc)
            self.update_router_assoc_precommit(context,
                                               old_router_assoc, router_assoc)
        self.update_router_assoc_postcommit(context,
                                            old_router_assoc, router_assoc)
        return router_assoc

    @abc.abstractmethod
    def update_router_assoc_precommit(self, context,
                                      old_router_assoc, router_assoc):
        pass

    @abc.abstractmethod
    def update_router_assoc_postcommit(self, context,
                                       old_router_assoc, router_assoc):
        pass

    def create_port_assoc(self, context, bgpvpn_id, port_association):
        with db_api.context_manager.writer.using(context):
            port_assoc = self.bgpvpn_db.create_port_assoc(context, bgpvpn_id,
                                                          port_association)
            self.create_port_assoc_precommit(context, port_assoc)
        self.create_port_assoc_postcommit(context, port_assoc)
        return port_assoc

    @abc.abstractmethod
    def create_port_assoc_precommit(self, context, port_assoc):
        pass

    @abc.abstractmethod
    def create_port_assoc_postcommit(self, context, port_assoc):
        pass

    def get_port_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        return self.bgpvpn_db.get_port_assoc(context, assoc_id,
                                             bgpvpn_id, fields)

    def get_port_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        return self.bgpvpn_db.get_port_assocs(context, bgpvpn_id,
                                              filters, fields)

    def update_port_assoc(self, context, assoc_id, bgpvpn_id, port_assoc):
        old_port_assoc = self.get_port_assoc(context, assoc_id, bgpvpn_id)
        with db_api.context_manager.writer.using(context):
            port_assoc = self.bgpvpn_db.update_port_assoc(context, assoc_id,
                                                          bgpvpn_id,
                                                          port_assoc)
            self.update_port_assoc_precommit(context,
                                             old_port_assoc, port_assoc)
        self.update_port_assoc_postcommit(context,
                                          old_port_assoc, port_assoc)
        return port_assoc

    @abc.abstractmethod
    def update_port_assoc_precommit(self, context,
                                    old_port_assoc, port_assoc):
        pass

    @abc.abstractmethod
    def update_port_assoc_postcommit(self, context,
                                     old_port_assoc, port_assoc):
        pass

    def delete_port_assoc(self, context, assoc_id, bgpvpn_id):
        with db_api.context_manager.writer.using(context):
            port_assoc = self.bgpvpn_db.get_port_assoc(context,
                                                       assoc_id,
                                                       bgpvpn_id)
            self.delete_port_assoc_precommit(context, port_assoc)
            self.bgpvpn_db.delete_port_assoc(context,
                                             assoc_id,
                                             bgpvpn_id)
        self.delete_port_assoc_postcommit(context, port_assoc)

    @abc.abstractmethod
    def delete_port_assoc_precommit(self, context, port_assoc):
        pass

    @abc.abstractmethod
    def delete_port_assoc_postcommit(self, context, port_assoc):
        pass


class BGPVPNDriverRC(BGPVPNDriverRCDBMixin, BGPVPNDriver):
    """Base class for a DB driver supporting bgpvpn-routes-control API ext."""

    def update_router_assoc_precommit(self, context,
                                      old_router_assoc, router_assoc):
        pass

    def update_router_assoc_postcommit(self, context,
                                       old_router_assoc, router_assoc):
        pass

    def create_port_assoc_precommit(self, context, port_assoc):
        pass

    def create_port_assoc_postcommit(self, context, port_assoc):
        pass

    def update_port_assoc_precommit(self, context,
                                    old_port_assoc, port_assoc):
        pass

    def update_port_assoc_postcommit(self, context,
                                     old_port_assoc, port_assoc):
        pass

    def delete_port_assoc_precommit(self, context, port_assoc):
        pass

    def delete_port_assoc_postcommit(self, context, port_assoc):
        pass
