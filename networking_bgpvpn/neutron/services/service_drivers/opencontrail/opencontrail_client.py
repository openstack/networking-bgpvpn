# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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
from networking_bgpvpn.neutron.services.service_drivers.opencontrail import \
    exceptions as oc_exc
from oslo_config import cfg
from oslo_log import log
from oslo_utils import uuidutils
import requests
import six
from six.moves import http_client as httplib
from six.moves.urllib import parse as urlparse

LOG = log.getLogger(__name__)

CONF = cfg.CONF
opencontrail_opts = [
    cfg.IntOpt('request_timeout', default=30,
               help='Timeout seconds for HTTP requests. Set it to None to '
                    'disable timeout.'),
]
CONF.register_opts(opencontrail_opts, 'APISERVER')


def get_auth_token():
    DEFAULT_HEADERS = {
        'Content-type': 'application/json; charset="UTF-8"',
        'X-Contrail-Useragent': 'bgppn_opencontrail_client',
    }
    admin_user = cfg.CONF.keystone_authtoken.admin_user
    admin_password = cfg.CONF.keystone_authtoken.admin_password
    admin_tenant_name = cfg.CONF.keystone_authtoken.admin_tenant_name
    auth_body = {
        "auth": {
            "passwordCredentials": {
                "username": admin_user,
                "password": admin_password
            },
            "tenantName": admin_tenant_name
        }
    }
    try:
        auth_type = CONF.keystone_authtoken.auth_type
    except cfg.NoSuchOptError:
        auth_type = "keystone"
    if auth_type != "keystone":
        return
    try:
        auth_url = cfg.CONF.keystone_authtoken.auth_url
    except cfg.NoSuchOptError:
        try:
            auth_host = cfg.CONF.keystone_authtoken.auth_host
        except cfg.NoSuchOptError:
            auth_host = "127.0.0.1"
        try:
            auth_protocol = cfg.CONF.keystone_authtoken.auth_protocol
        except cfg.NoSuchOptError:
            auth_protocol = "http"
        try:
            auth_port = cfg.CONF.keystone_authtoken.auth_port
        except cfg.NoSuchOptError:
            auth_port = "35357"
        auth_url = "%s://%s:%s" % (auth_protocol, auth_host, auth_port)
    url = auth_url + '/v2.0/tokens'
    response = requests.post(url, data=json.dumps(auth_body),
                             headers=DEFAULT_HEADERS)

    if response.status_code == 200:
        auth_content = json.loads(response.text)
        return auth_content['access']['token']['id']
    else:
        raise RuntimeError("Authentication failure. Code: %d, reason: %s"
                           % (response.status_code, response.reason))


class RequestHandler(object):
    """Handles processing requests."""

    def __init__(self):
        self._host = CONF.APISERVER.api_server_ip
        self._port = CONF.APISERVER.api_server_port
        self._request_timeout = float(CONF.APISERVER.request_timeout)
        self._api_url = 'http://' + self._host + ':' + str(self._port)
        self._token = get_auth_token()

        self._pool = requests.Session()
        self._resource = ""
        self._id = ""

    def delete(self, url, body=None, headers=None, params=None):
        return self._do_request("DELETE", url, body=body,
                                headers=headers, params=params)

    def get(self, url, body=None, headers=None, params=None):
        return self._do_request("GET", url, body=body,
                                headers=headers, params=params)

    def post(self, url, body=None, headers=None, params=None):
        return self._do_request("POST", url, body=body,
                                headers=headers, params=params)

    def put(self, url, body=None, headers=None, params=None):
        return self._do_request("PUT", url, body=body,
                                headers=headers, params=params)

    def _do_request(self, method, url, body=None, headers=None,
                    params=None, retry_auth=True):
        req_params = self._get_req_params(data=body)
        if headers:
            req_params['headers'].update(headers)

        url = urlparse.urljoin(self._api_url, url)
        if params and isinstance(params, dict):
            url += '?' + urlparse.urlencode(params, doseq=1)

        if url[-1] == '/':
            url = url[:-1]

        self._log_req(method, url, params, req_params)

        try:
            response = self._pool.request(method, url, **req_params)
        except Exception as e:
            raise oc_exc.OpenContrailAPIFailed(url=url, excption=e)

        self._log_res(response)

        if response.status_code == httplib.UNAUTHORIZED and retry_auth:
            self._auth_token = get_auth_token()
            return self._do_request(method, url, body=body, headers=headers,
                                    params=params, retry_auth=False)
        if response.status_code == httplib.UNAUTHORIZED and not retry_auth:
            raise oc_exc.OpenContrailAPINotAuthorized

        if response.status_code == httplib.NOT_FOUND:
            raise oc_exc.OpenContrailAPINotFound(resource=self._resource,
                                                 id=self._id)

        if response.status_code == httplib.CONFLICT:
            raise oc_exc.OpenContrailAPIConflict(reason=response.reason)

        if response.status_code == httplib.BAD_REQUEST:
            raise oc_exc.OpenContrailAPIBadRequest(reason=response.reason)

        if response.status_code is not httplib.OK:
            raise oc_exc.OpenContrailAPIError(status=response.status_code,
                                              reason=response.reason)

        if response.content:
            return response.json()

    def _get_req_params(self, data=None):
        req_params = {
            'headers': {
                'Content-type': 'application/json; charset="UTF-8"',
                'Accept': "application/json",
                'X-Auth-Token': self._token,
            },
            'allow_redirects': False,
            'timeout': self._request_timeout,
        }

        if data:
            req_params.update({'data': json.dumps(data)})

        return req_params

    @staticmethod
    def _log_req(method, url, params, req_params):
        if not CONF.debug:
            return

        curl_command = ['REQ: curl -i -X %s ' % method]

        if params and isinstance(params, dict):
            url += '?' + urlparse.urlencode(params, doseq=1)

        curl_command.append('"%s" ' % url)

        for name, value in six.iteritems(req_params['headers']):
            curl_command.append('-H "%s: %s" ' % (name, value))

        if ('data' in req_params.keys()
            and (isinstance(req_params['data'], dict)
                 or isinstance(req_params['data'], str))):
            curl_command.append("-d '%s'" % (req_params['data']))

        LOG.debug(''.join(curl_command))

    @staticmethod
    def _log_res(resp):
        if CONF.debug:
            dump = ['RES: \n', 'HTTP %.1f %s %s\n' % (resp.raw.version,
                                                      resp.status_code,
                                                      resp.reason)]
            dump.extend('%s: %s\n' % (k, v)
                        for k, v in six.iteritems(resp.headers))
            dump.append('\n')
            if resp.content:
                dump.extend([resp.content, '\n'])

            LOG.debug(''.join(dump))


