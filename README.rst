===============================================
BGP-MPLS VPN Extension for OpenStack Networking
===============================================

This project provides an API and Framework to interconnect BGP/MPLS VPNs
to Openstack Neutron networks, routers and ports.

The Border Gateway Protocol and Multi-Protocol Label Switching are widely
used Wide Area Networking technologies. The primary purpose of this project
is to allow attachment of Neutron networks and/or routers to VPNs built in
carrier provided WANs using these standard protocols. An additional purpose
of this project is to enable the use of these technologies within the Neutron
networking environment.

A vendor-neutral API and data model are provided such that multiple backends
may be "plugged in" while offering the same tenant facing API. A reference
implementation based on an Open Source BGP implementation is also provided.

* Free software: Apache license
* Source: http://git.openstack.org/cgit/openstack/networking-bgpvpn
* Bugs: http://bugs.launchpad.net/bgpvpn
* Doc: http://docs.openstack.org/developer/networking-bgpvpn

