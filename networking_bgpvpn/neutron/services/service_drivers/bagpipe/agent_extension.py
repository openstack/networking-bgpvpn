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

import logging

from networking_bagpipe.agent import bagpipe_bgp_agent

from neutron_lib import constants as n_const

from neutron.agent.l2 import agent_extension

from neutron.plugins.ml2.drivers.openvswitch.agent.common \
    import constants as ovs_agt_constants
from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.native \
    import br_tun as native_br_tun
from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.ovs_ofctl \
    import br_tun as ofctl_br_tun

LOG = logging.getLogger(__name__)


class OVSBridgeIntercept(ofctl_br_tun.OVSTunnelBridge,
                         native_br_tun.OVSTunnelBridge):
    """Interception bridge

    Making sure that specific calls end up using the cookie-specific
    code of the cookie bridge.
    """

    def __init__(self, bridge):
        """OVSBridgeIntercept

        :param bridge: underlying cookie bridge
        :type bridge: OVSCookieBridge
        """
        self.bridge = bridge

        self.intercept_method("install_arp_responder")

    def intercept_method(self, method_name):
        # The code below will result in calling the <method_name> on the right
        # parent class of the underlying bridge, but with our instance passed
        # as 'self'; this ensure that when the said method ends up calling do
        # action_flows it will use the do_action_flows of the Cookie bridge
        # not the cookie-less do_action_flows
        #
        # the condition that must be respected is that this class is also
        # a subclass of all the bridge classes implementing the intercepted
        # functions
        #
        # the __getattr__ passthrough below ensures that our instance, passed
        # instead of contains everything that the underlying bridge contains
        #
        method = getattr(self.bridge.__class__, method_name, None)
        if method is not None:
            setattr(self, method_name,
                    lambda *args, **kwargs: method(self, *args, **kwargs))

    def __getattr__(self, name):
        return getattr(self.bridge, name)


class BagpipeBgpvpnAgentExtension(agent_extension.AgentCoreResourceExtension):

    def initialize(self, connection, driver_type):

        if driver_type != ovs_agt_constants.EXTENSION_DRIVER_TYPE:
            raise Exception("This extension is designed to work with the"
                            " OVS Agent")

        # Create an HTTP client for BaGPipe BGP component REST service
        self.bagpipe_bgp_agent = bagpipe_bgp_agent.BaGPipeBGPAgent(
            n_const.AGENT_TYPE_OVS,
            connection,
            int_br=self.int_br,
            tun_br=OVSBridgeIntercept(self.tun_br),
        )

    def consume_api(self, agent_api):
        self.int_br = agent_api.request_int_br()
        self.tun_br = agent_api.request_tun_br()

    def handle_port(self, context, data):
        pass

    def delete_port(self, context, data):
        pass
