=================
Future attributes
=================

Specifications for the following attributes have been defined but not implemented yet:

.. csv-table:: Future attributes
    :header: Attribute Name,Type,Access,Default Value,Validation/Constraint,Description

    technique, string, RW admin only, None, for instance "ipvpn" or "evpn", (optional) selection of the technique used to implement the VPN
    auto_aggregate,bool,RW admin only,False,{ True | False },enable prefix aggregation or not (type l3 only) but no support in any driver
    admin_state_up,bool,RW admin only,True,{ True | False },interconnection with this BGPVPN is enabled by the admin

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

* GET /bgpvpn/techniques:

  .. code-block:: json

     { "techniques": {
        "l3": [ "ipvpn" ],
        "l2": [ "evpn" ]
     } }

* GET /bgpvpn/techniques/l3:

  .. code-block:: json

     { "l3": [ "ipvpn"] }

* GET /bgpvpn/techniques/l2:

  .. code-block:: json

     { "l2": [ "evpn"] }

'admin_state_up' attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is an admin-only attribute allowing the admin to shutdown connectivity to
and from a BGP VPN and expose this state to the tenant.
