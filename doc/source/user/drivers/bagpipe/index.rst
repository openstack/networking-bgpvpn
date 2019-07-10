..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

================================
OVS/linuxbridge driver (bagpipe)
================================

Introduction
------------

The **BaGPipe** driver for the BGPVPN service plugin is designed to work jointly with the openvswitch
and linuxbridge ML2 mechanism drivers.

It relies on the use of the bagpipe-bgp BGP VPN implementation on compute nodes
and the MPLS implementation in OpenVSwitch and or linuxbridge.

Architecture overview
---------------------

The bagpipe driver for the BGPVPN service plugin interacts with the Neutron agent on each
compute node, which is extended to support new RPCs to trigger the local configuration on compute
nodes of BGP VPN instances and of their MPLS dataplane.

Example with the OpenVSwitch mechanism driver and agent:

.. blockdiag:: overview.blockdiag

Limitations
-----------

On DHCP ports, Router interface ports, external network ports, etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No connectivity will be setup with BGP VPNs for DHCP ports or Router
interface ports, or other network specific ports. This improves the load on network nodes by
avoiding them to import/export a significant amount of routes, without limiting BGP VPN
deployment scenarios because no useful traffic would be exchanged between a router or DHCP
interface of a network associated to a BGP VPN.

Similarly, the driver will not bind a port on an external network. This behavior will be
revisited once a use case is well identified.

bagpipe_v2 driver
-----------------

For Queens release, the mechanism used by this driver for RPCs was changed.

The v1 driver ``networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver``
is backwards compatible with pre-Queens neutron agents and can be used during
a rolling upgrade, e.g. from Pike to Queens.

The v2 driver ``networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe_v2.BaGPipeBGPVPNDriver``
does not produce the old RPCs anymore and can be used:

* on a greenfield deployment

* after an upgrade

* during a non-rolling upgrade (some BGPVPN operations would be
  disrupted during the time where pre-Queens agent still run)

Future developments may happen only on the v2 driver and the v1
driver will be ultimately abandoned.

How to use ?
------------

The steps to take to use this driver are generally:

* install the networking-bagpipe package on both
  control nodes and compute nodes

* on control node, configure neutron to use bagpipe driver

* on compute nodes, configure the neutron agent to use bagpipe_bgpvpn
  extension and configure bagpipe-bgp

Of course, the typical way is to have all this taken care of by
an automated Openstack installer.

In devstack
~~~~~~~~~~~

* follow the instruction in README.rst

* ``local.conf``:

  * add the following to enable the BaGPipe driver for the BGPVPN service plugin:

    .. code-block:: ini

       NETWORKING_BGPVPN_DRIVER="BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe_v2.BaGPipeBGPVPNDriver:default"

  * enable networking-bagpipe_, which contains code for agent extensions:

    .. code-block:: ini

       enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git
       # enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git stable/pike
       # enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git stable/queens

* on a control node, if you want to run the Fake Route-Reflector there (relevant only for a multinode setup):

  .. code-block:: none

     enable_service b-fakerr

* on compute nodes:

  * the compute node Neutron agent is the Neutron openvswitch or linuxbridge agent, with the ``bagpipe_bgpvpn`` agent extension:

    * install networking-bagpipe_  (the code to interact with ``bagpipe-bgp`` comes from there):

      .. code-block:: ini

         enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git
         # enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git stable/queens
         # enable_plugin networking-bagpipe https://opendev.org/openstack/networking-bagpipe.git stable/pike

    * the ``bagpipe_bgpvpn`` agent extension is automatically added to the agent configuration by the devstack plugin

  * bagpipe-bgp will be installed automatically (part of networking-bagpipe since Pike, or as a submodule before)

  * you need to enable and configure bagpipe-bgp, typically with a peering to a BGP Route-Reflector or BGP router(s):

    .. code-block:: ini

       enable_service b-bgp

       BAGPIPE_DATAPLANE_DRIVER_IPVPN=ovs
       BAGPIPE_DATAPLANE_DRIVER_EVPN=ovs

       # IP of your route-reflector or BGP router, or fakeRR
       # BAGPIPE_BGP_PEERS defaults to $SERVICE_HOST, which will point to the controller in a
       # multi-node devstack setup
       #BAGPIPE_BGP_PEERS=1.2.3.4,2.3.4.5

.. _networking-bagpipe: https://docs.openstack.org/networking-bagpipe/latest/

