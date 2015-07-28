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

from networking_bgpvpn.neutron.services import service_drivers
from oslo_log import log

LOG = log.getLogger(__name__)


class dummyBGPVPNDriver(service_drivers.BGPVPNDriver):
    """dummy BGP VPN connection Service Driver class."""

    def __init__(self, service_plugin):
        super(dummyBGPVPNDriver, self).__init__(service_plugin)
        LOG.debug("dummyBGPVPNDriver service_plugin : %s", service_plugin)

    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    def get_bgpvpn_connections(self, context, filters=None, fields=None):
        pass

    def get_bgpvpn_connection(self, context, id, fields=None):
        pass

    def update_bgpvpn_connection(self, context, id, bgpvpn_connection):
        pass

    def delete_bgpvpn_connection(self, context, id):
        pass


class dummyBGPVPNDriverDB(service_drivers.BGPVPNDriverDB):
    """dummy BGP VPN connection Service Driver class with database."""

    def __init__(self, service_plugin):
        super(dummyBGPVPNDriverDB, self).__init__(service_plugin)
        LOG.debug("dummyBGPVPNDriverDB service_plugin : %s", service_plugin)

    def _create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    def _update_bgpvpn_connection(self, context, old_bgpvpn_connection,
                                  bgpvpn_connection):
        pass

    def _delete_bgpvpn_connection(self, context, bgpvpn_connection):
        pass
