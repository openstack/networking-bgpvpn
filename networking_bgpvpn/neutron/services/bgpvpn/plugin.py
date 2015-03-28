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

from networking_bgpvpn.neutron.db.bgpvpn import bgpvpn_db
from neutron.i18n import _LI
from neutron.openstack.common import log
from neutron.plugins.common import constants
from neutron.services import service_base

LOG = log.getLogger(__name__)


class BGPVPNPlugin(bgpvpn_db.BGPVPNPluginDb):
    supported_extension_aliases = ["bgpvpn"]

    def __init__(self):
        super(BGPVPNPlugin, self).__init__()
        # Load the service driver from neutron.conf.
        drivers, default_provider = service_base.load_drivers(
            constants.BGPVPN, self)
        LOG.info(_LI("BGP VPN Service Plugin using Service Driver: %s"),
                 default_provider)
        self.driver = drivers[default_provider]

    def get_plugin_type(self):
        return constants.BGPVPN

    def get_plugin_description(self):
        return "Neutron BGP VPN connection Service Plugin"

    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        bgpvpn_connection = super(
            BGPVPNPlugin, self).create_bgpvpn_connection(context,
                                                         bgpvpn_connection)

        self.driver.create_bgpvpn_connection(context, bgpvpn_connection)
        return bgpvpn_connection

    def delete_bgpvpn_connection(self, context, bgpvpn_conn_id):
        bgpvpn_connection = super(
            BGPVPNPlugin, self).delete_bgpvpn_connection(context,
                                                         bgpvpn_conn_id)

        self.driver.delete_bgpvpn_connection(context, bgpvpn_connection)

    def update_bgpvpn_connection(self,
                                 context, bgpvpn_conn_id,
                                 bgpvpn_connection):
        old_bgpvpn_connection = self.get_bgpvpn_connection(context,
                                                           bgpvpn_conn_id)

        bgpvpn_connection = super(
            BGPVPNPlugin, self).update_bgpvpn_connection(context,
                                                         bgpvpn_conn_id,
                                                         bgpvpn_connection)

        self.driver.update_bgpvpn_connection(context, old_bgpvpn_connection,
                                             bgpvpn_connection)
        return bgpvpn_connection
