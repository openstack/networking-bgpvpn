#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from neutron.conf.services import provider_configuration
from oslo_config import cfg


def list_service_provider():
    return [
        ('service_providers', provider_configuration.serviceprovider_opts),
    ]


_dummy_bgpvpn_provider = ':'.join([
    'BGPVPN', 'Dummy',
    'networking_bgpvpn.neutron.services.service_drivers.driver_api.'
    'BGPVPNDriver',
    'default'
])


# Set reasonable example for BGPVPN as a default value
def set_service_provider_default():
    cfg.set_defaults(provider_configuration.serviceprovider_opts,
                     service_provider=[_dummy_bgpvpn_provider])
