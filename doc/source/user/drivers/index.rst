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

+----------------------------------------------+-------------------------------------------------+
|               API                            |                        Driver                   |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|      Object         |     Attribute          | Neutron   | OpenContrail | OpenDaylight | Nuage |
|                     |                        | (bagpipe) |      [#]_    |      [#]_    |       |
+=====================+========================+===========+==============+==============+=======+
|      bgpvpn         |    base object         |   ✔       |       ✔      |       ✔      |   ✔   |
+---------------------+-------+----------------+-----------+--------------+--------------+-------+
|                     |       |     L3         |   ✔       |       ✔      |       ✔      |   ✔   |
|                     | type  +----------------+-----------+--------------+--------------+-------+
|                     |       |     L2         |   ✔       |       ✔      |       ✔      |       |
|                     +-------+----------------+-----------+--------------+--------------+-------+
|                     |    route_targets       |   ✔       |       ✔      |       ✔      |   ✔   |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     |    import_targets      |   ✔       |       ✔      |       ✔      |   ✔   |
|                     +------------------------+-----------+--------------+--------------+-------+
|                     |    export_targets      |   ✔       |       ✔      |       ✔      |   ✔   |
|                     +------------------------+-----------+--------------+--------------+-------+
|                     | route_distinguishers   |           |              |       ✔      |   ✔   |
|                     +------------------------+-----------+--------------+--------------+-------+
|                     |         vni            |   ✔       |              |       ✔      |       |
|                     +------------------------+-----------+--------------+--------------+-------+
|                     |     local_pref         |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
| network_association |    base object         |   ✔       |       ✔      |       ✔      |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
| router_association  |    base object         |   ✔       |       ✔      |       ✔      |   ✔   |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     | advertise_extra_routes |           |              |     [#]_     |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
| port_association    |    base object         |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     |  advertise_fixed_ips   |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     |     routes:prefix      |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     |     routes:bgpvpn      |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+
|                     |    routes:local_pref   |   ✔       |              |              |       |
+---------------------+------------------------+-----------+--------------+--------------+-------+

.. [#] This applies to the `current BGPVPN Contrail driver <https://github.com/Juniper/contrail-neutron-plugin/src/branch/master/master/neutron_plugin_contrail/plugins/opencontrail/networking_bgpvpn>`_
       sometimes called *v2 driver*, which is different from the now
       obsolete *v1 driver* that was under ``networking_bgpvpn``.
.. [#] This applies to the `current BGPVPN ODL v2 driver <https://opendev.org/openstack/networking-odl/src/branch/master/networking_odl/bgpvpn/odl_v2.py>`_
       sometimes called *v2 driver*, which is different from the now
       obsolete *v1 driver* that was under ``networking_bgpvpn``.
.. [#] The behavior corresponding to ``advertise_extra_routes: true``, is
       supported as the default with ODL, without support in the API for
       turning it off.
