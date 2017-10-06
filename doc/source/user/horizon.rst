========
Horizon
========

General information
===================

Networking-bgpvpn contains the bgpvpn_dashboard plugin for Horizon.
It adds a BGPVPN Interconnections panel in the admin section. Admin users can
handle BGPVPNs resources through this panel.
The operations possible for admin users are:

* listing BGPVPN
* creating a BGPVPN
* editing a BGPVPN
* associating or disassociating a BGPVPN to network(s)
* associating or disassociating a BGPVPN to router(s)
* deleting a BGPVPN

For non admin users the plugin adds a BGPVPN Interconnections panel in the Project
section under the Network subsection.
The operations possible for non admin users are:

* listing BGPVPN (display only name, type, networks and routers associations)
* editing a BGPVPN (only the name)
* associating or disassociating a BGPVPN to network(s)
* associating or disassociating a BGPVPN to router(s)

Installation and Configuration
==============================

Devstack will automatically configure Horizon to enable the Horizon plugin.

For others deployments we assume that Horizon and networking-bgpvpn are already
installed. Their installation folders are respectively <horizon> and
<networking-bgpvpn>.


Copy configuration file:

.. code-block:: shell

   cp <networking-bgpvpn>/bgpvpn_dashboard/enabled/_[0-9]*.py <horizon>/openstack_dashboard/local/enabled/

Configure the policy file for BGPVPN dashboard in OpenStack Dashboard ``local_settings.py``.
``<bgpvpn-dashboard-dir>`` is a directory which contains configurations for
BGPVPN dashboard and the location varies across distributions or deployments.
``<bgpvpn-dashboard-dir>`` can be found with: ``dirname $(python -c 'import bgpvpn_dashboard as _; print _.__file__')``

.. code-block:: python

   POLICY_FILES[' networking-bgpvpn'] = '<bgpvpn-dashboard-dir>/bgpvpn_dashboard/etc/bgpvpn-horizon.conf'

.. note::

   If you do not configure ``POLICY_FILES`` in your ``local_settings.py``,
   you also need to define the default ``POLICY_FILES`` in
   ``local_settings.py``. If you use the example ``local_settings.py`` file
   from horizon, what you need is to uncomment ``POLICY_FILES`` (which contains
   the default values).

Restart the web server hosting Horizon.

The BGPVPN Interconnections panels will now be in your Horizon dashboard.
