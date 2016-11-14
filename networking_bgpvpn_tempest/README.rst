===============================================
Tempest Integration of networking_bgpvpn
===============================================

This directory contains Tempest tests to cover the networking_bgpvpn project.

If you are running the tests locally you should set the env variables:
# TEMPEST_CONFIG_DIR=/opt/stack/tempest/etc
# OS_TEST_PATH=/opt/stack/networking_bgpvpn_tempest/tests

If the tests take too long to execute so that a test timeout failure happens,
that timeout value may need to be increased. This is done by setting the
environment variable OS_TEST_TIMEOUT to a sufficiently large value.

Examples - three ways to run Tempest scenario tests:
====================================================

Using tempest client:
---------------------
TEMPEST_CONFIG_DIR=/opt/stack/tempest/etc OS_TEST_PATH=./networking_bgpvpn_tempest/tests/ tempest run --regex scenario

Using ostestr:
--------------
TEMPEST_CONFIG_DIR=/opt/stack/tempest/etc OS_TEST_PATH=./networking_bgpvpn_tempest/tests/ ostestr --regex scenario

Using tox:
----------
TEMPEST_CONFIG_DIR=/opt/stack/tempest/etc tox -e scenario
