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
import tempest.api.network.base as test
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils

CONF = config.CONF


class BaseBgpvpnTest(test.BaseNetworkTest):
    """Base class for the Bgpvpn tests that use the Tempest Neutron REST client

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
            cls.os_primary.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.os_primary.default_params)
        cls.bgpvpn_admin_client = bgpvpn_client.BgpvpnClient(
            cls.os_admin.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.os_admin.default_params)
        cls.bgpvpn_alt_client = bgpvpn_client.BgpvpnClient(
            cls.os_alt.auth_provider,
            CONF.network.catalog_type,
            CONF.network.region or CONF.identity.region,
            endpoint_type=CONF.network.endpoint_type,
            build_interval=CONF.network.build_interval,
            build_timeout=CONF.network.build_timeout,
            **cls.os_alt.default_params)
        super(BaseBgpvpnTest, cls).resource_setup()

    @classmethod
    def skip_checks(cls):
        super(BaseBgpvpnTest, cls).skip_checks()
        if not utils.is_extension_enabled('bgpvpn', 'network'):
            msg = "Bgpvpn extension not enabled."
            raise cls.skipException(msg)

    def create_bgpvpn(self, client, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test-bgpvpn-')

        body = client.create_bgpvpn(**kwargs)
        bgpvpn = body['bgpvpn']
        self.bgpvpns.append(bgpvpn)
        return bgpvpn

    def delete_bgpvpn(self, client, bgpvpn):
        client.delete_bgpvpn(bgpvpn['id'])
        self.bgpvpns.remove(bgpvpn)
