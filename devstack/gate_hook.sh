#!/bin/sh

GATE_DEST=$BASE/new

sudo modprobe bridge

$GATE_DEST/devstack-gate/devstack-vm-gate.sh

