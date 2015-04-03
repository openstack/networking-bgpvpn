===============================
networking-bgpvpn
===============================

API and Framework to interconnect BGP/MPLS VPNs to Openstack Neutron networks

* Free software: Apache license
* Source: http://git.openstack.org/cgit/stackforge/networking-bgpvpn
* Bugs: http://bugs.launchpad.net/bgpvpn

Quick start
-----------

To be able to test this framework, you have to:

* install devstack

* add the devstack plugin for the BGPVPN service plugin to your ``local.conf``: ::

	[[local|localrc]]
	enable_plugin networking-bgpvpn git@github.com:stackforge/networking-bgpvpn.git

* add the following to your ``local.conf``: ::

	Q_SERVICE_PLUGIN_CLASSES=networking_bgpvpn.neutron.services.bgpvpn.plugin.BGPVPNPlugin
	
	[[post-config|/$NEUTRON_CONF]]
	[service_providers]
	service_provider=BGPVPN:Dummy:networking_bgpvpn.neutron.services.bgpvpn.service_drivers.dummy.dummyBGPVPNDriver:default

* bgpvpn-connection-create/update/delete/show/list commands will be available with 
  the neutron client, for example: ::

	source openrc admin admin
	neutron bgpvpn-connection-create --route-targets 64512:1
	neutron bgpvpn-connection-list
	neutron bgpvpn-connection-update <bgpvpn-connection-uuid> --network-id <neutron-net-uuid>

