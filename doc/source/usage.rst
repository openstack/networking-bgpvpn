========
Usage
========

Use from Neutron API CLI
------------------------

Example commands to use by the admin to create a BGPVPN resource:

.. code-block:: shell

	neutron bgpvpn-create --route-targets 64512:1 --tenant-id b954279e1e064dc9b8264474cb3e6bd2
	neutron bgpvpn-list
	neutron bgpvpn-update 1009a0f326b6403180c18f3caa1430de --name myBGPVPN --tenant 4a75e08c45f14aa9afc5da081c9bb534

Example commands to use by the tenant owning the BGPVPN to associate a Network to it:

.. code-block:: shell

	neutron bgpvpn-net-assoc-create myBGPVPN --network 828cddad3b834e79b79abc1b87b6cca0
	# returns <net-assoc-uuid>
	neutron bgpvpn-net-assoc-list myBGPVPN
	neutron bgpvpn-net-assoc-show <net-assoc-uuid> myBGPVPN 

	neutron bgpvpn-net-assoc-delete <net-assoc-uuid> myBGPVPN

Use from Horizon
----------------

See :doc:`horizon`.

Use from Heat
-------------

See :doc:`heat`.

Use from Python
---------------

The BGPVPN API is dynamically loaded by Neutron. There is the same behaviour with the Python lib "neutronclient" use.
This allows to programmatically handle BGPVPN resources as well as Network association resources and Router association resources.

Methods
~~~~~~~

BGPVPN Resources
^^^^^^^^^^^^^^^^

.. csv-table:: API methods for BGPVPN resources
 :header: Method Name,Description,Input parameter(s),Output

    "list_bgpvpns()", "Get the list of defined BGPVPN resources for the current tenant. An optional list of BGPVPN parameters can be used as filter.", "1. Use **kwargs as filter, e.g. list_bgpvpn(param1=val1, param2=val2,...) (Optional)", "Dictionary of BGPVPN attributes"
    "create_bgpvpn()", "Create a BGPVPN resource for the current tenant. Extra information about the BGPVPN resource can be provided as input.", "1. Dictionary of BGPVPN attributes (Optional)", "Dictionary of BGPVPN attributes"
    "show_bgpvpn()", "Get all information for a given BGPVPN.", "1. UUID of the said BGPVPN", "Dictionary of BGPVPN attributes related to the BGPVPN provided as input"
	"update_bgpvpn()", "Update the BGPVPN resource with the parameters provided as input.", "1. UUID of the said BGPVPN
 2. Dictionary of BGPVPN attributes to be updated", "Dictionary of  BGPVPN attributes"
	"delete_bgpvpn()", "Delete a given BGPVPN resource of which the UUID is provided as input.", "1. UUID of the said BGPVPN", "Boolean"


Network Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table:: API methods for Network association resources
 :header: Method Name,Description,Input parameter(s),Output

	"list_network_associations()", "Get the list of defined NETWORK ASSOCIATION resources for a given BGPVPN. An optional list of NETWORK ASSOCIATION parameters can be used as filter.", "1. UUID of the BGPVPN
 2. Use **kwargs as filter, e.g. list_network_associations( BGPVPN UUID, param1=val1, param2=val2,...) (Optional)", "List of dictionaries of NETWORK ASSOCIATION attributes, one of each related to a given BGPVPN"
	"create_network_association()", "Create a NETWORK ASSOCIATION resource for a given BGPVPN.
 Network UUID must be defined, provided in a NETWORK ASSOCIATION resource as input parameter.", "1. UUID of the said BGPVPN
 2. Dictionary of NETWORK ASSOCIATION parameters", "Dictionary of NETWORK ASSOCIATION attributes"
	"show_network_association()", "Get all parameters for a given NETWORK ASSOCIATION.", "1. UUID of the NETWORK ASSOCIATION resource
 2. UUID of the BGPVPN resource", "Dictionary of NETWORK ASSOCIATION parameters"
	"update_network_association()", "Update the parameters of the NETWORK ASSOCIATION resource provided as input.", "1. UUID of the NETWORK ASSOCIATION resource
 2. UUID of the BGPVPN resource
 3.  Dictionary of NETWORK ASSOCIATION parameters", "Dictionary of NETWORK ASSOCIATION parameters"
	"delete_network_association()", "Delete a given NETWORK ASSOCIATION resource of which the UUID is provided as input.", "1. UUID of the NETWORK ASSOCIATION resource
 2. UUID of the BGPVPN resource", "Boolean"


Router Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table:: API methods for Router associations
 :header: Method Name,Description,Input parameter(s),Output

	"list_router_associations()", "Get the list of defined ROUTER ASSOCIATION resources for a given BGPVPN. An optional list of ROUTER ASSOCIATION parameters can be used as filter", "1. UUID of the BGPVPN
 2. Use **kwargs as filter, e.g. list_router_associations( BGPVPN UUID, param1=val1, param2=val2,...) (Optional)", "List of dictionaries of ROUTER ASSOCIATION attributes, one of each related to a given BGPVPN"
	"create_router_association()", "Create a ROUTER ASSOCIATION resource for a given BGPVPN UUID.
 Router UUID must be defined, provided in a ROUTER ASSOCIATION resource as input parameter.", "1. UUID of the said BGPVPN
 2. Dictionary of ROUTER ASSOCIATION parameters (Optional)", "Dictionary of ROUTER ASSOCIATION parameters"
	"show_router_association()", "Get all parameters for a given ROUTER ASSOCIATION.", "1. UUID of the ROUTER ASSOCIATION resource
 2. UUID of the BGPVPN resource", "Dictionary of ROUTER ASSOCIATION parameters"
	"update_router_association()", "Update the parameters of the ROUTER ASSOCIATION resource provided as input.", "1. UUID of the ROUTER ASSOCIATION resource
 2. UUID of the BGPVPN resource
 3. Dictionary of ROUTER ASSOCIATION parameters", "Dictionary of ROUTER ASSOCIATION parameters"
	"delete_router_association()", "Delete a given ROUTER ASSOCIATION resource.", "1. UUID of the ROUTER ASSOCIATION resource
 2. UUID of the BGPVPN resource", "Boolean"


Examples
~~~~~~~~

BGPVPN + Network Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 .. literalinclude:: ./samples/bgpvpn-sample01.py


