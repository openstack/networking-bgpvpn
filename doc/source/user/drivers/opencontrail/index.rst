===================
OpenContrail driver
===================

Introduction
------------

The **OpenContrail** driver for the BGPVPN service plugin is designed to work
jointly with the `OpenContrail SDN controller <http://www.opencontrail.org/>`__
(`GitHub <https://github.com/Juniper/contrail-controller>`__).

Limitations
-----------

VPN Type
~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin can create only L3 VPN
type. The L2 is not yet supported.


Route Distinguishers
~~~~~~~~~~~~~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin does not permit
specifying `route distinguisher`_.

Router Association
~~~~~~~~~~~~~~~~~~

The OpenContrail driver for the BGPVPN service plugin does not support
`associations with routers`_. Only `network associations`_ are available for the
moment.

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
  compile/install all OpenContrail services and dependences:

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

 enable_plugin networking-bgpvpn git://git.openstack.org/openstack/networking-bgpvpn.git
 NETWORKING_BGPVPN_DRIVER="BGPVPN:OpenContrail:networking_bgpvpn.neutron.services.service_drivers.opencontrail.opencontrail.OpenContrailBGPVPNDriver:default"

.. _route distinguisher : https://developer.openstack.org/api-ref/networking/v2/#on-route-distinguishers-rds
.. _associations with routers : https://developer.openstack.org/api-ref/networking/v2/#router-associations
.. _network associations : https://developer.openstack.org/api-ref/networking/v2/#network-associations
.. _devstack plugin : https://github.com/zioc/contrail-devstack-plugin
