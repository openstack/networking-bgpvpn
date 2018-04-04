#!/usr/bin/env bash

set -xe

NETWORKING_BGPVPN_DIR="$BASE/new/networking-bgpvpn"
LOGS=/opt/stack/logs
GATE_STACK_USER=stack
SCRIPTS_DIR="/usr/os-testr-env/bin/"

typetest=${1:-"unknown"}

function generate_testr_results {
    sudo -H -u $GATE_STACK_USER chmod o+rw .
    sudo -H -u $GATE_STACK_USER chmod o+rw -R .stestr
    if [ -f ".stestr/0" ] ; then
        .tox/$venv/bin/subunit-1to2 < .stestr/0 > ./stestr.subunit
        $SCRIPTS_DIR/subunit2html ./stestr.subunit testr_results.html
        gzip -9 ./stestr.subunit
        gzip -9 ./testr_results.html
        sudo mv *.gz $LOGS
    fi
}

case "$typetest" in
dsvm-bagpipe-functional*|dsvm-functional*)
    cd $NETWORKING_BGPVPN_DIR
    sudo chown -R $GATE_STACK_USER:$GATE_STACK_USER .
    # Run tests
    venv=${typetest/dsvm-bagpipe/dsvm}
    echo "Running networking-bgpvpn $venv test suite"
    set +e
    sudo -H -u $GATE_STACK_USER tox -e ${venv}
    testr_exit_code=$?
    set -e

    # move and zip tox logs into log directory
    sudo mv $NETWORKING_BGPVPN_DIR/.tox/$venv/log /opt/stack/logs/tox
    sudo -H -u $GATE_STACK_USER chmod o+rw -R /opt/stack/logs/tox/
    gzip -9 /opt/stack/logs/tox/*.log

    # Collect and parse results
    generate_testr_results
    exit $testr_exit_code
    ;;
*)
    ;;
esac

