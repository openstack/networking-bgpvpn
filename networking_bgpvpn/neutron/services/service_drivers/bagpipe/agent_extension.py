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

"""
L2 Agent extension to support bagpipe networking-bgpvpn driver RPCs in the
OpenVSwitch agent
"""

from networking_bagpipe.agent import bagpipe_bgp_agent

from neutron_lib import constants as n_const

from neutron.agent.l2 import agent_extension

from neutron.plugins.ml2.drivers.openvswitch.agent.common \
    import constants as ovs_agt_constants


class BagpipeBgpvpnAgentExtension(agent_extension.AgentCoreResourceExtension):

    def initialize(self, connection, driver_type):

        if driver_type != ovs_agt_constants.EXTENSION_DRIVER_TYPE:
            raise Exception("This extension is currently works only with the"
                            " OVS Agent")

        # Create an HTTP client for BaGPipe BGP component REST service
        self.bagpipe_bgp_agent = bagpipe_bgp_agent.BaGPipeBGPAgent(
            n_const.AGENT_TYPE_OVS,
            connection,
            int_br=self.int_br,
            tun_br=self.tun_br,
        )

    def consume_api(self, agent_api):
        self.int_br = agent_api.request_int_br()
        self.tun_br = agent_api.request_tun_br()

    def handle_port(self, context, data):
        pass

    def delete_port(self, context, data):
        pass
