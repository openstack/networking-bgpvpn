..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===
API
===

BGPVPN Resource
---------------

A new BGPVPN resource is introduced. It contains a set of parameters
for a BGP-based VPN.

A BGPVPN is created by the admin and given to a tenant who can then
associate it to Networks or Routers.

Description of a BGPVPN resource:

.. csv-table:: BGPVPN
    :header: Attribute Name,Type,Access,Default Value,Validation/Constraint,Description

    id,uuid-str,R,Generated,UUID_PATTERN,id of BGPVPN resource
    name,string,RW,\"\",String,name of this BGPVPN
    tenant_id,uuid-str,R,None,UUID_PATTERN,tenant_id of owner
    type, string, R, l3, for instance "l3 or l2", selection of the type of VPN and the technology behind it
    route_targets,list(str),RW admin only,None,List of valid route-target strings (see below),Route Targets that will be both imported and used for export
    import_targets,list(str),RW admin only,None,List of valid route-target strings (see below),additional Route Targets that will be imported
    export_targets,list(str),RW admin only,None,List of valid route-target strings (see below),additional Route Targets that will be used for export
    route_distinguishers,list(str),RW admin only,None,List of valid route-distinguisher strings (see below),(if this parameter is specified) one of these RDs will be used to advertize VPN routes
    networks,list(uuid-str),RO,None,List of Network UUIDs,This read-only attribute reflects the associations defined by Network association API resources
    routers,list(uuid-str),RO,None,List of Router UUIDs,This read-only attribute reflects the associations defined by Router association API resources

Specifications for additional attributes have been defined, but not implemented yet, see :doc:`future/attributes`.

'route_targets', 'import_rts', 'export_rts' attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Route Targets:

* The set of RTs used for import is the union of route_targets and
  import_targets.
* The set of RTs used for export is the union of route_targets and
  export_targets.

At least one of route_targets, import_targets or export_targets options will
typically be defined, but the API will not enforce that and all lists can be
empty.

For instance, in the very typical use case where the BGPVPN uses a
single Route Target for both import and export, the route_targets parameter
alone is enough and will contain one Route target.

route_distinguishers
~~~~~~~~~~~~~~~~~~~~

The route_distinguishers parameter is optional and provides an indication of
the RDs that shall be used for routes announced for Neutron networks.
The contract is that when a list of RDs is specified, the backend will
use, for a said advertisement of a route, one of these RDs. The motivation for
having a list rather than only one RD is to allow the support for multihoming
a VPN prefix (typically for resiliency, load balancing or anycast).
A backend may or may not support this behavior, and should report an
API error in the latter case.
When not specified, the backend will use automatically-assigned RDs
(for instance <ip>:<number> RDs derived from the PE IP).

Valid strings for Route Distinguishers and Route Targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Valid strings for a Route Target or a Route Distinguisher are the following:

* <2-byte AS#>:<32bit-number>
* <4-byte AS#>:<16bit-number>
* <4-byte IPv4>:<16bit-number>

Example API call to manipulate a BGPVPN resource
------------------------------------------------

  * POST /bgpvpn/bgpvpns ::

     {"bgpvpn": {
        "name": "foo",
        "route_targets": ["64512:1444"],
        "type": "l3",
        "tenant_id": "f94ea398564d49dfb0d542f086c68ce7",
     }}

  * Result ::

     {"bgpvpn": {
        "id": "460ac411-3dfb-45bb-8116-ed1a7233d143",
        "name": "foo",
        "route_targets": ["64512:1444"],
        "export_targets": [],
        "import_targets": [],
        "type": "l3",
        "tenant_id": "f94ea398564d49dfb0d542f086c68ce7",
        "auto_aggregate": false,
        "admin_state_up": true,
     }}

Network association
-------------------

Associating a BGPVPN to a Network can be done for both BGPVPN of type l2 and
of type l3. For type L3, the semantic is that all Subnets bound to the Network
will be interconnected with the BGP VPN (and thus between themselves).

A said Network can be associated with multiple BGPVPNs.

Associating or disassociating a BGPVPN to a Network is done by manipulating
a Network association API resource as a sub-resource of the BGPVPN resource:

