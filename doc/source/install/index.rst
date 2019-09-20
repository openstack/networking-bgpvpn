=========================
Install and Configuration
=========================

Installation
============

The details related to how a package should be installed may depend on your
environment.

If possible, you should rely on packages provided by your Linux and/or
Openstack distribution.

If you use ``pip``, follow these steps to install networking-bgpvpn:

* identify the version of the networking-bgpvpn package that matches
  your Openstack version:

  * Liberty: most recent of 3.0.x
  * Mitaka: most recent of 4.0.x
  * Newton: most recent of 5.0.x
  * Ocata: most recent of 6.0.x
  * Pike: most recent of 7.0.x
  * (see `<https://releases.openstack.org/index.html>`_)

* indicate pip to (a) install precisely this version and (b) take into
  account Openstack upper constraints on package versions for dependencies
  (example for ocata):

  .. code-block:: console

     $ pip install -c https://releases.openstack.org/constraints/upper/ocata

Configuration
=============

The service plugin is enabled in Neutron, by
adding ``bgpvpn`` to the list
of enabled service plugins in ``neutron.conf`` (typically in ``/etc/neutron/``
but the location used may depend on your setup or packaging). For instance:

.. code-block:: ini

    service_plugins = router,bgpvpn

The BGPVPN driver to use is then specified in the ``networking_bgpvpn.conf``
file (located by default under ``/etc/neutron/``, but in any case in one of the
directories specified with ``--config-dir`` at neutron startup, which may
differ from ``/etc/neutron`` in your setup):

.. code-block:: ini

   [service_providers]
   service_provider = BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe_v2.BaGPipeBGPVPNDriver:default
   #service_provider= BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default

A given driver may require additional packages to work; the driver section
provides detailed installation information for each
specific driver.

Policy
======

API Policy for the BGPVPN service plugin can be controlled via the standard policy framework.

When pip is used to install the package, a default policy file is installed at ``/etc/neutron/policy.d/bgpvpn.conf``.

Database setup
==============

The DB tables for networking-bgpvpn are created and upgraded with:

.. code-block:: console

   neutron-db-manage --config-file /etc/neutron/neutron.conf --subproject networking-bgpvpn upgrade

Devstack
========

You can easily test the bgpvpn service plugin with devstack, by adding the following line to your local.conf:

.. code-block:: none

   enable_plugin networking-bgpvpn https://git.openstack.org/openstack/networking-bgpvpn.git

Or the following if you want a specific branch or version (example for Mitaka):

.. code-block:: none

   enable_plugin networking-bgpvpn https://git.openstack.org/openstack/networking-bgpvpn.git stable/mitaka

By default, the service driver will use a dummy driver, that only responds to API calls, and stores data in the database.
If you want to test a fully functional driver with devstack, you can configure the bagpipe driver with its devstack plugin (see :doc:`/user/drivers/bagpipe/index`).

Detailed information on how to use other drivers is provided in the documentation for each of these drivers.
