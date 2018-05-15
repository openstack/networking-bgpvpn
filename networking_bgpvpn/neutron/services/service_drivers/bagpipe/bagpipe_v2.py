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

from sqlalchemy import orm

from neutron.api.rpc.callbacks import events as rpc_events
from neutron.api.rpc.handlers import resources_rpc
from neutron.db import api as db_api
from neutron.db.models import external_net

from neutron_lib.api.definitions import bgpvpn_routes_control as bgpvpn_rc_def
from neutron_lib.api.definitions import bgpvpn_vni as bgpvpn_vni_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib import exceptions as n_exc
from neutron_lib.plugins import directory

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import utils
from networking_bgpvpn.neutron.services.service_drivers import driver_api

from networking_bagpipe.objects import bgpvpn as bgpvpn_objects

LOG = logging.getLogger(__name__)


BAGPIPE_DRIVER_NAME = "bagpipe"


class BGPVPNExternalNetAssociation(n_exc.NeutronException):
    message = _("driver does not support associating an external"
                "network to a BGPVPN")


@db_api.context_manager.reader
def network_is_external(context, net_id):
    try:
        context.session.query(external_net.ExternalNetwork).filter_by(
            network_id=net_id).one()
        return True
    except orm.exc.NoResultFound:
        return False


def _log_callback_processing_exception(resource, event, trigger, kwargs, e):
    LOG.exception("Error during notification processing "
                  "%(resource)s %(event)s, %(trigger)s, "
                  "%(kwargs)s: %(exc)s",
                  {'trigger': trigger,
                   'resource': resource,
                   'event': event,
                   'kwargs': kwargs,
                   'exc': e})


