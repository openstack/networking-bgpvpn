..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=====================
Nuage Networks driver
=====================

The Nuage Network driver works jointly with Nuage Networks VSP.

A pre-requisite for the nuage BGPVPN driver is that the Nuage-specific
installation and configuration steps have been applied; in particular the
installation of the ``nuage_neutron`` package. Please refer to Nuage Networks
documentation.

The driver will be enabled, by specifying in ``/etc/neutron/networking_bgpvpn.conf``::

    [service_providers]
    service_provider = BGPVPN:Nuage:nuage_neutron.bgpvpn.services.service_drivers.driver.NuageBGPVPNDriver:default
