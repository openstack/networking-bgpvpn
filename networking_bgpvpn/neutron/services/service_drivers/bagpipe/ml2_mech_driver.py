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

from oslo_log import log

from neutron.callbacks import events
from neutron.callbacks import resources

from neutron import context as n_context
from neutron import manager

from networking_bgpvpn.neutron.services.common import constants
from neutron.plugins.ml2 import driver_api as api

LOG = log.getLogger(__name__)


class ML2BGPVPNMechanismDriver(api.MechanismDriver):
    """This driver notifies the BGPVPNPlugin driver of port events.

    It allows to notify the BGPVPN bagpipe driver that need to be aware
    of ports coming and going. It is used in Kilo instead of the Neutron
    registry callbacks.
    """

    def initialize(self):
        self.db_context = n_context.get_admin_context()

        # self.bgpvpn_driver = manager.NeutronManager.get_service_plugins().
        #    get(constants.BGPVPN).driver

        # if not isintance(self.bgpvpn_driver, bagpipe.BaGPipeBGPVPNDriver):
        #    raise Exception("ML2BGPVPNMechanismDriver can't work without "
        #                    "the bagpipe driver being enabled for the "
        #                    "BGPVPN service plugin")

    def update_port_postcommit(self, context):
        bgpvpnplugin = manager.NeutronManager.get_service_plugins().get(
            constants.BGPVPN)

        if bgpvpnplugin:
            bgpvpnplugin.driver.registry_port_updated(
                resources.PORT,  # currently unused by driver
                events.AFTER_UPDATE,  # currently unused by driver
                self,  # currently unused by driver
                context=self.db_context,
                port=context.current,
                original_port=context.original)

    def delete_port_precommit(self, context):
        bgpvpnplugin = manager.NeutronManager.get_service_plugins().get(
            constants.BGPVPN)

        if bgpvpnplugin:
            bgpvpnplugin.driver.registry_port_deleted(
                resources.PORT,  # currently unused by driver
                events.BEFORE_DELETE,  # currently unused by driver
                self,  # currently unused by driver
                context=self.db_context,
                port_id=context.current['id'])

    def create_port_postcommit(self, context):
        bgpvpnplugin = manager.NeutronManager.get_service_plugins().get(
            constants.BGPVPN)

        if bgpvpnplugin:
            bgpvpnplugin.driver.registry_port_created(
                resources.PORT,  # currently unused by driver
                events.AFTER_CREATE,  # currently unused by driver
                self,  # currently unused by driver
                context=self.db_context,
                port=context.current)
