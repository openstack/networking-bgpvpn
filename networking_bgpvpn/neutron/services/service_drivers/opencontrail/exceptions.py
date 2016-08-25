# Copyright (C) 2015 Cloudwatt
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

from neutron_lib import exceptions as n_exc

# OpenContrail client API exceptions


class OpenContrailAPIFailed(n_exc.NeutronException):
    message = _("Could not reach OpenContrail API server : %(url)s "
                "Exception: %(excption)s.")


class OpenContrailAPIError(n_exc.NeutronException):
    message = _('OpenContrail API returned %(status)s %(reason)s')


class OpenContrailAPINotSupported(n_exc.BadRequest):
    message = _('OpenContrail API client cannot %(action)s on %(resource)s')


class OpenContrailAPIBadFqName(n_exc.BadRequest):
    message = _("Bad fq_name for forming a fq_name to ID request")


class OpenContrailAPIBadUUID(n_exc.BadRequest):
    message = _("Bad UUID for forming a UUID to fq_name request")


class OpenContrailAPIBadKVAttributes(n_exc.BadRequest):
    message = _("Bad attributes for forming a key/value store request")


class OpenContrailAPINotAuthorized(n_exc.NotAuthorized):
    pass


class OpenContrailAPINotFound(n_exc.NotFound):
    message = _("%(resource)s %(id)s does not exist")


class OpenContrailAPIConflict(n_exc.Conflict):
    message = _("OpenContrail API conflict: %(reason)s")


class OpenContrailAPIBadRequest(n_exc.BadRequest):
    message = _("OpenContrail API bad request: %(reason)s")


class OpenContrailMalformedUUID(n_exc.BadRequest):
    message = _("Malformed UUID: %(uuid)s")
