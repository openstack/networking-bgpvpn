# Copyright (c) 2015 Cloudwatt.
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

import json
import uuid

from oslo_log import log
from oslo_utils import uuidutils

from neutron.common import exceptions as n_exc
from neutron.i18n import _LI

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from networking_bgpvpn.neutron.services.common import constants
from networking_bgpvpn.neutron.services.common import utils
from networking_bgpvpn.neutron.services.service_drivers import driver_api
from networking_bgpvpn.neutron.services.service_drivers.opencontrail import \
    exceptions as oc_exc
from networking_bgpvpn.neutron.services.service_drivers.opencontrail import \
    opencontrail_client

OPENCONTRAIL_BGPVPN_DRIVER_NAME = 'OpenContrail'

LOG = log.getLogger(__name__)


class OpenContrailBGPVPNDriver(driver_api.BGPVPNDriverBase):
    """BGP VPN Service Driver class for OpenContrail."""

    def __init__(self, service_plugin):
        super(OpenContrailBGPVPNDriver, self).__init__(service_plugin)
        LOG.debug("OpenContrailBGPVPNDriver service_plugin : %s",
                  service_plugin)

    def _get_opencontrail_api_client(self, context):
        return opencontrail_client.OpenContrailAPIBaseClient()

    def _locate_rt(self, oc_client, rt_fq_name):
        try:
            rt_uuid = oc_client.fqname_to_id('route-target', rt_fq_name)
        except oc_exc.OpenContrailAPINotFound:
            body = {
                'route-target': {
                    "fq_name": [':'.join(rt_fq_name)]
                }
            }
            rt_uuid = oc_client.create('Route Target', body)['uuid']

        return rt_uuid

    def _clean_route_targets(self, oc_client, rts_fq_name):
        for rt_fq_name in rts_fq_name:
            try:
                rt_uuid = oc_client.fqname_to_id('route-target', rt_fq_name)
            except oc_exc.OpenContrailAPINotFound:
                continue

            rt = oc_client.show('Route Target', rt_uuid)
            if 'routing_instance_back_refs' not in rt.keys():
                # rt not use anymore, remove it
                rt = oc_client.remove('Route Target', rt_uuid)

    def _update_rt_ri_association(self, oc_client, operation, ri_id,
                                  rt_fq_name, import_export=None):
        rt_uuid = self._locate_rt(oc_client, rt_fq_name)

        kwargs = {
            "operation": operation,
            "resource_type": "routing-instance",
            "resource_uuid": ri_id,
            "ref_type": "route-target",
            "ref_fq_name": rt_fq_name,
            "ref_uuid": rt_uuid,
            "attributes": {
                "import_export": import_export
            }
        }
        oc_client.ref_update(**kwargs)

        if operation == 'DELETE':
            self._clean_route_targets(oc_client, [rt_fq_name])

    def _get_ri_id_of_network(self, oc_client, network_id):
        try:
            network = oc_client.show('Virtual Network', network_id)
            ri_fq_name = network['fq_name'] + [network['fq_name'][-1]]
            for ri_ref in network.get('routing_instances', []):
                if ri_ref['to'] == ri_fq_name:
                    return ri_ref['uuid']
        except (oc_exc.OpenContrailAPINotFound, IndexError):
            raise n_exc.NetworkNotFound(net_id=network_id)
        raise n_exc.NetworkNotFound(net_id=network_id)

    def _set_bgpvpn_association(self, oc_client, operation, bgpvpn,
                                networks=[]):
        for network_id in networks:
            try:
                net_ri_id = self._get_ri_id_of_network(oc_client, network_id)
            except n_exc.NetworkNotFound:
                LOG.info(_LI("Network %s not found, cleanup route targets"),
                         network_id)
                rts_fq_name = (bgpvpn['route_targets'] +
                               bgpvpn['import_targets'] +
                               bgpvpn['export_targets'])
                rts_fq_name = [['target'] + rt.split(':') for rt in
                               rts_fq_name]
                self._clean_route_targets(oc_client, rts_fq_name)
                return bgpvpn
            if bgpvpn['type'] == constants.BGPVPN_L3:
                for rt in bgpvpn['route_targets']:
                    rt_fq_name = ['target'] + rt.split(':')
                    self._update_rt_ri_association(oc_client, operation,
                                                   net_ri_id, rt_fq_name)

                for rt in bgpvpn['import_targets']:
                    rt_fq_name = ['target'] + rt.split(':')
                    self._update_rt_ri_association(oc_client, operation,
                                                   net_ri_id, rt_fq_name,
                                                   import_export="import")

                for rt in bgpvpn['export_targets']:
                    rt_fq_name = ['target'] + rt.split(':')
                    self._update_rt_ri_association(oc_client, operation,
                                                   net_ri_id, rt_fq_name,
                                                   import_export="export")

        return bgpvpn

    # Check if tenant ID exists by reading it from the Contrail API;
    # if not, it sends an exception
    def _check_tenant_id(self, oc_client, tenant_id):
        try:
            tenant_id = str(uuid.UUID(tenant_id))
        except ValueError:
            raise oc_exc.OpenContrailMalformedUUID(uuid=tenant_id)
        oc_client.show('Project', tenant_id)

    def create_bgpvpn(self, context, bgpvpn):
        LOG.debug("create_bgpvpn_ called with %s" % bgpvpn)

        # Only support l3 technique
        if not bgpvpn['type']:
            bgpvpn['type'] = constants.BGPVPN_L3
        elif bgpvpn['type'] != constants.BGPVPN_L3:
            raise bgpvpn_ext.BGPVPNTypeNotSupported(
                driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME, type=bgpvpn['type'])

        # Does not support to set route distinguisher
        if 'route_distinguishers' in bgpvpn and bgpvpn['route_distinguishers']:
            raise bgpvpn_ext.BGPVPNRDNotSupported(
                driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)

        oc_client = self._get_opencontrail_api_client(context)

        # Check if tenant ID exists;
        # if not, it sends an exception
        self._check_tenant_id(oc_client, bgpvpn['tenant_id'])

        bgpvpn['id'] = uuidutils.generate_uuid()

        oc_client.kv_store('STORE', key=bgpvpn['id'], value={'bgpvpn': bgpvpn})

        return utils.make_bgpvpn_dict(bgpvpn)

    def get_bgpvpns(self, context, filters=None, fields=None):
        LOG.debug("get_bgpvpns called, fields = %s, filters = %s"
                  % (fields, filters))

        oc_client = self._get_opencontrail_api_client(context)

        bgpvpns = []
        for kv_dict in oc_client.kv_store('RETRIEVE'):
            try:
                value = json.loads(kv_dict['value'])
            except ValueError:
                continue
            if (isinstance(value, dict) and
                    'bgpvpn' in value and
                    utils.filter_resource(value['bgpvpn'], filters)):
                bgpvpn = value['bgpvpn']
                if not fields or 'networks' in fields:
                    bgpvpn['networks'] = \
                        [net_assoc['network_id'] for net_assoc in
                         self.get_net_assocs(context, bgpvpn['id'])]
                bgpvpns.append(utils.make_bgpvpn_dict(bgpvpn, fields))

        return bgpvpns

    def _clean_bgpvpn_assoc(self, oc_client, bgpvpn_id):
        for kv_dict in oc_client.kv_store('RETRIEVE'):
            try:
                value = json.loads(kv_dict['value'])
            except ValueError:
                continue
            if (isinstance(value, dict) and
                    'bgpvpn_net_assoc' in value and
                    value['bgpvpn_net_assoc']['bgpvpn_id'] == bgpvpn_id):
                assoc_id = value['bgpvpn_net_assoc']['id']
                oc_client.kv_store('DELETE', key=assoc_id)

    def get_bgpvpn(self, context, id, fields=None):
        LOG.debug("get_bgpvpn called for id %s with fields = %s"
                  % (id, fields))

        oc_client = self._get_opencontrail_api_client(context)

        try:
            bgpvpn = json.loads(oc_client.kv_store('RETRIEVE', key=id))
        except (oc_exc.OpenContrailAPINotFound, ValueError):
            raise bgpvpn.BGPVPNNotFound(id=id)

        if (not isinstance(bgpvpn, dict) or 'bgpvpn' not in bgpvpn):
            raise bgpvpn.BGPVPNNotFound(id=id)

        bgpvpn = bgpvpn['bgpvpn']
        if not fields or 'networks' in fields:
            bgpvpn['networks'] = [net_assoc['network_id'] for net_assoc in
                                  self.get_net_assocs(context, id)]
        return utils.make_bgpvpn_dict(bgpvpn, fields)

    def update_bgpvpn(self, context, id, new_bgpvpn):
        LOG.debug("update_bgpvpn called with %s for %s" % (new_bgpvpn, id))

        oc_client = self._get_opencontrail_api_client(context)

        old_bgpvpn = self.get_bgpvpn(context, id)
        networks = old_bgpvpn.get('networks', [])
        bgpvpn = old_bgpvpn.copy()
        bgpvpn.update(new_bgpvpn)

        (added_keys, removed_keys, changed_keys) = \
            utils.get_bgpvpn_differences(bgpvpn, old_bgpvpn)
        if not (added_keys or removed_keys or changed_keys):
            return utils.make_bgpvpn_dict(bgpvpn)

        # Does not support to update route distinguisher
        if 'route_distinguishers' in added_keys | removed_keys | changed_keys:
            raise bgpvpn_ext.BGPVPNRDNotSupported(
                driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)

        rt_keys = set(['route_targets',
                       'import_targets',
                       'export_targets'])

        if (rt_keys & added_keys or
                rt_keys & changed_keys or
                rt_keys & removed_keys):
            self._set_bgpvpn_association(oc_client, 'DELETE', old_bgpvpn,
                                         networks)
            self._set_bgpvpn_association(oc_client, 'ADD', bgpvpn, networks)

        oc_client.kv_store('STORE', key=id, value={'bgpvpn': bgpvpn})
        return utils.make_bgpvpn_dict(bgpvpn)

    def delete_bgpvpn(self, context, id):
        LOG.debug("delete_bgpvpn called for id %s" % id)

        bgpvpn = self.get_bgpvpn(context, id)
        networks = bgpvpn.get('networks', [])
        oc_client = self._get_opencontrail_api_client(context)

        self._set_bgpvpn_association(oc_client, 'DELETE', bgpvpn, networks)
        self._clean_bgpvpn_assoc(oc_client, id)
        oc_client.kv_store('DELETE', key=id)

    def create_net_assoc(self, context, bgpvpn_id, network_association):
        LOG.debug("create_net_assoc called for bgpvpn %s with network %s"
                  % (bgpvpn_id, network_association['network_id']))

        bgpvpn = self.get_bgpvpn(context, bgpvpn_id)
        oc_client = self._get_opencontrail_api_client(context)

        network_id = network_association['network_id']
        if network_id not in bgpvpn.get('networks', []):
            assoc_uuid = uuidutils.generate_uuid()
            self._set_bgpvpn_association(oc_client, 'ADD', bgpvpn,
                                         [network_id])

            assoc_dict = utils.make_net_assoc_dict(
                assoc_uuid, network_association['tenant_id'],
                bgpvpn_id, network_association['network_id'])
            oc_client.kv_store('STORE', key=assoc_uuid,
                               value={'bgpvpn_net_assoc': assoc_dict})
            return assoc_dict
        else:
            # the tuple (bgpvpn_id, network_id) is necessarily unique
            return self.get_net_assocs(context, bgpvpn_id,
                                       filters={'network_id': network_id})[0]

    def get_net_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        LOG.debug("get_net_assoc called for %s for BGPVPN %s, with fields = %s"
                  % (assoc_id, bgpvpn_id, fields))

        oc_client = self._get_opencontrail_api_client(context)

        try:
            net_assoc = json.loads(
                oc_client.kv_store('RETRIEVE', key=assoc_id))
        except (oc_exc.OpenContrailAPINotFound, ValueError):
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

        if (not isinstance(net_assoc, dict) or
                'bgpvpn_net_assoc' not in net_assoc):
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)
        net_assoc = net_assoc['bgpvpn_net_assoc']

        if net_assoc['bgpvpn_id'] != bgpvpn_id:
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

        # It the bgpvpn was deleted, the 'get_bgpvpn' will clean all related
        # associations and replaces BGPVPNNotFound by a BGPVPNNetAssocNotFound
        try:
            get_fields = ['tenant_id', 'route_targets', 'import_targets',
                          'export_targets']
            bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'],
                                     fields=get_fields)
        except bgpvpn.BGPVPNNotFound:
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

        # If the network was delete all bgpvpn related association should be
        # deleted also
        try:
            oc_client.id_to_fqname(net_assoc['network_id'])
        except oc_exc.OpenContrailAPINotFound:
            self._set_bgpvpn_association(oc_client, 'DELETE', bgpvpn,
                                         [net_assoc['network_id']])
            oc_client.kv_store('DELETE', key=assoc_id)
            raise bgpvpn_ext.BGPVPNNetAssocNotFound(id=assoc_id,
                                                    bgpvpn_id=bgpvpn_id)

        net_assoc = utils.make_net_assoc_dict(net_assoc['id'],
                                              net_assoc['tenant_id'],
                                              net_assoc['bgpvpn_id'],
                                              net_assoc['network_id'],
                                              fields)
        return net_assoc

    def get_net_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        LOG.debug("get_net_assocs called for bgpvpn %s, fields = %s, "
                  "filters = %s" % (bgpvpn_id, fields, filters))

        oc_client = self._get_opencontrail_api_client(context)

        get_fields = ['tenant_id', 'route_targets', 'import_targets',
                      'export_targets']
        bgpvpn = self.get_bgpvpn(context, bgpvpn_id, fields=get_fields)

        bgpvpn_net_assocs = []
        for kv_dict in oc_client.kv_store('RETRIEVE'):
            try:
                value = json.loads(kv_dict['value'])
            except ValueError:
                continue
            if (isinstance(value, dict) and
                    'bgpvpn_net_assoc' in value and
                    utils.filter_resource(value['bgpvpn_net_assoc'],
                                          filters) and
                    value['bgpvpn_net_assoc']['bgpvpn_id'] == bgpvpn_id):
                net_assoc = value['bgpvpn_net_assoc']
                # If the network was delete all bgpvpn related association
                # should be deleted also
                try:
                    oc_client.id_to_fqname(net_assoc['network_id'])
                except oc_exc.OpenContrailAPINotFound:
                    self._set_bgpvpn_association(oc_client, 'DELETE', bgpvpn,
                                                 [net_assoc['network_id']])
                    oc_client.kv_store('DELETE', key=net_assoc['id'])
                    continue
                net_assoc = utils.make_net_assoc_dict(net_assoc['id'],
                                                      net_assoc['tenant_id'],
                                                      net_assoc['bgpvpn_id'],
                                                      net_assoc['network_id'],
                                                      fields)
                bgpvpn_net_assocs.append(net_assoc)

        return bgpvpn_net_assocs

    def delete_net_assoc(self, context, assoc_id, bgpvpn_id):
        LOG.debug("delete_net_assoc called for %s" % assoc_id)
        net_assoc = self.get_net_assoc(context, assoc_id, bgpvpn_id)
        fields = ['type', 'route_targets', 'import_targets', 'export_targets']
        bgpvpn = self.get_bgpvpn(context, net_assoc['bgpvpn_id'],
                                 fields=fields)
        oc_client = self._get_opencontrail_api_client(context)

        self._set_bgpvpn_association(oc_client, 'DELETE', bgpvpn,
                                     [net_assoc['network_id']])
        oc_client.kv_store('DELETE', key=assoc_id)

        return net_assoc

    def create_router_assoc(self, context, bgpvpn_id, router_association):
        raise bgpvpn_ext.BGPVPNRouterAssociationNotSupported(
            driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)

    def get_router_assoc(self, context, assoc_id, bgpvpn_id, fields=None):
        raise bgpvpn_ext.BGPVPNRouterAssociationNotSupported(
            driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)

    def get_router_assocs(self, context, bgpvpn_id, filters=None, fields=None):
        raise bgpvpn_ext.BGPVPNRouterAssociationNotSupported(
            driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)

    def delete_router_assoc(self, context, assoc_id, bgpvpn_id):
        raise bgpvpn_ext.BGPVPNRouterAssociationNotSupported(
            driver=OPENCONTRAIL_BGPVPN_DRIVER_NAME)
