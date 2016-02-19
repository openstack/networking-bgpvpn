========
Heat
========

Installation and Configuration
=============================
Devstack will automatically configure bgpvpn heat support.
Other deployments need to add $NETWORKING_BGPVPN_DIR/networking_bgpvpn_heat
to plugin_dirs in the heat config: /etc/heat/heat.conf.

NETWORKING_BGPVPN_DIR can be found out with:

  ``python -c "import networking_bgpvpn as n;print(n.__file__)"``

The following HOT file can be used with cloud admin privileges in the demo
project. Within devstack, such privileges can be obtained with the command:

  ``source openrc admin demo``

Heat Orchestration Template (HOT) example
-----------------------------------------
::

    description: BGPVPN networking example
    heat_template_version: '2013-05-23'
    resources:

      Net1:
        type: OS::Neutron::Net

      SubNet1:
        type: OS::Neutron::Subnet
        properties:
          network: { get_resource: Net1 }
          cidr: 192.168.10.0/24

      BGPVPN1:
        type: OS::Neutron::BGPVPN
        properties:
          import_targets: [ '100:1001' ]
          export_targets: [ '100:1002' ]
          route_targets: [ '100:1000', '200:2000' ]
          type: l3

      BGPVPN_NET_assoc1:
        type: OS::Neutron::BGPVPN-NET-ASSOCIATION
        properties:
          bgpvpn_id: { get_resource: BGPVPN1 }
          network_id: { get_resource: Net1 }

      Router1:
        type: OS::Neutron::Router

      BGPVPN_ROUTER_assoc1:
        type: OS::Neutron::BGPVPN-ROUTER-ASSOCIATION
        properties:
          bgpvpn_id: { get_resource: BGPVPN1 }
          router_id: { get_resource: Router1 }
