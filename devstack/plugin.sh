#!/bin/bash

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

if [[ "$1" == "source" ]]; then
	# no-op
	:
elif [[ "$1" == "stack" && "$2" == "install" ]]; then
	setup_develop $NETWORKING_BGPVPN_DIR
 	mkdir -p $NEUTRON_CONF_DIR/policy.d && cp $NETWORKING_BGPVPN_DIR/etc/neutron/policy.d/bgpvpn.conf $NEUTRON_CONF_DIR/policy.d
	mkdir -p $(dirname $NETWORKING_BGPVPN_CONF) && cp $NETWORKING_BGPVPN_DIR/etc/neutron/networking_bgpvpn.conf $NETWORKING_BGPVPN_CONF
elif [[ "$1" == "stack" && "$2" == "pre-install" ]]; then
	_neutron_service_plugin_class_add $BGPVPN_PLUGIN_CLASS
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
	#no-op
	:
fi
if [[ "$1" == "unstack" ]]; then
	#no-op
	:
fi
if [[ "$1" == "clean" ]]; then
	#no-op
	:
fi

set +x
$xtrace

