#!/bin/sh

# Many of neutron's repos suffer from the problem of depending on neutron,
# but it not existing on pypi.

# This wrapper for tox's package installer will use the existing package
# if it exists, else use zuul-cloner if that program exists, else grab it
# from neutron master via a hard-coded URL. That last case should only
# happen with devs running unit tests locally.

# From the tox.ini config page:
# install_command=ARGV
# default:
# pip install {opts} {packages}

ZUUL_CLONER=/usr/zuul-env/bin/zuul-cloner
BRANCH_NAME=master

install_project() {
    local project=$1

    set +e
    project_installed=$(echo "import $project" | python 2>/dev/null ; echo $?)
    set -e

    if [ $project_installed -eq 0 ]; then
        echo "ALREADY INSTALLED" > /tmp/tox_install.txt
        echo "$project already installed; using existing package"
    elif [ -x "$ZUUL_CLONER" ]; then
        export ZUUL_BRANCH=${ZUUL_BRANCH-$BRANCH}
        echo "ZUUL CLONER" > /tmp/tox_install.txt
        cwd=$(/bin/pwd)
        cd /tmp
        $ZUUL_CLONER --cache-dir \
            /opt/git \
            --branch $BRANCH_NAME \
            git://git.openstack.org \
            openstack/$project
        cd openstack/$project
        $install_cmd -e .
        cd "$cwd"
    else
        echo "PIP HARDCODE" > /tmp/tox_install.txt
        if [ -z "$PIP_LOCATION" ]; then
            PIP_LOCATION="git+https://git.openstack.org/openstack/$project@$BRANCH_NAME#egg=$project"
        fi
        $install_cmd -U -e ${PIP_LOCATION}
    fi
}

set -e

install_cmd="pip install -c$1"
shift

install_project neutron
install_project horizon

$install_cmd -U $*
exit $?
