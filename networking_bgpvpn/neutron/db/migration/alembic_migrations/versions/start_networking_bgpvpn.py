# Copyright 2014 OpenStack Foundation
#
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
#

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'start_networking_bgpvpn'
down_revision = None

vpn_types = sa.Enum("l2", "l3", name="vpn_types")


def upgrade(active_plugins=None, options=None):
    op.create_table(
        u'bgpvpn_connections',
        sa.Column(u'name', sa.String(255), nullable=True),
        sa.Column(u'id', sa.String(length=36), nullable=False),
        sa.Column(u'tenant_id', sa.String(length=255), nullable=True),
        sa.Column(u'type', vpn_types, nullable=False),
        sa.Column(u'route_targets', sa.String(255), nullable=False),
        sa.Column(u'import_targets', sa.String(255), nullable=True),
        sa.Column(u'export_targets', sa.String(255), nullable=True),
        sa.Column(u'auto_aggregate', sa.Boolean(), nullable=False),
        sa.Column(u'network_id', sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(['network_id'], [u'networks.id'], ),
        sa.PrimaryKeyConstraint(u'id'),
        mysql_default_charset=u'utf8',
        mysql_engine='InnoDB'
    )


def downgrade(active_plugins=None, options=None):
    op.drop_table(u'bgpvpn_connections')
    vpn_types.drop(op.get_bind(), checkfirst=False)
