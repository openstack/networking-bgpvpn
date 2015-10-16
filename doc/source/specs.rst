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

* one to define the 1-n relation ship between a BGPVPN and a set of Networks

* one to define the 1-n relation ship between a BGPVPN and a set of Routers


The information stored in these tables will reflect what is exposed on the
API, with an exception for route_targets:

* this list will not be present in the database

* on an API request to create or modify a BGPVPN: the route_targets
  parameter will be merged with import_rts, without duplicates, before storing
  in import_rts ; and the same will be done for export_rts

* on an API request to show a BGPVPN:

  * route_targets will be synthesized to include RTs present in both
    export_rts and import_rts

  * import_targets will contain only RTs not in common with export_rts

  * export_targets will contain only RTs not in common with import_rts


