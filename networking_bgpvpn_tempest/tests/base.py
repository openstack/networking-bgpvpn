# Copyright (c) 2015 Ericsson.
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

from networking_bgpvpn_tempest.services.bgpvpn import bgpvpn_client
from oslo_log import log as logging
import tempest.api.network.base as test
from tempest.common.utils import data_utils
from tempest import config

CONF = config.CONF

LOG = logging.getLogger(__name__)


class BaseBgpvpnTest(test.BaseNetworkTest):
    """Base class for the Bgpvpn tests that use the Tempest Neutron REST client

    Finally, it is assumed that the following option is defined in the
    [service_available] section of etc/tempest.conf

        bgpvpn as True

    """

    credentials = ['primary', 'admin', 'alt']
    bgpvpn_client = None
    bgpvpn_admin_client = None
    bgpvpn_alt_client = None

    @classmethod
    def resource_cleanup(cls):
        for bgpvpn in cls.bgpvpns:
            cls.bgpvpn_admin_client.delete_bgpvpn(bgpvpn['id'])
        super(BaseBgpvpnTest, cls).resource_cleanup()

    @classmethod
    def resource_setup(cls):
        cls.route_distinguishers = []
        cls.bgpvpns = []
        cls.bgpvpn_client = bgpvpn_client.BgpvpnClient(
            cls.os.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.os.default_params)
        cls.bgpvpn_admin_client = bgpvpn_client.BgpvpnClient(
            cls.os_adm.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.os_adm.default_params)
        cls.bgpvpn_alt_client = bgpvpn_client.BgpvpnClient(
            cls.alt_manager.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.alt_manager.default_params)
        super(BaseBgpvpnTest, cls).resource_setup()

    @classmethod
    def skip_checks(cls):
        super(BaseBgpvpnTest, cls).skip_checks()
        if not CONF.service_available.bgpvpn:
            raise cls.skipException("Bgpvpn support is required")

    def create_bgpvpn(self, client, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test-bgpvpn-')

        body = client.create_bgpvpn(**kwargs)
        bgpvpn = body['bgpvpn']
        self.bgpvpns.append(bgpvpn)
        return bgpvpn
