# Copyright 2017 <PUT YOUR NAME/COMPANY HERE>
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

"""Add tables for port associations

Revision ID: 9a6664f3b8d4
Revises: 0ab4049986b8
Create Date: 2017-06-26 17:34:14.411603

"""

# revision identifiers, used by Alembic.
revision = '9a6664f3b8d4'
down_revision = '0ab4049986b8'


def upgrade():
    op.create_table(
        'bgpvpn_port_associations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Column('project_id', sa.String(length=255),
                  index=True, nullable=False),
        sa.Column('bgpvpn_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['bgpvpn_id'], ['bgpvpns.id'],
                                ondelete='CASCADE'),
        sa.Column('port_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['port_id'], ['ports.id'],
                                ondelete='CASCADE'),
        sa.Column('advertise_fixed_ips', sa.Boolean(),
                  server_default=sa.sql.true(), nullable=False),
        sa.UniqueConstraint('bgpvpn_id', 'port_id')
    )

    op.create_table(
        'bgpvpn_port_association_routes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Column('port_association_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['port_association_id'],
                                ['bgpvpn_port_associations.id'],
                                ondelete='CASCADE'),
        sa.Column('type', sa.Enum("prefix", "bgpvpn",
                                  name="bgpvpn_port_association_route_type"),
                  nullable=False),
        sa.Column('local_pref', sa.BigInteger(),
                  autoincrement=False, nullable=True),
        # an IPv6 prefix can be up to 49 chars (IPv4-mapped IPv6 string
        # representation: up to 45 chars, plus 4 chars for "/128" which is the
        # highest/longest possible mask)
        sa.Column('prefix', sa.String(49), nullable=True),
        sa.Column('bgpvpn_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['bgpvpn_id'],
                                ['bgpvpns.id'],
                                ondelete='CASCADE')
        # NOTE(tmorin): it would be nice to add some CheckConstraint so that
        # prefix and bgpvpn_id are enforced as NULL unless relevant for the
        # type, and non-NULL when relevant for the type
    )
