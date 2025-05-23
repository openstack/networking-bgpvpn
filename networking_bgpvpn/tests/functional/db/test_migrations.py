#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

from neutron.db.migration.alembic_migrations import external
from neutron.db.migration import cli as migration
from neutron.tests.functional.db import test_migrations
from neutron.tests.unit import testlib_api

from networking_bgpvpn.neutron.db import head


# Tables from other repos that we depend on but do not manage.
IGNORED_TABLES_MATCH = (
    'ml2_route_target_allocations',
    '_bagpipe_',
)

# EXTERNAL_TABLES should contain all names of tables that are not related to
# current repo.
EXTERNAL_TABLES = set(external.TABLES)
VERSION_TABLE = 'alembic_version_bgpvpn'


class TestModelsMigrationsBGPVPN(test_migrations.TestModelsMigrations,
                                 testlib_api.MySQLTestCaseMixin,
                                 testlib_api.SqlTestCaseLight):

    def db_sync(self, engine):
        cfg.CONF.set_override(
            'connection',
            engine.url.render_as_string(hide_password=False),
            group='database')
        for conf in migration.get_alembic_configs():
            self.alembic_config = conf
            self.alembic_config.neutron_config = cfg.CONF
            migration.do_alembic_command(conf, 'upgrade', 'heads')

    def get_metadata(self):
        return head.get_metadata()

    def include_object(self, object_, name, type_, reflected, compare_to):
        if (type_ == "table" and (
            name.startswith("alembic") or
            name == VERSION_TABLE or
            name in EXTERNAL_TABLES or
            any([match in name for match in IGNORED_TABLES_MATCH])
        )):
            return False
        if type_ == 'index' and reflected and name.startswith("idx_autoinc_"):
            return False
        return True
