========
Heat
========

Installation and Configuration
==============================

Devstack will automatically configure heat to support BGPVPN.

Other deployments need to add the directory for the python networking_bgpvpn_heat module
to ``plugin_dirs`` in the heat config: ``/etc/heat/heat.conf``.

This directory can be found out with:

    .. code-block:: shell

       dirname $(python -c "import networking_bgpvpn_heat as n;print(n.__file__)")

Examples
========

Heat Orchestration Template (HOT) example 1
-------------------------------------------

This template has to be run with admin rights and will create
a BGPVPN for the current tenant, along with a Network associated with it:

    .. literalinclude:: ../../networking_bgpvpn_heat/examples/bgpvpn_test-00.yaml
       :language: yaml

In devstack, this HOT file can be used with cloud admin privileges in the demo
project; such privileges can be obtained with the command:

    .. code-block:: shell

       source openrc admin demo

This example can then be run:

    .. code-block:: shell-session

        $ heat stack-create networks -f bgpvpn_test-00.yaml
        +--------------------------------------+------------+--------------------+---------------------+--------------+
        | id                                   | stack_name | stack_status       | creation_time       | updated_time |
        +--------------------------------------+------------+--------------------+---------------------+--------------+
        | 5a6c2bf1-c5da-4f8f-9838-4c3e59d13d41 | networks   | CREATE_IN_PROGRESS | 2016-03-02T08:32:52 | None         |
        +--------------------------------------+------------+--------------------+---------------------+--------------+
    
        $ heat stack-list
        +--------------------------------------+------------+-----------------+---------------------+--------------+
        | id                                   | stack_name | stack_status    | creation_time       | updated_time |
        +--------------------------------------+------------+-----------------+---------------------+--------------+
        | 5a6c2bf1-c5da-4f8f-9838-4c3e59d13d41 | networks   | CREATE_COMPLETE | 2016-03-02T08:32:52 | None         |
        +--------------------------------------+------------+-----------------+---------------------+--------------+
        

Heat Orchestration Template (HOT) example 2
-------------------------------------------

This is a set of two templates:

* one that has to be run with admin rights and will create a BGPVPN for the 'demo' tenant:

    .. literalinclude:: ../../networking_bgpvpn_heat/examples/bgpvpn_test-04-admin.yaml
       :language: yaml

    .. code-block:: shell-session
 
       $ source openrc admin admin
       $ heat stack-create bgpvpn -f bgpvpn_test-04-admin.yaml

* one to run as a plain 'demo' tenant user, that will:

    * create a Network and bind it to the 'default_vpn' BGPVPN

    * create a second Network connected to a Router, and bind the Router to the 'default_vpn'

    .. literalinclude:: ../../networking_bgpvpn_heat/examples/bgpvpn_test-04-tenant.yaml
       :language: yaml

    .. code-block:: shell-session
 
       $ source openrc demo demo
       $ heat stack-create networks_bgpvpn -f bgpvpn_test-04-tenant.yaml
       +--------------------------------------+-----------------+--------------------+---------------------+--------------+
       | id                                   | stack_name      | stack_status       | creation_time       | updated_time |
       +--------------------------------------+-----------------+--------------------+---------------------+--------------+
       | a3cf1c1b-ac6c-425c-a4b5-d8ca894539f2 | networks_bgpvpn | CREATE_IN_PROGRESS | 2016-03-02T09:16:39 | None         |
       +--------------------------------------+-----------------+--------------------+---------------------+--------------+

       $ neutron bgpvpn-list 
       +--------------------------------------+-------------+------+-------------------------------------------+------------------------------------------------+
       | id                                   | name        | type | networks                                  | routers                                        |
       +--------------------------------------+-------------+------+-------------------------------------------+------------------------------------------------+
       | 473e5218-f4a2-46bd-8086-36d6849ecf8e | default VPN | l3   | [u'5b1af75b-0608-4e03-aac1-2608728be45d'] | [u'cb9c7304-e844-447d-88e9-4a0a2dc14d21']      |
       +--------------------------------------+-------------+------+-------------------------------------------+------------------------------------------------+


