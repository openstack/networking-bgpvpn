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

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BGPVPNDriver(object):

    def __init__(self, service_plugin):
        self.service_plugin = service_plugin

    @property
    def service_type(self):
        pass

    @abc.abstractmethod
    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def update_bgpvpn_connection(self, context, old_bgpvpn_connection,
                                 bgpvpn_connection):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def notify_port_updated(self, context, port):
        pass

    @abc.abstractmethod
    def remove_port_from_bgpvpn_agent(self, context, port):
        pass
