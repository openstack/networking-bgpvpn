..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

===
API
===

This API is documented in the `Neutron API Reference <https://docs.openstack.org/api-ref/network/v2/#bgp-mpls-vpn-interconnection>`_.

ADMIN
=====

Configuration
=============

On VXLAN VNI
------------

.. note:: This feature is under development in the Queens release

VXLAN is one option among others that could be used for BGP E-VPNs.
When VXLAN is used on a hardware platform the use of a locally-assigned id
may not be always possible which introduces the need to configure a
globally-assigned VXLAN VNI.

The optional ``vni`` attribute is an admin-only parameter and allows the
admin to enforce the use of a chosen globally-assigned VXLAN VNI for the
said BGPVPN.

The default when no VNI is specified and the VXLAN encapsulation is used, is
to let the backend choose the VNI in advertised routes, and use the VNI in
received routes for transmitted traffic. The backend will conform to
E-VPN overlay specs.

If the ``vni`` attribute is set for a BGPVPN, the following is enforced:

* the routes announced by the backend will advertise the specified VNI (this
  relates to traffic sent from this BGP VPN to a Network or Router)

* for the routes received by the backend for this BGPVPN, and that carry a
  different VNI that the VNI specified for the BGPVPN the behavior may
  depend on the backend, with the recommended behavior being to
  liberally accept such routes.

If a backend does not support the approach recommended above of liberally
accepting routes with a different VNI, the check can be implemented as follows:

* when a route is imported, for each BGPVPN associated to the Network or
  Router and having a VNI defined:

  * the set of Route Targets of the route is intersected with the import_rts of
    the BGPVPN

  * if this intersection is non-empty the ``vni`` of the BGPVPN is retained

* the route is used to establish connectivity to the destination in the
  forwarding plane only if the advertised VNI is equal to all retained
  VNIs in the previous step

The above check is applied similarly for a Router associated to multiple BGP
VPN.

The backend is expected to provide troubleshooting information for the cases
when a route ends up not being used because the VNI check failed.

Valid range for the ``vni`` attribute is [1, 2\ :sup:`24`\ -1].
