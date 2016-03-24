#!/bin/sh

GATE_DEST=$BASE/new
DEVSTACK_PATH=$GATE_DEST/devstack
NEUTRON_PATH=$GATE_DEST/neutron

if [[ "$COMPILE_OVS" == "True" ]]; then
	source $DEVSTACK_PATH/functions
	source $NEUTRON_PATH/devstack/lib/ovs

	# The OVS_BRANCH variable is used by git checkout.
	OVS_BRANCH=branch-2.4
	echo "Compiling OVS $OVS_BRANCH..."
	for package in openvswitch openvswitch-switch openvswitch-common; do
	    if is_package_installed $package; then
		uninstall_package $package
	    fi
	done
	compile_ovs True /usr
	echo "Starting new OVS..."
	start_new_ovs
fi

sudo modprobe bridge

$GATE_DEST/devstack-gate/devstack-vm-gate.sh

