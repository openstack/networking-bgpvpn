#!/bin/sh

set -xe

testtype=${1:-"unknown"}
GATE_DEST=$BASE/new

sudo modprobe bridge

case "$testtype" in
dsvm-bagpipe-functional*|dsvm-functional*)
    # Used by configure_for_func_testing
    DEVSTACK_PATH=$GATE_DEST/devstack
    IS_GATE=True
    source "$GATE_DEST"/neutron/tools/configure_for_func_testing.sh
    configure_host_for_func_testing
    sudo chown -R stack:stack /opt/stack
    ;;
*)
    $GATE_DEST/devstack-gate/devstack-vm-gate.sh
esac

