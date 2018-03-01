..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
BGP VPN Interconnection Service Overview
==========================================

.. include:: ../introduction.rst

Alternatives and related techniques
-----------------------------------

Other techniques are available to build VPNs, but the goal of this proposal
is to make it possible to create the interconnect we need when the technology
of BGP-based VPNs is already used outside an OpenStack cloud.

Reminder on BGP VPNs and Route Targets
--------------------------------------

BGP-based VPNs allow a network operator to offer a VPN service to a VPN
customer, delivering isolating connectivity between multiple sites of this
customer.

Unlike IPSec or SSL-based VPNs, for instance, these VPNs are not
typically built over the Internet, are most often not encrypted, and their
creation is not at the hand of the end-user.

Here is a reminder on how the connectivity is defined between sites of a VPN (VRFs).

In BGP-based VPNs, a set of identifiers called Route Targets are associated
with a VPN, and in the typical case identify a VPN ; they can also be used
to build other VPN topologies such as hub'n'spoke.

Each VRF (Virtual Routing and Forwarding) in a PE  (Provider Edge router)
imports/exports routes from/to Route Targets. If a VRF imports from a Route
Target, BGP IP VPN routes will be imported in this VRF. If a VRF exports to
a Route Target, the routes in the VRF will be associated to this Route Target
and announced by BGP.

Mapping between PEs/CEs and Neutron constructs
----------------------------------------------

As outlined in the overview, how PEs, CEs (Customer Edge router), VRFs
map to Neutron constructs will depend on the backend driver used for this
service plugin.

For instance, with the current bagpipe driver, the PE and VRF functions
are implemented on compute nodes and the VMs are acting as CEs. This PE
function will BGP-peer with edge IP/MPLS routers, BGP Route Reflectors
or other PEs.

Bagpipe BGP which implements this function could also be instantiated
in network nodes, at the l3agent level, with a BGP speaker on each
l3agent; router namespaces could then be considered as CEs.

Other backends might want to consider the router as a CE and drive an
external PE to peer with the service provider PE, based on information
received with this API. It's up to the backend to manage the connection
between the CE and the cloud provider PE.

Another typical option is where the driver delegates the work to an SDN
controller which drives a BGP implementation advertising/consuming the
relevant BGP routes and remotely drives the vswitches to setup the
datapath accordingly.

API and Workflows
-----------------

BGP VPN are deployed, and managed by the operator, in particular to
manage Route Target identifiers that control the isolation between the different
VPNs. Because of this BGP VPN parameters cannot be chosen by tenants, but
only by the admin. In addition, network operators may prefer to not expose
actual Route Target values to the users.

The operation that is let at the hand of a tenant is the association of a BGPVPN
resource that it owns with his Neutron Networks or Routers.

So there are two workflows, one for the admin, one for a tenant.

* Admin/Operator Workflow: Creation of a BGPVPN

  * the cloud/network admin creates a BGPVPN for a tenant based on
    contract and OSS information about the VPN for this tenant

  * at this stage, the list of associated Networks and Routers can be empty

* Tenant Workflow: Association of a BGPVPN to Networks and/or Routers, on-demand

  * the tenant lists the BGPVPNs that it can use

  * the tenant associates a BGPVPN with one or more Networks or Routers.

Sequence diagram summarizing these two workflows:

.. seqdiag:: workflows.seqdiag


Component architecture overview
-------------------------------

This diagram gives an overview of the architecture:

.. blockdiag:: components-sdn.blockdiag

This second diagram depicts how the *bagpipe* reference driver implements its
backend:

.. blockdiag:: drivers/bagpipe/overview.blockdiag

References
----------

.. [RFC4364] BGP/MPLS IP Virtual Private Networks (IP VPNs) http://tools.ietf.org/html/rfc4364
.. [RFC7432] BGP MPLS-Based Ethernet VPN (Ethernet VPNs, a.k.a E-VPN) http://tools.ietf.org/html/rfc7432

