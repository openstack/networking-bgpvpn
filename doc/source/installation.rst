============
Installation
============

The details related to how a package should be installed may depend on your environment.

If you use pip, the following will install the networking-bgppvn package:::

    $ pip install networking-bgpvpn

=============
Configuration
=============

The service plugin is enabled in Neutron, by adding ``networking_bgpvpn.neutron.services.plugin.BGPVPNPlugin`` to the list
of enabled service plugins in ``/etc/neutron.conf``. For instance::

    service_plugins = networking_bgpvpn.neutron.services.plugin.BGPVPNPlugin,neutron.services.l3_router.l3_router_plugin.L3RouterPlugin

The BGPVPN driver to use is then specified in ``/etc/neutron/networking_bgpvpn.conf``, for instance::

    [service_providers]
    service_provider = BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default
    #service_provider= BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default

A said driver may require additional package to work; the driver section provides detailed installation information for each
specific driver.

==============
Policy
==============

API Policy for the BGPVPN service plugin can be controlled via the standard policy framework.

When pip is used to install the package, a default policy file is intalled at ``/etc/neutron/policy.d/bgpvpn.conf``.

==============
Database setup
==============

The DB tables for networking-bgpvpn are created and upgraded with::

    neutron-db-manage --config-file /etc/neutron/neutron.conf --subproject networking-bgpvpn upgrade


