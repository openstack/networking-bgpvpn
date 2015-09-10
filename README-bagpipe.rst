How to use bagpipe driver for the BGPVPN plugin, jointly with the openvswitch ML2 mech driver ?
-----------------------------------------------------------------------------------------------

The **bagpipe** driver for the BGPVPN service plugin is designed to work jointly with the openvswitch
ML2 mechanism driver.  It relies on the use of the _bagpipe-bgp BGP VPN implementation on compute node
and the MPLS implementation in OpenVSwitch.

In devstack :

* ``local.conf``: 

  * enable the ``openvswitch`` ML2 mechanism driver, and activate the agent ARP responder (you need to enable l2population too for the ARP responder to be enabled)

  * add the following to enable the BaGPipe driver for the BGPVPN service plugin::

     [[post-config|/$NETWORKING_BGPVPN_CONF]]
     [service_providers]
     service_provider=BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default

* on a control node, if you want to run the Fake Route-Reflector there::

     enable_plugin bagpipe-bgp https://github.com/Orange-OpenSource/bagpipe-bgp.git
     enable_service b-fakerr

* on compute nodes:

  * install and configure bagpipe-bgp_, typically with a peering to a BGP Router-Reflector or BGP routers, can be done through devstack
    like this::

        enable_plugin bagpipe-bgp https://github.com/Orange-OpenSource/bagpipe-bgp.git
        BAGPIPE_DATAPLANE_DRIVER_IPVPN=mpls_ovs_dataplane.MPLSOVSDataplaneDriver
        # IP of your route-reflector or BGP router, or fakeRR
        # (typically $SERVICE_HOST on compute node, if the control node is running the RR)
        BAGPIPE_BGP_PEERS=1.2.3.4
        enable_service b-bgp

  * the compute node agent is ``bagpipe-openvswitch`` (inherits from openvswitch agent, with additions to interact with ``bagpipe-bgp``):

    * install networking-bagpipe-l2_  (the code to interact with ``bagpipe-bgp`` comes from there)::

        enable_plugin networking-bagpipe-l2 git@github.com:openstack/networking-bagpipe-l2.git

    * define ``Q_AGENT=bagpipe-openvswitch`` in ``local.conf``

Note well: you need to ``git clone git@github.com:openstack/networking-bgpvpn.git`` in /opt/stack manually before doing a ./stack.sh,
or a devstack more recent than 2015-04-20 which includes https://review.openstack.org/#/c/168796

.. _bagpipe-bgp: https://github.com/Orange-OpenSource/bagpipe-bgp
.. _networking-bagpipe-l2: https://github.com/openstack/networking-bagpipe-l2



