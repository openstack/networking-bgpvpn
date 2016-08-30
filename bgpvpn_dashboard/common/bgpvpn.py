# Copyright (c) 2016 Orange.
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
import re

from django.utils.translation import ugettext_lazy as _


ROUTE_TARGET_HELP = _("A single BGP Route Target or a "
                      "comma-separated list of BGP Route Target. Example: "
                      "64512:1 or 64512:1,64512:2,64512:3")

RT_FORMAT_ATTRIBUTES = ('route_targets', 'import_targets', 'export_targets')


def format_rt(route_targets):
    if route_targets:
        return re.compile(" *, *").split(route_targets)
    else:
        return route_targets
