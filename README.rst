=================
networking-bgpvpn
=================

API and Framework to interconnect BGP/MPLS VPNs to Openstack Neutron networks

* Free software: Apache license
* Source: http://git.openstack.org/cgit/openstack/networking-bgpvpn
* Bugs: http://bugs.launchpad.net/bgpvpn

Quick start
-----------

To test this framework with the **dummy** driver (not doing any real interaction with BGP nor
the forwarding plane) you have to:

* install devstack

* add the devstack plugin for the BGPVPN service plugin to your ``local.conf``: ::

	[[local|localrc]]
	enable_plugin networking-bgpvpn git@github.com:openstack/networking-bgpvpn.git

* add the following to your ``local.conf``: ::

	[[post-config|$NETWORKING_BGPVPN_CONF]]
	[service_providers]
	service_provider=BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default

* bgpvpn-connection-create/update/delete/show/list commands will be available with
  the neutron client, for example: ::

	source openrc admin admin
	neutron bgpvpn-connection-create --route-targets 64512:1
	neutron bgpvpn-connection-list
	neutron bgpvpn-connection-update <bgpvpn-connection-uuid> --network-id <neutron-net-uuid>


To test this framework with the **bagpipe** reference driver, you can follow :doc:`README-bagpipe` .

