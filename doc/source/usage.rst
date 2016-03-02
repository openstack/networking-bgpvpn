========
Usage
========

Use from Neutron API CLI
------------------------

Example commands to use by the admin to create a BGPVPN resource:

	neutron bgpvpn-create --route-targets 64512:1 --tenant-id b954279e1e064dc9b8264474cb3e6bd2
	neutron bgpvpn-list
	neutron bgpvpn-update 1009a0f326b6403180c18f3caa1430de --name myBGPVPN --tenant 4a75e08c45f14aa9afc5da081c9bb534

Example commands to use by the tenant owning the BGPVPN to associate a Network to it:

	neutron bgpvpn-net-assoc-create myBGPVPN --network 828cddad3b834e79b79abc1b87b6cca0
	# returns <net-assoc-uuid>
	neutron bgpvpn-net-assoc-list myBGPVPN
	neutron bgpvpn-net-assoc-show <net-assoc-uuid> myBGPVPN 

	neutron bgpvpn-net-assoc-delete <net-assoc-uuid> myBGPVPN

Use from Horizon
----------------

(not supported yet)

Use from Heat
------------- 

See :doc:`heat`.

