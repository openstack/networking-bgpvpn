..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

Specification notes
===================

Database design
---------------

The implementation will rely on three tables:

* one for BGPVPN objects

* one to define the n-n relation ship between BGPVPNs and Networks

* one to define the n-n relation ship between BGPVPNs and Routers


The information stored in these tables will reflect what is exposed on the
API.


