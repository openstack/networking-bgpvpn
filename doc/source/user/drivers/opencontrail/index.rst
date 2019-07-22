===================
OpenContrail driver
===================

Introduction
------------

The **OpenContrail** driver for the BGPVPN service plugin is designed to work
jointly with the `OpenContrail SDN controller`_ (`GitHub`_). The BGP VPN driver
can be found in the `monolithic Neutron plugin tree`__ [#]_.

.. Note::

   The BGPVPN Contrail driver that was under ``networking_bgpvpn`` (``networking_bgpvpn.neutron.services.service_drivers.opencontrail.opencontrail.OpenContrailBGPVPNDriver``)
   has been deprecated in Queens release, and has been completly removed in
   Stein release. The documentation below refers to the production ready
   `driver`_ under ``Juniper/contrail-neutron-plugin``. Be careful, **no**
   migration path is planned.

Limitations
-----------

Route Distinguishers
~~~~~~~~~~~~~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin does not permit
specifying `route distinguisher`_.

Resource Association
~~~~~~~~~~~~~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin does not yet support
`association with ports`_. But it supports `network associations`_ and `router
associations`_.

VPN Type
~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin can create L2 & L3 VPN
types for network associations and L3 VPN type for router association.

How to use ?
------------

On an Openstack Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[TBC (package installation + config)]

In devstack
~~~~~~~~~~~

A `devstack plugin`_ can be used to setup an OpenContrail dev/test platform.

* Clone devstack:

  .. code-block:: console

     git clone git@github.com:openstack-dev/devstack

* Here a proposed devstack ``local.conf`` file which permits to deploy
  OpenStack keystone, glance, nova, neutron/networking-bgpvpn and
  compile/install all OpenContrail services and dependencies:

.. code-block:: bash

 [[local|localrc]]
 LOG=True
 LOGDAYS=1
 PASSWORD="secret"
 DATABASE_PASSWORD=$PASSWORD
 RABBIT_PASSWORD=$PASSWORD
 SERVICE_TOKEN=$PASSWORD
 SERVICE_PASSWORD=$PASSWORD
 ADMIN_PASSWORD=$PASSWORD

 # disable some nova services
 disable_service n-obj n-novnc n-cauth
 # disable cinder
 disable_service cinder c-api c-vol c-sch
 # disable heat
 disable_service h-eng h-api h-api-cfn h-api-cw
 # diable horizon
 disable_service horizon
 # disable swift
 disable_service swift s-proxy s-object s-container s-account
 # disable some contrail services
 #disable_service ui-webs ui-jobs named dns query-engine

 DEST=/opt/stack/openstack
 CONTRAIL_DEST=/opt/stack/contrail

 enable_plugin contrail https://github.com/zioc/contrail-devstack-plugin.git

 enable_plugin networking-bgpvpn https://opendev.org/openstack/networking-bgpvpn.git
 NETWORKING_BGPVPN_DRIVER="BGPVPN:OpenContrail:neutron_plugin_contrail.plugins.opencontrail.networking_bgpvpn.contrail.ContrailBGPVPNDriver:default"

.. [#] That driver requires OpenContrail release upper or equal to 4.0
.. _OpenContrail SDN controller: http://www.opencontrail.org/
.. _GitHub: https://github.com/Juniper/contrail-controller
.. _driver: https://github.com/Juniper/contrail-neutron-plugin/tree/master/neutron_plugin_contrail/plugins/opencontrail/networking_bgpvpn
__ driver_
.. _route distinguisher: https://docs.openstack.org/api-ref/network/v2/#on-route-distinguishers-rds
.. _router associations: https://docs.openstack.org/api-ref/network/v2/#router-associations
.. _network associations: https://docs.openstack.org/api-ref/network/v2/#network-associations
.. _association with ports: https://docs.openstack.org/api-ref/network/v2/#port-associations
.. _devstack plugin: https://github.com/zioc/contrail-devstack-plugin
