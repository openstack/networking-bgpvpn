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

import types

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
from neutron.plugins.ml2.drivers.openvswitch.agent import \
    ovs_agent_extension_api

LOG = logging.getLogger(__name__)


class OVSBridgeIntercept(ofctl_br_tun.OVSTunnelBridge,
                         native_br_tun.OVSTunnelBridge):
    """Interception bridge

    Making sure that specific calls end up using the cookie-specific
    code of the cookie bridge.
    """

    _COOKIE_BRIDGE_METHODS = [
        'add_flow',
        'del_flow',
        'mod_flows',
        'do_action_flows',
    ]

    def __init__(self, bridge):
        """OVSBridgeIntercept

        :param bridge: underlying cookie bridge
        :type bridge: OVSCookieBridge
        """
        # The inheritance from ofctl_br_tun.OVSTunnelBridge and
        # ofctl_br_tun.OVSTunnelBridge is here to allow calling their
        # methods with a OVSBridgeIntercept 'self'
        # This does not result in actual calls to propagate to these mother
        # classes via simple inheritance, because of the special code in
        # __getattribute__ that redirect these calls with a vooded self

        if not isinstance(bridge, ovs_agent_extension_api.OVSCookieBridge):
            raise Exception("Bridge has to be an OVSCookieBridge")

        self.bridge = bridge

    def __getattribute__(self, name):
        cookie_bridge = object.__getattribute__(self, 'bridge')

        # classes not using add_flow/del_flow etc, but reading
        # self._default_cookie, such as native_br_tun.OVSTunnelBridge
        # will get the right cookie:
        if name == "_default_cookie":
            return cookie_bridge._cookie

        # the cookie-specific methods need to be mapped to the CookieBridge
        if name in OVSBridgeIntercept._COOKIE_BRIDGE_METHODS:
            return getattr(cookie_bridge, name)

        # cookie_bridge.bridge is the bridge behind it and should be an
        # OVSTunnelBridge
        attr = getattr(cookie_bridge.bridge.__class__, name, None)
        # flake8: noqa
        # pylint: disable=unidiomatic-typecheck
        if type(attr) is types.MethodType:
            # The code below will result in calling the <method_name> on the
            # right parent class of the underlying bridge, but with our
            # instance passed as 'self'; this ensure that when the said method
            # ends up calling add/del/mod_flows, it will use the method of the
            # OVSCookieBridge, that uses the extension-specific cookie.
            #
            # The condition that must be respected is that OVSBridgeIntercept
            # is a subclass of all the bridge classes implementing the
            # intercepted functions.
            #
            # the __getattribute__ implemenation below ensures that our
            # instance passed instead of self, will still behave like the
            # underlying bridge.
            return lambda *args, **kwargs: attr(self, *args, **kwargs)

        return getattr(cookie_bridge, name)


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
            tun_br=OVSBridgeIntercept(self.tun_br),
        )

    def consume_api(self, agent_api):
        self.int_br = agent_api.request_int_br()
        self.tun_br = agent_api.request_tun_br()

    def handle_port(self, context, data):
        pass

    def delete_port(self, context, data):
        pass
