===================
OpenContrail driver
===================

The **OpenContrail** driver for the BGPVPN service plugin is designed to work
jointly with the `OpenContrail SDN controller`_.

OpenContrail proposes a `contrail installer`_ script which is similar to devstack,
and can be used to deploy a devi/test environment.

* Clone that OpenContrail installer script::

        git clone git@github.com:Juniper/contrail-installer

* Compile and run OpenContrail::

        cd ~/contrail-installer
        cp samples/localrc-all localrc (edit localrc as needed)
        ./contrail.sh build
        ./contrail.sh install
        ./contrail.sh configure
        ./contrail.sh start

* Then clone devstack::

        git clone git@github.com:openstack-dev/devstack

* A glue file is needed in the interim till it is upstreamed to devstack::

        cp ~/contrail-installer/devstack/lib/neutron_plugins/opencontrail lib/neutron_plugins/

* Use a sample ``localrc``::

        cp ~/contrail-installer/devstack/samples/localrc-all localrc

* add the following to enable the OpenContrail driver for the BGPVPN service plugin::

        NETWORKING_BGPVPN_DRIVER="BGPVPN:OpenContrail:networking_bgpvpn.neutron.services.service_drivers.opencontrail.opencontrail.OpenContrailBGPVPNDriver:default"

* Run stack.sh::

        ./stack.sh

.. _OpenContrail SDN controller : https://github.com/Juniper/contrail-controller
.. _contrail installer : https://github.com/Juniper/contrail-installer
