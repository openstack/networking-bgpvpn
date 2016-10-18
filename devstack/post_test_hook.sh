#!/usr/bin/env bash

set -xe

NETWORKING_BGPVPN_DIR="$BASE/new/networking-bgpvpn"
LOGS=/opt/stack/logs
GATE_STACK_USER=stack

typetest=${1:-"unknown"}

function generate_testr_results {
    sudo -H -u $GATE_STACK_USER chmod o+rw .
    sudo -H -u $GATE_STACK_USER chmod o+rw -R .testrepository
    if [ -f ".testrepository/0" ]; then
        .tox/$venv/bin/subunit-1to2 < .testrepository/0  > ./testrepository.subunit
        .tox/$venv/bin/subunit2html ./testrepository.subunit ./testr_results.html
        gzip ./testrepository.subunit   
        gzip ./testr_results.html
        sudo mv ./testrepository.subunit.gz testr_results.html.gz $LOGS
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
    # Collect and parse results
    generate_testr_results
    exit $testr_exit_code
    ;;
*)
    ;;
esac

