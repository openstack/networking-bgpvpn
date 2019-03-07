To generate the sample networking-bgpvpn configuration files and
the sample policy file, run the following commands respectively
from the top level of the networking-bgpvpn directory:

  tox -e genconfig
  tox -e genpolicy

If a 'tox' environment is unavailable, then you can run
the following commands respectively
instead to generate the configuration files:

  oslo-config-generator --config-file etc/oslo-config-generator/networking-bgpvpn.conf
  oslopolicy-sample-generator --config-file=etc/oslo-policy-generator/policy.conf
