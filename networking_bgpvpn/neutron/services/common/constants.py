# Copyright 2015 OpenStack Foundation
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

BGPVPN = "BGPVPN"

BGPVPN_RES = "bgpvpns"
BGPVPN_L3 = 'l3'
BGPVPN_L2 = 'l2'
BGPVPN_TYPES = [BGPVPN_L3, BGPVPN_L2]

# Regular expression to validate 32 bits unsigned int
UINT32_REGEX = (r'(0|[1-9]\d{0,8}|[1-3]\d{9}|4[01]\d{8}|42[0-8]\d{7}'
                r'|429[0-3]\d{6}|4294[0-8]\d{5}|42949[0-5]\d{4}'
                r'|429496[0-6]\d{3}|4294967[0-1]\d{2}|42949672[0-8]\d'
                r'|429496729[0-5])')
# Regular expression  to validate 16 bits unsigned int
UINT16_REGEX = (r'(0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}'
                r'|655[0-2]\d|6553[0-5])')
# Regular expression to validate 8 bits unsigned int
UINT8_REGEX = (r'(0|[1-9]\d{0,1}|1\d{2}|2[0-4]\d|25[0-5])')
# Regular expression to validate IPv4 address
IP4_REGEX = (r'(%s\.%s\.%s\.%s)') % (UINT8_REGEX, UINT8_REGEX, UINT8_REGEX,
                                     UINT8_REGEX)
# Regular expression to validate Route Target list format
# Support of the Type 0, Type 1 and Type 2, cf. chapter 4.2 in RFC 4364
RT_REGEX = (r'^(%s:%s|%s:%s|%s:%s)$') % (UINT16_REGEX, UINT32_REGEX,
                                         IP4_REGEX, UINT16_REGEX,
                                         UINT32_REGEX, UINT16_REGEX)
