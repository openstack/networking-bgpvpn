============
Installation
============

The details related to how a package should be installed may depend on your environment.

If you use pip, the following will install the networking-bgpvpn package:::

    $ pip install networking-bgpvpn

=============
Configuration
=============

The service plugin is enabled in Neutron, by adding ``networking_bgpvpn.neutron.services.plugin.BGPVPNPlugin`` to the list
of enabled service plugins in ``/etc/neutron/neutron.conf``. For instance::

    service_plugins = networking_bgpvpn.neutron.services.plugin.BGPVPNPlugin,neutron.services.l3_router.l3_router_plugin.L3RouterPlugin

The BGPVPN driver to use is then specified in ``/etc/neutron/networking_bgpvpn.conf``, for instance::

    [service_providers]
    service_provider = BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default
    #service_provider= BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default

A given driver may require additional package to work; the driver section provides detailed installation information for each
specific driver.

==============
Policy
==============

API Policy for the BGPVPN service plugin can be controlled via the standard policy framework.

When pip is used to install the package, a default policy file is installed at ``/etc/neutron/policy.d/bgpvpn.conf``.

==============
Database setup
==============

The DB tables for networking-bgpvpn are created and upgraded with::

    neutron-db-manage --config-file /etc/neutron/neutron.conf --subproject networking-bgpvpn upgrade

==============
Devstack
==============

You can easily test the bgpvpn service plugin with devstack, by adding the following line to your local.conf::

    enable_plugin networking-bgpvpn git://git.openstack.org/openstack/networking-bgpvpn.git

Or the following if you want a specific branch or version (example for Mitaka)::

    enable_plugin networking-bgpvpn git://git.openstack.org/openstack/networking-bgpvpn.git stable/mitaka

By default, the service driver will use a dummy driver, that only responds to API calls, and stores datas in the database.
If you want to test a fully functional driver with devstack, you can configure the bagpipe driver with its devstack plugin (see :doc:`bagpipe/index`).

Detailed information on how to use other drivers is provided in the documentation for each of these drivers.
