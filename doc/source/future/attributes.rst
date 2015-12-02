=================
Future attributes
=================

Specifications for the following attributes have been defined but not implemented yet:

.. csv-table:: Future attributes
    :header: Attribute Name,Type,Access,Default Value,Validation/Constraint,Description

    technique, string, RW admin only, None, for instance "ipvpn" or "evpn", (optional) selection of the technique used to implement the VPN
    auto_aggregate,bool,RW admin only,False,{ True | False },enable prefix aggregation or not (type l3 only) but no support in any driver
    admin_state_up,bool,RW admin only,True,{ True | False },interconnection with this BGPVPN is enabled by the admin
    vnid,integer,RW admin only,None,24bit integer,Globally-assigned VXLAN id

'auto_aggregate' attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~

The 'auto_aggregate' flag controls whether or not routes should be automatically
aggregated before being advertised outside Neutron.
A backend may or may not support this behavior, and its driver should report
an API error in the latter case.

'technique' attribute
~~~~~~~~~~~~~~~~~~~~~

The 'technique' attribute is optional and can be used by the admin to select one
of multiple techniques when more than one is supported by the driver. When no
technique is specified, the driver will use a default value. An API call will
be available to let the API user know about the types supported by the driver
for a said vpn type.

Currently defined techniques are:

* for l3:

  * 'ipvpn': this corresponds to RFC4364
  * 'evpn-prefix': this corresponds to
    draft-ietf-bess-evpn-prefix-advertisement

* for l2:

  * 'evpn': this corresponds to RFC7432

API call to list the available techniques, with example answers:

  * GET /bgpvpn/techniques ::

     { "techniques": {
        "l3": [ "ipvpn" ],
        "l2": [ "evpn" ]
     } }

  * GET /bgpvpn/techniques/l3 ::

     { "l3": [ "ipvpn"] }

  * GET /bgpvpn/techniques/l2 ::

     { "l2": [ "evpn"] }

'admin_state_up' attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is an admin-only attribute allowing the admin to shutdown connectivity to
and from a BGP VPN and expose this state to the tenant.

'VNID' attribute
~~~~~~~~~~~~~~~~

VXLAN is one option among others that could be used for BGP E-VPNs for instance
in the context of E-VPN [draft-ietf-bess-evpn-overlay]_. When VXLAN is used on a
hardware platforms the use of a locally-assigned id may not be always possible
which introduce the need to configure a globally-assigned VXLAN VNID.

The 'VNID' optional VNID attribute allows the admin to enforce the use of a
chosen globally-assigned VXLAN VNID for the said BGPVPN.

The default when no VNID is specified and the VXLAN encapsulation is used, is
to let the backend choose the VNID in advertised routes, and use the VNID in
received routes for transmitted traffic

If the 'VNID' attribute is set for a BGPVPN, the following is enforced:

* the routes announced by the backend will advertise the specified VNID (this
  relates to traffic sent from this BGP VPN to a Network or Router)

* the routes received by the backend and that would be used to send traffic to
  the BGP VPN will not be used if they carry a different VNID than the VNID
  specified for the BGPVPN (this relates to traffic sent from a Network or
  Router to the BGP VPN)

In the case of a Network or Router associated to multiple BGPVPNs, the check
in the second bullet in the previous paragraph is done as follows:

* when a route is imported, for each BGPVPN associated to the Network or
  Router and having a VNID defined:

  * the set of Route Targets of the route is intersected with the import_rts of
    the BGPVPN

  * if this intersection is non-empty the 'VNID' of the BGPVPN is retained

* the route is used to establish connectivity to the destination in the
  forwarding plane only if the VNID is advertised is equal to all retained
  VNIDs in the previous step

The above check is applied similarly for a Router associated to multiple BGP
VPN.

The backend is expected provide troubleshooting information for the cases when
a route ends up not being used because the VNID checked failed.
