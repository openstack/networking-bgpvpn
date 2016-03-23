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
import six

from networking_bgpvpn.neutron.db import bgpvpn_db


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverBase(object):
    """BGPVPNDriver interface for driver

    That driver interface does not persist BGPVPN data in any database. The
    driver needs to do it by itself.
    """

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

    def __init__(self, service_plugin):
        super(BGPVPNDriverDBMixin, self).__init__(service_plugin)
        self.bgpvpn_db = bgpvpn_db.BGPVPNPluginDb()

    def create_bgpvpn(self, context, bgpvpn):
        with context.session.begin(subtransactions=True):
            bgpvpn = self.bgpvpn_db.create_bgpvpn(
                context, bgpvpn)
            self.create_bgpvpn_precommit(context, bgpvpn)
        self.create_bgpvpn_postcommit(context, bgpvpn)
        return bgpvpn

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self.bgpvpn_db.get_bgpvpns(context, filters, fields)

    def get_bgpvpn(self, context, id, fields=None):
        return self.bgpvpn_db.get_bgpvpn(context, id, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        old_bgpvpn = self.get_bgpvpn(context, id)
        with context.session.begin(subtransactions=True):
            bgpvpn = self.bgpvpn_db.update_bgpvpn(
                context, id, bgpvpn)
            self.update_bgpvpn_precommit(context, old_bgpvpn, bgpvpn)

        self.update_bgpvpn_postcommit(context, old_bgpvpn, bgpvpn)
        return bgpvpn

    def delete_bgpvpn(self, context, id):
        bgpvpn = self.bgpvpn_db.delete_bgpvpn(context, id)
        self.delete_bgpvpn_postcommit(context, bgpvpn)

    def create_net_assoc(self, context, bgpvpn_id, network_association):
        with context.session.begin(subtransactions=True):
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
        net_assoc = self.bgpvpn_db.delete_net_assoc(context,
                                                    assoc_id,
                                                    bgpvpn_id)
        self.delete_net_assoc_postcommit(context, net_assoc)

    def create_router_assoc(self, context, bgpvpn_id, router_association):
        with context.session.begin(subtransactions=True):
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
        router_assoc = self.bgpvpn_db.delete_router_assoc(context,
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
    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        pass

    @abc.abstractmethod
    def update_bgpvpn_precommit(self, context, old_bgpvpn, bgpvpn):
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
    def delete_net_assoc_postcommit(self, context, net_assoc):
        pass

    @abc.abstractmethod
    def create_router_assoc_precommit(self, context, router_assoc):
        pass

    @abc.abstractmethod
    def create_router_assoc_postcommit(self, context, router_assoc):
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
    def __init__(self, service_plugin):
        super(BGPVPNDriver, self).__init__(service_plugin)

    def create_bgpvpn_precommit(self, context, bgpvpn):
        pass

    def create_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    def update_bgpvpn_precommit(self, context, old_bgpvpn, bgpvpn):
        pass

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        pass

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        pass

    def create_net_assoc_precommit(self, context, net_assoc):
        pass

    def create_net_assoc_postcommit(self, context, net_assoc):
        pass

    def delete_net_assoc_postcommit(self, context, net_assoc):
        pass

    def create_router_assoc_precommit(self, context, router_assoc):
        pass

    def create_router_assoc_postcommit(self, context, router_assoc):
        pass

    def delete_router_assoc_postcommit(self, context, router_assoc):
        pass
