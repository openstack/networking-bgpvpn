# Copyright 2015 Alcatel-Lucent
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

"""Add router association table

Revision ID: 3600132c6147
Revises: 17d9fd4fddee
Create Date: 2015-11-16 15:48:31.343859

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3600132c6147'
down_revision = '17d9fd4fddee'


def upgrade():
    op.create_table(
        'bgpvpn_router_associations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('bgpvpn_id', sa.String(36), nullable=False),
        sa.Column('router_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['router_id'], ['routers.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bgpvpn_id'], ['bgpvpns.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bgpvpn_id', 'router_id')
    )
