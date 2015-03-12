===============================
networking-bgpvpn
===============================

API and Framework to interconnect bgpvpn to neutron networks

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/networking-bgpvpn
* Source: http://git.openstack.org/cgit/stackforge/networking-bgpvpn
* Bugs: http://bugs.launchpad.net/bgpvpn

Features
--------

to be able to test this framework, you have to :

-clone this repo and install the python package :
#git clone http://git.openstack.org/cgit/stackforge/networking-bgpvpn
#sudo python setup.py develop

-run the latest devstack (and let it fetch latest openstack code)
with the following options :
Q_SERVICE_PLUGIN_CLASSES=networking_bgpvpn.neutron.services.bgpvpn.plugin.BGPVPNPlugin
[[post-config|/$NEUTRON_CONF]]
[service_providers]
service_provider=BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.bgpvpn.service_drivers.dummy.dummyBGPVPNDriver:default

-update the db with :
#/usr/local/bin/bgpvpn-db-manage --config-file /etc/neutron/neutron.conf --config-file /etc/neutron/plugins/ml2/ml2_conf.ini upgrade head

-bgpvpn-connection-create/update/delete/show/list commands will be available with the neutron client
for example :
#. openrc admin admin
#neutron bgpvpn-connection-create --route-targets 64512:1
#neutron bgpvpn-connection-list