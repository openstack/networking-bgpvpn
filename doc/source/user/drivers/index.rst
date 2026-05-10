=======
Drivers
=======

The BGPVPN service plugin supports the following drivers:

.. toctree::
   :maxdepth: 1

   bagpipe/index

The API is consistent across drivers, but not all drivers support all parts of
the API. Refer to the Driver Compatibility Matrix to determine what is
supported with each driver.

Driver Compatibility Matrix
---------------------------

+----------------------------------------------+-----------+
|               API                            |  Driver   |
+---------------------+------------------------+-----------+
|      Object         |     Attribute          | Neutron   |
|                     |                        | (bagpipe) |
+=====================+========================+===========+
|      bgpvpn         |    base object         |   ✔       |
+---------------------+-------+----------------+-----------+
|                     |       |     L3         |   ✔       |
|                     | type  +----------------+-----------+
|                     |       |     L2         |   ✔       |
|                     +-------+----------------+-----------+
|                     |    route_targets       |   ✔       |
+---------------------+------------------------+-----------+
|                     |    import_targets      |   ✔       |
|                     +------------------------+-----------+
|                     |    export_targets      |   ✔       |
|                     +------------------------+-----------+
|                     | route_distinguishers   |           |
|                     +------------------------+-----------+
|                     |         vni            |   ✔       |
|                     +------------------------+-----------+
|                     |     local_pref         |   ✔       |
+---------------------+------------------------+-----------+
| network_association |    base object         |   ✔       |
+---------------------+------------------------+-----------+
| router_association  |    base object         |   ✔       |
+---------------------+------------------------+-----------+
|                     | advertise_extra_routes |           |
+---------------------+------------------------+-----------+
| port_association    |    base object         |   ✔       |
+---------------------+------------------------+-----------+
|                     |  advertise_fixed_ips   |   ✔       |
+---------------------+------------------------+-----------+
|                     |     routes:prefix      |   ✔       |
+---------------------+------------------------+-----------+
|                     |     routes:bgpvpn      |   ✔       |
+---------------------+------------------------+-----------+
|                     |    routes:local_pref   |   ✔       |
+---------------------+------------------------+-----------+
