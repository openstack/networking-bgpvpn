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

* bgpvpn-create/update/associate/delete/show/list commands will be available with
  the neutron client, for example: ::

	source openrc admin admin
	neutron bgpvpn-create --route-targets 64512:1 --tenant-id b954279e1e064dc9b8264474cb3e6bd2
	neutron bgpvpn-list
	neutron bgpvpn-update 1009a0f326b6403180c18f3caa1430de --name foo
	neutron bgpvpn-network-associate foo --network 828cddad3b834e79b79abc1b87b6cca0

To test this framework with the **bagpipe** reference driver, you can follow :doc:`README-bagpipe.rst` .

