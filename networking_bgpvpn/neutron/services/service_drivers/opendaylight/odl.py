#
# Copyright (C) 2015 Ericsson India Global Services Pvt Ltd.
#
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
#

import requests

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

from networking_odl.common import client as odl_client

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.service_drivers import driver_api

cfg.CONF.import_group('ml2_odl', 'networking_odl.common.config')

LOG = logging.getLogger(__name__)
BGPVPNS = 'bgpvpns'
OPENDAYLIGHT_BGPVPN_DRIVER_NAME = 'OpenDaylight'


class OpenDaylightBgpvpnDriver(driver_api.BGPVPNDriver):

    """OpenDaylight BGPVPN Driver

    This code is the backend implementation for the OpenDaylight BGPVPN
    driver for Openstack Neutron.
    """

    def __init__(self, service_plugin):
        LOG.debug("Initializing OpenDaylight BGPVPN driver")
        super(OpenDaylightBgpvpnDriver, self).__init__(service_plugin)
        self.service_plugin = service_plugin

        self.client = odl_client.OpenDaylightRestClient.create_client()

    def _scrub_rd_list(self, bgpvpn):
        if len(bgpvpn['route_distinguishers']) > 1:
            bgpvpn['route_distinguishers'] = bgpvpn['route_distinguishers'][0]

    def create_bgpvpn_precommit(self, context, bgpvpn):
        pass

    def create_bgpvpn_postcommit(self, context, bgpvpn):
        url = BGPVPNS
        try:
            self._scrub_rd_list(bgpvpn)
            self.client.sendjson('post', url, {BGPVPNS[:-1]: bgpvpn})
        except requests.exceptions.RequestException:
            with excutils.save_and_reraise_exception():
                # delete from db
                d_bgpvpn = self.bgpvpn_db.delete_bgpvpn(context, bgpvpn['id'])
                LOG.debug("Deleted bgpvpn %s from db", d_bgpvpn)

    def delete_bgpvpn_postcommit(self, context, bgpvpn):
        url = BGPVPNS + '/' + bgpvpn['id']
        self.client.sendjson('delete', url, None)

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        url = BGPVPNS + '/' + bgpvpn['id']
        self.client.sendjson('put', url, {BGPVPNS[:-1]: bgpvpn})

    def create_net_assoc_precommit(self, context, net_assoc):
        bgpvpns = self.bgpvpn_db.find_bgpvpns_for_network(
            context, net_assoc['network_id'])
        if len(bgpvpns) > 1:
            raise bgpvpn_ext.BGPVPNNetworkAssocExistsAnotherBgpvpn(
                driver=OPENDAYLIGHT_BGPVPN_DRIVER_NAME,
                network=net_assoc['network_id'],
                bgpvpn=bgpvpns[0]['id'])

    def create_net_assoc_postcommit(self, context, net_assoc):
        bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
        url = BGPVPNS + '/' + bgpvpn['id']
        self._scrub_rd_list(bgpvpn)
        try:
            self.client.sendjson('put', url, {BGPVPNS[:-1]: bgpvpn})
        except requests.exceptions.RequestException:
            with excutils.save_and_reraise_exception():
                # delete from db
                d_netassoc = self.bgpvpn_db.delete_net_assoc(
                    context, net_assoc['id'], net_assoc['bgpvpn_id'])
                LOG.debug("Deleted net_assoc %s from db", d_netassoc)

    def delete_net_assoc_postcommit(self, context, net_assoc):
        bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'])
        url = BGPVPNS + '/' + bgpvpn['id']
        self.client.sendjson('put', url, {BGPVPNS[:-1]: bgpvpn})

    def create_router_assoc_precommit(self, context, router_assoc):
        associated_routers = self.get_router_assocs(context,
                                                    router_assoc['bgpvpn_id'])
        for assoc_router in associated_routers:
            if(router_assoc["router_id"] != assoc_router["router_id"]):
                raise bgpvpn_ext.BGPVPNMultipleRouterAssocNotSupported(
                    driver=OPENDAYLIGHT_BGPVPN_DRIVER_NAME)

    def create_router_assoc_postcommit(self, context, router_assoc):
        bgpvpn = self.get_bgpvpn(context, router_assoc['bgpvpn_id'])
        url = BGPVPNS + '/' + bgpvpn['id']
        self._scrub_rd_list(bgpvpn)
        try:
            self.client.sendjson('put', url, {BGPVPNS[:-1]: bgpvpn})
        except requests.exceptions.RequestException:
            with excutils.save_and_reraise_exception():
                # delete from db
                d_routerassoc = self.bgpvpn_db.delete_router_assoc(
                    context, router_assoc['id'], router_assoc['bgpvpn_id'])
                LOG.debug("Deleted router_assoc %s from db", d_routerassoc)

    def delete_router_assoc_postcommit(self, context, router_assoc):
        bgpvpn = self.get_bgpvpn(context, router_assoc['bgpvpn_id'])
        url = BGPVPNS + '/' + bgpvpn['id']
        self.client.sendjson('put', url, {BGPVPNS[:-1]: bgpvpn})