* Associate:

  * POST /bgpvpn/bgpvpns/{bgpvpn_uuid}/network_associations ::

     { "network_association": 
        {
           "network_id": NETWORK_UUID
        }
     }

  * Result::

     { "network_association": 
        {
	   "id": NET_ASSOCIATION_UUID,
           "network_id": NETWORK_UUID,
        }
     }

* Dis-associate::

     DELETE /bgpvpn/bgpvpns/{bgpvpn_uuid}/network_associations/NET_ASSOCIATION_UUID

Listing existing Network associations of a BGPVPN is done via a GET
on "/bgpvpn/bgpvpns/{bgpvpn_uuid}/network_associations".

Router association
------------------

Associating a BGPVPN to a Router can be done only for BGPVPN of type l3.
The semantic is that all Subnets bound to the Router will be interconnected
with the BGPVPN.

A said Router can be associated with multiple BGPVPNs.

Associating or disassociating a BGPVPN to a Router is done by manipulating
a Router association API resource as a sub-resource of the BGPVPN resource:

* Associate:

  * POST /bgpvpn/bgpvpns/{bgpvpn_uuid}/router_associations ::

     { "router_association": 
        {
           "router_id": ROUTER_UUID
        }
     }

  * Result::

     { "router_association": 
        {
	   "id": NET_ASSOCIATION_UUID,
           "router_id": ROUTER_UUID,
           "bgpvpn_id": BGPVPN_UUID,
        }
     }

* Dis-associate::

     DELETE /bgpvpn/bgpvpns/{bgpvpn_uuid}/router_associations/NET_ASSOCIATION_UUID

Listing existing Router associations of a BGPVPN is done via a GET
on "/bgpvpn/bgpvpns/{bgpvpn_uuid}/router_associations".

Association constraints
-----------------------

A said BGPVPN can be associated to multiple Networks and/or multiple Routers.

To avoid any ambiguity on semantics in particular the context of processing
associated to a Router (e.g. NAT or FWaaS), if a said Subnet in a Network is
bound to a Router, this API does not allow to both associate the Network to an
L3 BGPVPN and the Router to the same or to a distinct L3 BGPVPN.

Moreover, for BGP VPNs of type L3, there are possible cases of IP prefix
overlaps that can't be detected by the service plugin before BGP routes are
received, for which the behavior is left undefined by these specifications
(i.e. which of the overlapping routes is being used) and will depend on the
backend. This applies for both Router associations and Network associations
in the case where traffic is forwarded by a Router and the destination IP
belongs both to a prefix of a BGP VPN associated with the Router or with the
Network originating the traffic, and to a prefix of a Subnet bound to the
Router; in such a case whether the traffic will be delivered to the Subnet
or to the BGP VPN is not defined by this API.

Listing the Networks and Routers associated to a BGPVPN
-------------------------------------------------------

On a GET request on a BGPVPN, the dictionary returned will have a 'networks'
attribute with a list of the UUID of Networks associated with the BGPVPN and
a 'routers' attribute with a list of the UUID of Routers associated with the
BGPVPN.

Example with 2 Network associations:

  * GET /bgpvpn/bgpvpns/eb371abd-d7de-4664-8991-3a3be1279cf4

  * Result::

     {"bgpvpn": {
        "export_targets": [],
        "name": "",
        "route_targets": ["64512:1444"],
        "tenant_id": "f94ea398564d49dfb0d542f086c68ce7",
        "auto_aggregate": False,
        "type": "l3",
        "id": "460ac411-3dfb-45bb-8116-ed1a7233d143"
        "networks": [ "d457fefe-7ae5-4aea-927e-0d16a3767be5",
                      "445744ca-678e-4265-962f-367607c79245" ]
     }}

Connectivity Impact inside Openstack Neutron
--------------------------------------------

Creating two BGPVPNs with RTs resulting in both VPNs to exchange routes, and
then associating these two BGPVPNs to two Networks, will result in
establishing interconnectivity between these two Networks, this simply being
the result of applying BGP VPN Route Target semantics (i.e. without making
prefixes to Neutron Networks a particular case).

This similarly applies to Router associations.


