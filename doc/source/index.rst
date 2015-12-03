..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=============================================
Neutron BGP VPN Interconnection Documentation
=============================================

Introduction
============

BGP-based IP VPNs networks are widely used in the industry especially for
enterprises. This project aims at supporting inter-connection between L3VPNs
and Neutron resources, i.e. Networks, Routers and Ports.

A typical use-case is the following: a tenant already having a BGP IP VPN
(a set of external sites) setup outside the datacenter, and they want to be able
to trigger the establishment of connectivity between VMs and these VPN sites.

Another similar need is when E-VPN is used to provide an Ethernet interconnect
between multiple sites.

This service plugin exposes an API to interconnect OpenStack Neutron ports,
typically VMs, via the Networks and Routers they are connected to, with
an L3VPN network as defined by [RFC4364]_ (BGP/MPLS IP Virtual Private Networks).
The framework is generic to also support E-VPN [RFC7432]_, which inherits the
same protocol architecture as BGP/MPLS IP VPNs.

Contents
========

.. toctree::
   :maxdepth: 2

   overview
   api
   installation
   usage
   heat
   contributing
   specs
   future/index

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

