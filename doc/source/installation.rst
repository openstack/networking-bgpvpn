============
Installation
============

The details related to how a package should be installed may depend on your
environment.

If possible, you should rely on packages provided by your Linux and/or
Openstack distribution.

If you use ``pip``, follow these steps to install networking-bgpvpn:

    * identify the version of the networking-bgpvpn package that matches
      your Openstack version:

      * Newton: most recent of 5.0.x
      * Mitaka: most recent of 4.0.x
      * Liberty: most recent of 3.0.x
      * (see `<http://git.openstack.org/cgit/openstack/releases/tree/deliverables/_independent/networking-bgpvpn.yaml>`_)

    * indicate pip to (a) install precisely this version and (b) take into
      account Openstack upper constraints on package versions for dependencies
      (example for newton)::

          $ pip install -c  https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=stable/newton networking-bgpvpn=5.0.0

=============
Configuration
=============

The service plugin is enabled in Neutron, by
adding ``bgpvpn`` to the list
of enabled service plugins in ``neutron.conf`` (typically in ``/etc/neutron/``
but the location used may depend on your setup or packaging). For instance::

    service_plugins = router,bgpvpn

The BGPVPN driver to use is then specified in the ``networking_bgpvpn.conf``
file (located by default under ``/etc/neutron/``, but in any case in one of the
directories specified with ``--config-dir`` at neutron startup, which may
differ from ``/etc/neutron`` in your setup)::

    [service_providers]
    service_provider = BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default
    #service_provider= BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default

A given driver may require additional packages to work; the driver section
provides detailed installation information for each
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

By default, the service driver will use a dummy driver, that only responds to API calls, and stores data in the database.
If you want to test a fully functional driver with devstack, you can configure the bagpipe driver with its devstack plugin (see :doc:`bagpipe/index`).

Detailed information on how to use other drivers is provided in the documentation for each of these drivers.
