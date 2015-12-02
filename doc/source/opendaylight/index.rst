===================
OpenDaylight driver
===================

The **OpenDaylight** driver for the BGPVPN service plugin is designed to work
jointly with the OpenDaylight SDN controller.

OpenDaylight driver requires `networking-odl plugin`_ which comes with its own
devstack scripts. Details on how to configure devstack for OpenDaylight
plugin can be found at `networking-odl/devstack`_.

* add the following to local.conf to enable networking-odl plugin::

        enable_plugin networking-odl http://git.openstack.org/openstack/networking-odl

* add the following to local.conf to enable ODL Driver for BGPVPN service Plugin::

        NETWORKING_BGPVPN_DRIVER="BGPVPN:OpenDaylight:networking_bgpvpn.neutron.services.service_drivers.opendaylight.odl.OpenDaylightBgpvpnDriver:default"

* Run stack.sh::

        ./stack.sh

.. _networking-odl plugin : https://launchpad.net/networking-odl
.. _networking-odl/devstack : https://github.com/openstack/networking-odl/tree/master/devstack