@registry.has_registry_receivers
class BaGPipeBGPVPNDriver(driver_api.BGPVPNDriverRC):

    """BGPVPN Service Driver class for BaGPipe"""

    more_supported_extension_aliases = [bgpvpn_rc_def.ALIAS,
                                        bgpvpn_vni_def.ALIAS]

    def __init__(self, service_plugin):
        super(BaGPipeBGPVPNDriver, self).__init__(service_plugin)

        self._push_rpc = resources_rpc.ResourcesPushRpcApi()

    def _push_association(self, context, association, event_type):
        self._push_associations(context, [association], event_type)

    def _push_associations(self, context, associations, event_type):
        if not associations:
            return
        for assoc in associations:
            LOG.debug("pushing %s %s (%s)", event_type, assoc, assoc.bgpvpn)
        self._push_rpc.push(context, associations, event_type)

    def _common_precommit_checks(self, bgpvpn):
        # No support yet for specifying route distinguishers
        if bgpvpn.get('route_distinguishers', None):
            raise bgpvpn_ext.BGPVPNRDNotSupported(driver=BAGPIPE_DRIVER_NAME)

    def create_bgpvpn_precommit(self, context, bgpvpn):
        self._common_precommit_checks(bgpvpn)

    def delete_bgpvpn_precommit(self, context, bgpvpn):
        self._push_bgpvpn_associations(context, bgpvpn['id'],
                                       rpc_events.DELETED)

    def update_bgpvpn_precommit(self, context, old_bgpvpn, bgpvpn):
        self._common_precommit_checks(bgpvpn)

    def update_bgpvpn_postcommit(self, context, old_bgpvpn, bgpvpn):
        (added_keys, removed_keys, changed_keys) = (
            utils.get_bgpvpn_differences(bgpvpn, old_bgpvpn))
        ATTRIBUTES_TO_IGNORE = set(['name'])
        moving_keys = added_keys | removed_keys | changed_keys
        if len(moving_keys ^ ATTRIBUTES_TO_IGNORE):
            self._push_bgpvpn_associations(context, bgpvpn['id'],
                                           rpc_events.UPDATED)

    def _push_bgpvpn_associations(self, context, bgpvpn_id, event_type):
        self._push_associations(
            context,
            (bgpvpn_objects.BGPVPNNetAssociation.get_objects(
                context,
                bgpvpn_id=bgpvpn_id) +
             bgpvpn_objects.BGPVPNRouterAssociation.get_objects(
                context,
                bgpvpn_id=bgpvpn_id)
             ),
            event_type)

    def create_net_assoc_precommit(self, context, net_assoc):
        if network_is_external(context, net_assoc['network_id']):
            raise BGPVPNExternalNetAssociation()

    def create_net_assoc_postcommit(self, context, net_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNNetAssociation.get_object(
                context,
                id=net_assoc['id']),
            rpc_events.CREATED)

    def delete_net_assoc_precommit(self, context, net_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNNetAssociation.get_object(
                context,
                id=net_assoc['id']),
            rpc_events.DELETED)

    def create_port_assoc_postcommit(self, context, port_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNPortAssociation.get_object(
                context,
                id=port_assoc['id']),
            rpc_events.CREATED)

    def update_port_assoc_postcommit(self, context,
                                     old_port_assoc, port_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNPortAssociation.get_object(
                context,
                id=port_assoc['id']),
            rpc_events.UPDATED)

    def delete_port_assoc_precommit(self, context, port_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNPortAssociation.get_object(
                context,
                id=port_assoc['id']),
            rpc_events.DELETED)

    def create_router_assoc_postcommit(self, context, router_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNRouterAssociation.get_object(
                context,
                id=router_assoc['id']),
            rpc_events.CREATED)

    def delete_router_assoc_precommit(self, context, router_assoc):
        self._push_association(
            context,
            bgpvpn_objects.BGPVPNRouterAssociation.get_object(
                context,
                id=router_assoc['id']),
            rpc_events.DELETED)

    @log_helpers.log_method_call
    def notify_router_interface_created(self, context, router_id, net_id):
        # update associations for the networks on which the router was plugged
        self._push_associations(
            context,
            (bgpvpn_objects.BGPVPNNetAssociation.get_objects(
                context,
                network_id=net_id) +
             bgpvpn_objects.BGPVPNRouterAssociation.get_objects(
                context,
                network_id=net_id)),
            rpc_events.UPDATED)

    @log_helpers.log_method_call
    def notify_router_interface_deleted(self, context, router_id, net_id):
        # update associations for the networks on which the router was plugged
        associations = (
            bgpvpn_objects.BGPVPNNetAssociation.get_objects(
                context,
                network_id=net_id) +
            bgpvpn_objects.BGPVPNRouterAssociation.get_objects(
                context,
                router_id=router_id)
        )

        # NOTE(tmorin): the gateway_mac information in these notifications
        # will not be None, as it should, because unfortunately the OVObjects
        # are created before the DB is updated after interface removal.
        # So we reprocess them to empty this field...
        for assoc in associations:
            for subnet in assoc.all_subnets(net_id):
                subnet['gateway_mac'] = None

        self._push_associations(context, associations, rpc_events.UPDATED)

    @registry.receives(resources.ROUTER_INTERFACE, [events.AFTER_CREATE])
    @log_helpers.log_method_call
    def registry_router_interface_created(self, resource, event, trigger,
                                          **kwargs):
        try:
            context = kwargs['context']
            router_id = kwargs['router_id']
            net_id = kwargs['port']['network_id']
            self.notify_router_interface_created(context, router_id, net_id)
        except Exception as e:
            _log_callback_processing_exception(resource, event, trigger,
                                               kwargs, e)

    # need to subscribe to router interface *before*_delete
    # because after delete, we can't build the OVO objects from the DB anymore
    @registry.receives(resources.ROUTER_INTERFACE, [events.BEFORE_DELETE])
    @log_helpers.log_method_call
    def registry_router_interface_deleted(self, resource, event, trigger,
                                          **kwargs):
        try:
            context = kwargs['context']
            # for router_interface after_delete, in stable/newton, the
            # callback does not include the router_id directly, but we find
            # it in the port device_id
            router_id = kwargs['router_id']
            subnet_id = kwargs['subnet_id']
            # find the network for this subnet
            network_id = directory.get_plugin().get_subnet(
                context, subnet_id)['network_id']
            self.notify_router_interface_deleted(
                context, router_id, network_id)
        except Exception as e:
            _log_callback_processing_exception(resource, event, trigger,
                                               kwargs, e)
