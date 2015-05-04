How to use bagpipe driver for the BGPVPN plugin, jointly with the openvswitch ML2 mech driver ?
-----------------------------------------------------------------------------------------------

In devstack :

* ``local.conf``: 

  * enable the ``openvswitch`` ML2 mechanism driver, and activate the agent ARP responder (you need to enable l2population too for the ARP responder to be enabled)

  * add the following to enable the BaGPipe driver for the BGPVPN service plugin::

	[[post-config|/$NEUTRON_CONF]]
	[service_providers]
	service_provider=BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.bgpvpn.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default

  * add ``bgpvpn_notify`` to ``Q_ML2_PLUGIN_MECHANISM_DRIVERS``

    * (this mech_driver does not implement the setup of L2 networks; it is used only to notify the ``bagpipe`` driver for the BGPVPN plugin of L2 ports coming and going on compute nodes)

* on compute nodes:

  * install and configure bagpipe-bgp_, typically with a peering to a BGP Route Reflector or BGP routers

  * the compute node agent is ``bagpipe-openvswitch`` (openvswitch agent, modified to interact with ``bagpipe-bgp``):

    * install networking-bagpipe-l2_  (the code to interact with ``bagpipe-bgp`` comes from there)::

	enable_plugin networking-bagpipe-l2 git@github.com:stackforge/networking-bagpipe-l2.git

    * define ``Q_AGENT=bagpipe-openvswitch`` in ``local.conf``

    * (you need to ``git clone git@github.com:stackforge/networking-bgpvpn.git`` in /opt/stack manually before doing a ./stack.sh,
      or a devstack more recent than 2015-04-20 which includes https://review.openstack.org/#/c/168796 )

.. _bagpipe-bgp: https://github.com/Orange-OpenSource/bagpipe-bgp
.. _networking-bagpipe-l2: https://github.com/stackforge/networking-bagpipe-l2



