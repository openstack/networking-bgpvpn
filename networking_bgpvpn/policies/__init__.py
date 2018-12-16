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

import itertools

from networking_bgpvpn.policies import bgpvpn
from networking_bgpvpn.policies import network_association
from networking_bgpvpn.policies import port_association
from networking_bgpvpn.policies import router_association


def list_rules():
    return itertools.chain(
        bgpvpn.list_rules(),
        network_association.list_rules(),
        router_association.list_rules(),
        port_association.list_rules(),
    )
