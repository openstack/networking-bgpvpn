=======
Drivers
=======

The BGPVPN service plugin supports the following drivers:

.. toctree::
   :maxdepth: 1

   bagpipe/index
   opencontrail/index
   opendaylight/index
   nuage/index

The API is consistent across drivers, but not all drivers support all parts of
the API. Refer to the Driver Compatibility Matrix to determine what is
supported with each driver.

Driver Compatibility Matrix
---------------------------

+-------------------------------------------+---------------------------------------------------+
|               API                         |                       Driver                      |
+---------------------+---------------------+-----------+---------------+--------------+--------+
|      Object         |     Attribute       | Neutron   | OpenContrail  | OpenDaylight | Nuage  |
|                     |                     | w. bagpipe|               |              |        |
|                     |                     +-------+---+-------+-------+-------+------+        |
|                     |                     | ovs   |lnx|v1 [#]_|   v2  |   v1  |  v2  |        |
+=====================+=====================+=======+===+=======+=======+=======+======+========+
|      bgpvpn         |    base object      |   Yes     |  Yes  |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+-----------+-------+-------+-------+------+--------+
|                     | route_distinguisher |   No      |  No   |  No   |  Yes  | Yes  |   Yes  |
|                     +---------------------+-----------+-------+-------+-------+------+--------+
|                     |    route_targets    |   Yes     |  Yes  |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+-----------+-------+-------+-------+------+--------+
|                     |    import_targets   |   Yes     |  Yes  |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+-----------+-------+-------+-------+------+--------+
|                     |    export_targets   |   Yes     |  Yes  |  Yes  |  Yes  | Yes  |   Yes  |
|                     +-------+-------------+-------+---+-------+-------+-------+------+--------+
|                     |       |     L3      | Yes   |Yes|  Yes  |  Yes  |  Yes  | Yes  |   Yes  |
|                     | type  +-------------+-------+---+-------+-------+-------+------+--------+
|                     |       |     L2      |No [#]_|Yes|  No   |  Yes  |  No   |  ?   |   ?    |
+---------------------+-------+-------------+-------+---+-------+-------+-------+------+--------+
| network_association |    base object      |   Yes     |  Yes  |  Yes  |  Yes  | Yes  |   No   |
+---------------------+---------------------+-----------+-------+-------+-------+------+--------+
| router_association  |    base object      |   Yes     |  No   |  Yes  |  Yes  | Yes  |   Yes  |
+---------------------+---------------------+-----------+-------+-------+-------+------+--------+

.. [#] OpenContrail driver v1 has been deprecated in favor of the production
   ready `driver v2`_. Warning, **no** migration path is planned.
.. [#] Support for BGPVPNs of type L2 with Neutron/bagpipe is supported
   with linuxbridge agents. The support for OVS agents is being worked on
   in the Queens cycle.
.. _driver v2: https://github.com/Juniper/contrail-neutron-plugin/tree/master/neutron_plugin_contrail/plugins/opencontrail/networking_bgpvpn
