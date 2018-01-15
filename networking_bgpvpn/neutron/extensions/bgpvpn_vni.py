#
# Copyright 2017 Ericsson India Global Services Pvt Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

from neutron_lib.api.definitions import bgpvpn_vni
from neutron_lib.api import extensions


class Bgpvpn_vni(extensions.APIExtensionDescriptor):
    """Extension class supporting vni.

    This class is used by neutron's extension framework to make
    metadata about the vni attribute in bgpvpn available to
    external applications.

    With admin rights one will be able to create and read the values.
    """

    api_definition = bgpvpn_vni
