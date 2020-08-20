# Copyright 2018 <PUT YOUR NAME/COMPANY HERE>
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

""" Add local_pref to bgpvpns table

Revision ID: 666c706fea3b
Revises: 39411aacf9b8
Create Date: 2018-01-18 15:40:05.723129

"""

# revision identifiers, used by Alembic.
revision = '666c706fea3b'
down_revision = '4610803bdf0d'


def upgrade():
    op.add_column('bgpvpns', sa.Column('local_pref',
                                       sa.BigInteger,
                                       nullable=True))
