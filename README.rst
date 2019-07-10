========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/networking-bgpvpn.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

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

A vendor-neutral API and data model are provided such that multiple SDN
controllers may be used as backends, while offering the same tenant facing API.
A reference implementation working along with Neutron reference drivers is
also provided.

* Free software: Apache license
* Source: https://opendev.org/openstack/networking-bgpvpn
* Bugs: https://bugs.launchpad.net/bgpvpn
* Doc: https://docs.openstack.org/networking-bgpvpn/latest/
* Release notes: https://docs.openstack.org/releasenotes/networking-bgpvpn/

===================
Introduction videos
===================

The following videos are filmed presentations of talks given during the
Barcelona OpenStack Summit (Oct' 2016). Although they do not cover the work
done since, they can be a good introduction to the project:

* https://www.youtube.com/watch?v=kGW5R8mtmRg
* https://www.youtube.com/watch?v=LCDeR7MwTzE
