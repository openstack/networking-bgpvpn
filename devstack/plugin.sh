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
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
	if is_service_enabled q-svc; then
		bgpvpn-db-manage --config-file $NEUTRON_CONF --config-file /$Q_PLUGIN_CONF_FILE upgrade head
	fi
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

