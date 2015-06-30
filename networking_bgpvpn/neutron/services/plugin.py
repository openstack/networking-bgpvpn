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

from neutron.common import exceptions as n_exc
from neutron.db import servicetype_db as st_db
from neutron.i18n import _LI
from neutron import manager
from neutron.services import provider_configuration as pconf
from neutron.services import service_base
from oslo_log import log

from networking_bgpvpn.neutron.extensions.bgpvpn import BGPVPNPluginBase
from networking_bgpvpn.neutron.services.common import constants

LOG = log.getLogger(__name__)


class BGPVPNPlugin(BGPVPNPluginBase):
    supported_extension_aliases = ["bgpvpn"]
    path_prefix = "/bgpvpn"

    def __init__(self):
        super(BGPVPNPlugin, self).__init__()

        service_type_manager = st_db.ServiceTypeManager.get_instance()
        # Need to also look into /etc/neutron/networking_bgpvpn.conf for
        # service_provider definitions:
        service_type_manager.add_provider_configuration(
            constants.BGPVPN,
            pconf.ProviderConfiguration('networking_bgpvpn'))

        # Load the default driver
        drivers, default_provider = service_base.load_drivers(constants.BGPVPN,
                                                              self)
        LOG.info(_LI("BGP VPN Service Plugin using Service Driver: %s"),
                 default_provider)
        self.driver = drivers[default_provider]

    def _validate_network_body(self, context, bgpvpn_id, network_body):
        # Check that the tenant of the network is the same as the tenant of the
        # bgpvpn resource
        if (not network_body or 'network_id' not in network_body):
            msg = 'no network specified'
            raise n_exc.BadRequest(resource='bgpvpn', msg=msg)
        plugin = manager.NeutronManager.get_plugin()
        return plugin.get_network(context, network_body['network_id'])

    def get_plugin_type(self):
        return constants.BGPVPN

    def get_plugin_description(self):
        return "Neutron BGPVPN Service Plugin"

    def create_bgpvpn(self, context, bgpvpn):
        return self.driver.create_bgpvpn(context, bgpvpn)

    def get_bgpvpns(self, context, filters=None, fields=None):
        return self.driver.get_bgpvpns(context, filters, fields)

    def get_bgpvpn(self, context, id, fields=None):
        return self.driver.get_bgpvpn(context, id, fields)

    def update_bgpvpn(self, context, id, bgpvpn):
        return self.driver.update_bgpvpn(context, id, bgpvpn)

    def delete_bgpvpn(self, context, id):
        self.driver.delete_bgpvpn(context, id)

    def associate_network(self, context, id, network_body):
        net = self._validate_network_body(context, id, network_body)
        bgpvpn = self.get_bgpvpn(context, id)
        if not net['tenant_id'] == bgpvpn['tenant_id']:
            msg = 'network doesn\'t belong to the bgpvpn owner'
            raise n_exc.NotAuthorized(resource='bgpvpn', msg=msg)

        self.driver.associate_network(context, id, net['id'])

    def disassociate_network(self, context, id, network_body):
        net = self._validate_network_body(context, id, network_body)
        self.driver.disassociate_network(context, id, net['id'])
