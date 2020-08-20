# Copyright 2018 OpenStack Fundation
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

"""Add standard attributes

Revision ID: 7a9482036ecd
Revises: 666c706fea3b
Create Date: 2018-04-04 10:12:40.399032

"""

# revision identifiers, used by Alembic.
revision = '7a9482036ecd'
down_revision = '666c706fea3b'


def upgrade():
    for table in ('bgpvpns', 'bgpvpn_network_associations',
                  'bgpvpn_router_associations', 'bgpvpn_port_associations'):
        op.add_column(table, sa.Column('standard_attr_id', sa.BigInteger(),
                                       nullable=True))