class OpenContrailAPIBaseClient(RequestHandler):
    """OpenContrail Base REST API Client."""

    resource_path = {
        'FQName to ID': '/fqname-to-id/',
        'ID to FQName': '/id-to-fqname/',
        'Ref Update': "/ref-update/",
        'Virtual Network': '/virtual-networks/',
        'Routing Instance': '/routing-instances/',
        'Route Target': '/route-targets/',
        'Key Value Store': '/useragent-kv/',
        'Project': '/projects/'
    }

    def list(self, resource, **params):
        """Fetches a list of resources."""

        res = self.resource_path.get(resource, None)
        if not res:
            raise oc_exc.OpenContrailAPINotSupported(action='list',
                                                     resource=resource)

        self._resource = resource
        return self.get(res, params=params)

    def show(self, resource, id, **params):
        """Fetches information of a certain resource."""

        res = self.resource_path.get(resource, None)
        if not res:
            raise oc_exc.OpenContrailAPINotSupported(action='show',
                                                     resource=resource)

        if res[-2:] == 's/':
            res = res[:-2] + '/'

        self._resource = resource
        self._id = id
        return self.get(res + id, params=params).popitem()[1]

    def create(self, resource, body):
        """Creates a new resource."""

        res = self.resource_path.get(resource, None)
        if not res:
            raise oc_exc.OpenContrailAPINotSupported(action='create',
                                                     resource=resource)

        self._resource = resource
        resp = self.post(res, body=body)
        if resp:
            return resp.popitem()[1]

    def update(self, resource, id, body=None):
        """Updates a resource."""

        res = self.resource_path.get(resource, None)
        if not res:
            raise oc_exc.OpenContrailAPINotSupported(action='update',
                                                     resource=resource)

        if res[-2:] == 's/':
            res = res[:-2] + '/'

        self._resource = resource
        self._id = id
        return self.put(res + id, body=body)

    def remove(self, resource, id):
        """Removes the specified resource."""

        res = self.resource_path.get(resource, None)
        if not res:
            raise oc_exc.OpenContrailAPINotSupported(action='delete',
                                                     resource=resource)

        if res[-2:] == 's/':
            res = res[:-2] + '/'

        self._resource = resource
        self._id = id
        return self.delete(res + id)

    def fqname_to_id(self, resource, fq_name):
        """Get UUID resource from an OpenContrail fq_name"""

        if not isinstance(fq_name, list):
            raise oc_exc.OpenContrailAPIBadFqName

        body = {'fq_name': fq_name, 'type': resource}

        return self.create('FQName to ID', body)

    def id_to_fqname(self, id):
        """Get fq_name resource from an OpenContrail UUID"""

        if not uuidutils.is_uuid_like(id):
            raise oc_exc.OpenContrailAPIBadUUID

        body = {'uuid': id}

        return self.create('ID to FQName', body)

    def ref_update(self, operation, resource_uuid, resource_type, ref_type,
                   ref_fq_name, ref_uuid, attributes=None):
        """Updates a resource refference"""

        body = {
            "operation": operation,
            "type": resource_type,
            "uuid": resource_uuid,
            "ref-type": ref_type,
            "ref-fq-name": ref_fq_name,
            "ref-uuid": ref_uuid,
        }
        if attributes and isinstance(attributes, dict):
            body.update({'attr': attributes})

        return self.create('Ref Update', body)

    def kv_store(self, operation, key=None, value=None):
        """Use key/value store exposed by the OpenContrail API"""

        body = {
            'operation': operation,
            'key': None,
        }

        if operation == 'RETRIEVE' and not key:
            pass
        elif operation in ['RETRIEVE', 'DELETE'] and key:
            body.update({'key': key})
        elif operation == 'STORE' and key and value:
            body.update({'key': key, 'value': json.dumps(value)})
        else:
            raise oc_exc.OpenContrailAPIBadKVAttributes

        return self.create('Key Value Store', body)
