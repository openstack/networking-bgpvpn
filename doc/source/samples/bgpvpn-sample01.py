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

from neutronclient.v2_0 import client
import os
import sys

# Parameter for subnet neutron object
SUBNET_IP = "192.168.24.0/24"

# Parameters for bgpvpn neutron object
BGPVPN_RT = "64512:2"


# Function to obtain stack parameters from system vars
def get_keystone_creds():
    d = {}
    try:
        d['username'] = os.environ['OS_USERNAME']
        d['password'] = os.environ['OS_PASSWORD']
        d['auth_url'] = os.environ['OS_AUTH_URL']
        d['tenant_name'] = os.environ['OS_TENANT_NAME']
    except KeyError:
        print ("ERROR: Stack environment variables type "
               "OS_* are not properly set")
        sys.exit(1)
    return d


# Main function
def main():
    # Call function that imports (dev)stack vars
    creds = get_keystone_creds()

    # Neutron object
    # It dynamically loads the BGPVPN API
    neutron = client.Client(**creds)

    try:
        # Network object creation. This dummy network will be used to bind the
        # attached subnet to the BGPVPN object.

        # Creation of the Network
        net_obj = neutron.create_network({'network': {'name': "dummyNet"}})
        # Verify creation
        print ('Network created\t[network-id:%s]...' %
               net_obj['network']['id'])

        # Creation of the subnet, is attached to the created network
        subnet_obj = neutron.create_subnet(
            {'subnet':
                {'name': "dummySubnet",
                 'cidr': SUBNET_IP,
                 'network_id': net_obj['network']['id'],
                 'ip_version': 4}})
        # Verify
        print ("Subnet created\t[subnet-id:%s]..." %
               subnet_obj['subnet']['id'])

        # Creation of a BGPVPN object. This object is created with the
        # required parameter 'routes_targets'.
        # This object can be created with others parameters or be updated with
        # them by calling the update function on the object.

        print ("\nBGPVPN object handling.")
        # Creation of the BGPVPN object
        bgpvpn_obj = neutron.create_bgpvpn(
            {'bgpvpn': {'route_targets': [BGPVPN_RT]}})
        print ("BGPVPN object created\t[bgpvpn-id:%s]..." %
               bgpvpn_obj['bgpvpn']['id'])
        # Update the BGPVPN object
        bgpvpn_obj = neutron.update_bgpvpn(
            bgpvpn_obj['bgpvpn']['id'], {'bgpvpn': {'name': "dummyBGPVPN"}})
        # List all BGPVPN objects
        list_bgpvpn_obj = neutron.list_bgpvpns()
        print ("List of all BGPVPN object\t[%s]" % list_bgpvpn_obj)
        # List of all BGPVPN objects filtered on the type parameter set to l3
        # value
        list_bgpvpn_obj = neutron.list_bgpvpns(type='l3')
        print ("List of all BGPVPN object with type=l3\t[%s]" %
               list_bgpvpn_obj)

        # Creation of a BGPVPN Network association.
        print ("\nBGPVPN Network Association object handling.")
        # Creation of a Network Association bound on the created BGPVPN object
        bgpvpn_net_assoc_obj = neutron.create_network_association(
            bgpvpn_obj['bgpvpn']['id'],
            {'network_association':
                {'network_id':
                    net_obj['network']['id']}})
        print ("BGPVPN Network Association created\t"
               "[network_association:%s]..." %
               bgpvpn_net_assoc_obj['network_association']['id'])
        # List all NETWORK ASSOCIATION object filtered on the network created
        # above
        list_bgpvpn_net_assoc_obj = neutron.list_network_associations(
            bgpvpn_obj['bgpvpn']['id'],
            network_id=net_obj['network']['id'])
        print ("List of NETWORK ASSOCIATION objects using network_id"
               "[%s]\t[%s]" %
               (net_obj['network']['id'], list_bgpvpn_net_assoc_obj))

        # Deletion of all objects created in this example

        print ("\nDeletion of all created objects")
        # First declared associations related of the created BGPVPN object in
        # this example
        neutron.delete_network_association(
            bgpvpn_net_assoc_obj['network_association']['id'],
            bgpvpn_obj['bgpvpn']['id'])
        # Then the BGPVPN object
        neutron.delete_bgpvpn(bgpvpn_obj['bgpvpn']['id'])
        # Subnet
        neutron.delete_subnet(subnet_obj['subnet']['id'])
        # And finally the Network
        neutron.delete_network(net_obj['network']['id'])
    except Exception as e:
        print ("[ERROR][%s]" % str(e))
        sys.exit(1)

    print ("[Done]")

if __name__ == '__main__':
        main()

__all__ = ['main']
