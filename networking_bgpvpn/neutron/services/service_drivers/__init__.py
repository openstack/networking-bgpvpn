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
class BGPVPNDriver(object):
    """BGPVPNDriver interface for driver

    That driver interface does not persist BGPVPN data in any database. The
    driver need to do it by itself.
    """

    def __init__(self, service_plugin):
        self.service_plugin = service_plugin

    @property
    def service_type(self):
        pass

    @abc.abstractmethod
    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def get_bgpvpn_connections(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn_connection(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn_connection(self, context, id, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_connection(self, context, id):
        pass


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriverDB(object):
    """BGPVPNDriverDB interface for driver with database.

    That driver interface persists BGPVPN data in its database. The driver just
    need to take actions on its datapatch.
    """

    def __init__(self, service_plugin):
        self.service_plugin = service_plugin
        self.bgpvpn_db = bgpvpn_db.BGPVPNPluginDb()

    @property
    def service_type(self):
        pass

    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        bgpvpn_connection = self.bgpvpn_db.create_bgpvpn_connection(
            context, bgpvpn_connection)
        self._create_bgpvpn_connection(context, bgpvpn_connection)
        return bgpvpn_connection

    def get_bgpvpn_connections(self, context, filters=None, fields=None):
        return self.bgpvpn_db.get_bgpvpn_connections(context, filters, fields)

    def get_bgpvpn_connection(self, context, id, fields=None):
        return self.bgpvpn_db.get_bgpvpn_connection(context, id, fields)

    def update_bgpvpn_connection(self, context, id, bgpvpn_connection):
        old_bgpvpn_connection = self.get_bgpvpn_connection(context, id)

        bgpvpn_connection = self.bgpvpn_db.update_bgpvpn_connection(
            context, id, bgpvpn_connection)

        self._update_bgpvpn_connection(context, old_bgpvpn_connection,
                                       bgpvpn_connection)
        return bgpvpn_connection

    def delete_bgpvpn_connection(self, context, id):
        bgpvpn_connection = self.bgpvpn_db.delete_bgpvpn_connection(context,
                                                                    id)

        self._delete_bgpvpn_connection(context, bgpvpn_connection)

    @abc.abstractmethod
    def _create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def _update_bgpvpn_connection(self, context, old_bgpvpn_connection,
                                  bgpvpn_connection):
        pass

    @abc.abstractmethod
    def _delete_bgpvpn_connection(self, context, bgpvpn_connection):
        pass
