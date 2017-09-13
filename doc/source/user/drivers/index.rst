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

+-------------------------------------------+------------------------------------------------+
|               API                         |                    Driver                      |
+---------------------+---------------------+---------+--------------+--------------+--------+
|      Object         |     Attribute       | BaGPipe | OpenContrail | OpenDaylight | Nuage  |
|                     |                     |         +------+-------+-------+------+        |
|                     |                     |         |  v1  |   v2  |   v1  |  v2  |        |
+=====================+=====================+=========+======+=======+=======+======+========+
|      bgpvpn         |    base object      |   Yes   |  Yes |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+---------+------+-------+-------+------+--------+
|                     | route_distinguisher |   No    |  No  |  No   |  Yes  | Yes  |   Yes  |
|                     +---------------------+---------+------+-------+-------+------+--------+
|                     |    route_targets    |   Yes   |  Yes |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+---------+------+-------+-------+------+--------+
|                     |    import_targets   |   Yes   |  Yes |  Yes  |  Yes  | Yes  |   Yes  |
|                     +---------------------+---------+------+-------+-------+------+--------+
|                     |    export_targets   |   Yes   |  Yes |  Yes  |  Yes  | Yes  |   Yes  |
+---------------------+---------------------+---------+------+-------+-------+------+--------+
| network_association |    base object      |   Yes   |  Yes |  Yes  |  Yes  | Yes  |   No   |
+---------------------+---------------------+---------+------+-------+-------+------+--------+
| router_association  |    base object      |   Yes   |  No  |  Yes  |  Yes  | Yes  |   Yes  |
+---------------------+---------------------+---------+------+-------+-------+------+--------+