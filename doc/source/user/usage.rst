========
Usage
========

Use from OpenStack CLI
------------------------

Example commands to use by the admin to create a BGPVPN resource:

.. code-block:: console

	openstack bgpvpn create --route-target 64512:1 --project b954279e1e064dc9b8264474cb3e6bd2
	openstack bgpvpn list
	openstack bgpvpn set <bgpvpn-uuid> --name myBGPVPN

Example commands to use by the tenant owning the BGPVPN to associate a Network to it:

.. code-block:: console

	openstack bgpvpn network association create myBGPVPN <net-uuid>
	# returns <net-assoc-uuid>
	openstack bgpvpn network association list myBGPVPN
	openstack bgpvpn network association show <net-assoc-uuid> myBGPVPN

	openstack bgpvpn network association delete <net-assoc-uuid> myBGPVPN

There are more details in the `OpenStack Client (OSC) documentation
for BGPVPN <https://docs.openstack.org/python-neutronclient/latest/cli/osc/v2/networking-bgpvpn.html>`_.

Use from Horizon
----------------

See :doc:`horizon`.

Use from Heat
-------------

See :doc:`heat`.

Use from Python
---------------

The python ``neutroclient`` library includes support for the BGPVPN API
extensions since Ocata release.

.. note::

   For older releases, the dynamic extension of ``neutronclient`` provided
   in ``networking-bgpvpn`` is available.  In that case, the methods to
   list, get, create, delete and update network associations and router
   associations are different from what is documented here:

   * different name: ``list_network_associations`` instead of
     `list_bgpvpn_network_assocs``, and same change for all the methods

   * order of parameters: BGPVPN UUID as first parameter, association UUID as
     second parameter

   These old methods are deprecated.

Methods
~~~~~~~

BGPVPN Resources
^^^^^^^^^^^^^^^^

.. csv-table:: API methods for BGPVPN resources
 :header: Method Name,Description,Input parameter(s),Output

    "list_bgpvpns()", "Get the list of defined BGPVPN resources for the current tenant. An optional list of BGPVPN parameters can be used as filter.", "1. Use \**kwargs as filter, e.g. list_bgpvpn(param1=val1, param2=val2,...) (Optional)", "Dictionary of BGPVPN attributes"
    "create_bgpvpn()", "Create a BGPVPN resource for the current tenant. Extra information about the BGPVPN resource can be provided as input.", "1. Dictionary of BGPVPN attributes (Optional)", "Dictionary of BGPVPN attributes"
    "show_bgpvpn()", "Get all information for a given BGPVPN.", "1. UUID of the said BGPVPN", "Dictionary of BGPVPN attributes related to the BGPVPN provided as input"
	"update_bgpvpn()", "Update the BGPVPN resource with the parameters provided as input.", "1. UUID of the said BGPVPN
 2. Dictionary of BGPVPN attributes to be updated", "Dictionary of  BGPVPN attributes"
	"delete_bgpvpn()", "Delete a given BGPVPN resource of which the UUID is provided as input.", "1. UUID of the said BGPVPN", "Boolean"

Network Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table:: API methods for Network association resources
 :header: Method Name,Description,Input parameter(s),Output

	"list_bgpvpn_network_assocs()", "Get the list of defined NETWORK ASSOCIATION resources for a given BGPVPN. An optional list of NETWORK ASSOCIATION parameters can be used as filter.", "1. UUID of the BGPVPN
 2. Use \**kwargs as filter, e.g. list_bgpvpn_network_assocs( BGPVPN UUID, param1=val1, param2=val2,...) (Optional)", "List of dictionaries of NETWORK ASSOCIATION attributes, one of each related to a given BGPVPN"
	"create_bgpvpn_network_assoc()", "Create a NETWORK ASSOCIATION resource for a given BGPVPN.
 Network UUID must be defined, provided in a NETWORK ASSOCIATION resource as input parameter.", "1. UUID of the said BGPVPN
 2. Dictionary of NETWORK ASSOCIATION parameters", "Dictionary of NETWORK ASSOCIATION attributes"
	"show_bgpvpn_network_assoc()", "Get all parameters for a given NETWORK ASSOCIATION.", "1. UUID of the BGPVPN resource
 2. UUID of the NETWORK ASSOCIATION resource", "Dictionary of NETWORK ASSOCIATION parameters"
	"update_bgpvpn_network_assoc()", "Update the parameters of the NETWORK ASSOCIATION resource provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the NETWORK ASSOCIATION resource, 3.  Dictionary of NETWORK ASSOCIATION parameters", "Dictionary of NETWORK ASSOCIATION parameters"
	"delete_bgpvpn_network_assoc()", "Delete a given NETWORK ASSOCIATION resource of which the UUID is provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the NETWORK ASSOCIATION resource", "Boolean"

Router Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table:: API methods for Router association resources
 :header: Method Name,Description,Input parameter(s),Output

	"list_bgpvpn_router_assocs()", "Get the list of defined ROUTER ASSOCIATION resources for a given BGPVPN. An optional list of ROUTER ASSOCIATION parameters can be used as filter.", "1. UUID of the BGPVPN
 2. Use \**kwargs as filter, e.g. list_bgpvpn_router_assocs( BGPVPN UUID, param1=val1, param2=val2,...) (Optional)", "List of dictionaries of ROUTER ASSOCIATION attributes, one of each related to a given BGPVPN"
	"create_bgpvpn_router_assoc()", "Create a ROUTER ASSOCIATION resource for a given BGPVPN.
 Router UUID must be defined, provided in a ROUTER ASSOCIATION resource as input parameter.", "1. UUID of the said BGPVPN
 2. Dictionary of ROUTER ASSOCIATION parameters", "Dictionary of ROUTER ASSOCIATION attributes"
	"show_bgpvpn_router_assoc()", "Get all parameters for a given ROUTER ASSOCIATION.", "1. UUID of the BGPVPN resource
 2. UUID of the ROUTER ASSOCIATION resource", "Dictionary of ROUTER ASSOCIATION parameters"
	"update_bgpvpn_router_assoc()", "Update the parameters of the ROUTER ASSOCIATION resource provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the ROUTER ASSOCIATION resource, 3.  Dictionary of ROUTER ASSOCIATION parameters", "Dictionary of ROUTER ASSOCIATION parameters"
	"delete_bgpvpn_router_assoc()", "Delete a given ROUTER ASSOCIATION resource of which the UUID is provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the ROUTER ASSOCIATION resource", "Boolean"

Port Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table:: API methods for Port association resources
 :header: Method Name,Description,Input parameter(s),Output

	"list_bgpvpn_port_assocs()", "Get the list of defined PORT ASSOCIATION resources for a given BGPVPN. An optional list of PORT ASSOCIATION parameters can be used as filter.", "1. UUID of the BGPVPN
 2. Use \**kwargs as filter, e.g. list_bgpvpn_port_assocs( BGPVPN UUID, param1=val1, param2=val2,...) (Optional)", "List of dictionaries of PORT ASSOCIATION attributes, one of each related to a given BGPVPN"
	"create_bgpvpn_port_assoc()", "Create a PORT ASSOCIATION resource for a given BGPVPN.
 Port UUID must be defined, provided in a PORT ASSOCIATION resource as input parameter.", "1. UUID of the said BGPVPN
 2. Dictionary of PORT ASSOCIATION parameters", "Dictionary of PORT ASSOCIATION attributes"
	"show_bgpvpn_port_assoc()", "Get all parameters for a given PORT ASSOCIATION.", "1. UUID of the BGPVPN resource
 2. UUID of the PORT ASSOCIATION resource", "Dictionary of PORT ASSOCIATION parameters"
	"update_bgpvpn_port_assoc()", "Update the parameters of the PORT ASSOCIATION resource provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the PORT ASSOCIATION resource, 3.  Dictionary of PORT ASSOCIATION parameters", "Dictionary of PORT ASSOCIATION parameters"
	"delete_bgpvpn_port_assoc()", "Delete a given PORT ASSOCIATION resource of which the UUID is provided as input.", "1. UUID of the BGPVPN resource
 2. UUID of the PORT ASSOCIATION resource", "Boolean"

Examples
~~~~~~~~

BGPVPN + Network Association Resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../samples/bgpvpn-sample01.py


