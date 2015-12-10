# Copyright 2012 OpenStack Foundation.
# Copyright 2015 Hewlett-Packard Development Company, L.P.
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

import inspect

from neutronclient.common import extension as client_extension
from neutronclient.v2_0 import client

# python-neutronclient Kilo does not have support for sub-resources
# we will thus do monkey patching as a workaround

# the methods below are copy-pasted from
# python-neutronclient/neutronclient/v2_0/client.py


def extend_show(self, resource_plural, path, parent_resource):
    def _fx(obj, **_params):
        return self.show_ext(path, obj, **_params)

    def _parent_fx(obj, parent_id, **_params):
        return self.show_ext(path % parent_id, obj, **_params)
    fn = _fx if not parent_resource else _parent_fx
    setattr(self, "show_%s" % resource_plural, fn)


def extend_list(self, resource_plural, path, parent_resource):
    def _fx(**_params):
        return self.list_ext(path, **_params)

    def _parent_fx(parent_id, **_params):
        return self.list_ext(path % parent_id, **_params)
    fn = _fx if not parent_resource else _parent_fx
    setattr(self, "list_%s" % resource_plural, fn)


def extend_create(self, resource_singular, path, parent_resource):
    def _fx(body=None):
        return self.create_ext(path, body)

    def _parent_fx(parent_id, body=None):
        return self.create_ext(path % parent_id, body)
    fn = _fx if not parent_resource else _parent_fx
    setattr(self, "create_%s" % resource_singular, fn)


def extend_delete(self, resource_singular, path, parent_resource):
    def _fx(obj):
        return self.delete_ext(path, obj)

    def _parent_fx(obj, parent_id):
        return self.delete_ext(path % parent_id, obj)
    fn = _fx if not parent_resource else _parent_fx
    setattr(self, "delete_%s" % resource_singular, fn)


def extend_update(self, resource_singular, path, parent_resource):
    def _fx(obj, body=None):
        return self.update_ext(path, obj, body)

    def _parent_fx(obj, parent_id, body=None):
        return self.update_ext(path % parent_id, obj, body)
    fn = _fx if not parent_resource else _parent_fx
    setattr(self, "update_%s" % resource_singular, fn)


def _extend_client_with_module(self, module, version):
    classes = inspect.getmembers(module, inspect.isclass)
    for _, cls in classes:
        if hasattr(cls, 'versions'):
            if version not in cls.versions:
                continue
        parent_resource = getattr(cls, 'parent_resource', None)
        if issubclass(cls, client_extension.ClientExtensionList):
            self.extend_list(cls.resource_plural, cls.object_path,
                             parent_resource)
        elif issubclass(cls, client_extension.ClientExtensionCreate):
            self.extend_create(cls.resource, cls.object_path,
                               parent_resource)
        elif issubclass(cls, client_extension.ClientExtensionUpdate):
            self.extend_update(cls.resource, cls.resource_path,
                               parent_resource)
        elif issubclass(cls, client_extension.ClientExtensionDelete):
            self.extend_delete(cls.resource, cls.resource_path,
                               parent_resource)
        elif issubclass(cls, client_extension.ClientExtensionShow):
            self.extend_show(cls.resource, cls.resource_path,
                             parent_resource)
        elif issubclass(cls, client_extension.NeutronClientExtension):
            setattr(self, "%s_path" % cls.resource_plural,
                    cls.object_path)
            setattr(self, "%s_path" % cls.resource, cls.resource_path)
            self.EXTED_PLURALS.update({cls.resource_plural: cls.resource})


setattr(client.Client,
        "extend_list",
        extend_list)


setattr(client.Client,
        "extend_create",
        extend_create)


setattr(client.Client,
        "extend_show",
        extend_show)


setattr(client.Client,
        "extend_update",
        extend_update)


setattr(client.Client,
        "extend_delete",
        extend_delete)


setattr(client.Client,
        "_extend_client_with_module",
        _extend_client_with_module)
