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

import sys

import eventlet
eventlet.monkey_patch()

from neutron.common import config as common_config
from neutron.common import constants as q_const
from neutron.common import utils as n_utils
from neutron.i18n import _LE

from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.ovs_ofctl import \
    br_int
from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.ovs_ofctl import \
    br_phys
from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.ovs_ofctl import \
    br_tun
from neutron.plugins.ml2.drivers.openvswitch.agent.ovs_neutron_agent import \
    create_agent_config_map
from neutron.plugins.ml2.drivers.openvswitch.agent.ovs_neutron_agent import \
    OVSNeutronAgent
from neutron.plugins.ml2.drivers.openvswitch.agent.ovs_neutron_agent import \
    prepare_xen_compute
from neutron.plugins.ml2.drivers.openvswitch.agent.ovs_neutron_agent import \
    validate_local_ip

from oslo_config import cfg
from oslo_log import log as logging

from networking_bagpipe.agent import bagpipe_bgp_agent

LOG = logging.getLogger(__name__)
cfg.CONF.import_group('AGENT', 'neutron.plugins.ml2.drivers.openvswitch.'
                      'agent.common.config')
cfg.CONF.import_group('OVS', 'neutron.plugins.ml2.drivers.openvswitch.agent.'
                      'common.config')


class OVSBagpipeNeutronAgent(OVSNeutronAgent):

    def __init__(self, *args, **kwargs):
        super(OVSBagpipeNeutronAgent, self).__init__(*args, **kwargs)

        # Creates an HTTP client for BaGPipe BGP component REST service
        self.bgp_agent = (bagpipe_bgp_agent.BaGPipeBGPAgent(
            q_const.AGENT_TYPE_OVS,
            int_br=self.int_br,
            tun_br=self.tun_br,
            patch_int_ofport=self.patch_int_ofport,
            local_vlan_map=self.local_vlan_map,
            setup_entry_for_arp_reply=self.setup_entry_for_arp_reply)
        )

        self.bgp_agent.setup_rpc(self.endpoints, self.connection, self.topic)


def main():
    # this is from neutron.plugins.ml2.drivers.openvswitch.agent.main
    common_config.init(sys.argv[1:])
    n_utils.log_opt_values(LOG)
    common_config.setup_logging()
    # this is from neutron.plugins.ml2.drivers.openvswitch.agent.openflow.
    # ovs_ofctl.main
    bridge_classes = {
        'br_int': br_int.OVSIntegrationBridge,
        'br_phys': br_phys.OVSPhysicalBridge,
        'br_tun': br_tun.OVSTunnelBridge,
    }
    # this is from neutron.plugins.ml2.drivers.openvswitch.agent.
    # ovs_neutron_agent
    try:
        agent_config = create_agent_config_map(cfg.CONF)
    except ValueError:
        LOG.exception(_LE("Agent failed to create agent config map"))
        raise SystemExit(1)
    prepare_xen_compute()
    validate_local_ip(agent_config['local_ip'])
    try:
        agent = OVSBagpipeNeutronAgent(bridge_classes, **agent_config)
    except (RuntimeError, ValueError) as e:
        LOG.error(_LE("%s Agent terminated!"), e)
        sys.exit(1)
    agent.daemon_loop()
