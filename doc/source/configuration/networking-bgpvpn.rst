======================
networking-bgpvpn.conf
======================

To use networking-bgpvpn, you need to configure one of valid service providers
for ``BGPVPN`` service in ``service_provider`` of ``[service_providers]``
group of the neutron server. Note that you can specify multiple providers for
BGPVPN but only one of them can be default.

* Dummy provider: ``service_provider = BGPVPN:Dummy:networking_bgpvpn.neutron.services.service_drivers.driver_api.BGPVPNDriver:default``
* BaGPipe provider: ``service_provider = BGPVPN:BaGPipe:networking_bgpvpn.neutron.services.service_drivers.bagpipe.bagpipe.BaGPipeBGPVPNDriver:default``

.. show-options::
   :config-file: etc/oslo-config-generator/networking-bgpvpn.conf
