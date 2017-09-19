#
# Copyright 2017 Ericsson India Global Services Pvt Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

"""add vni to bgpvpn table

Revision ID: 39411aacf9b8
Revises: 9a6664f3b8d4
Create Date: 2017-09-19 17:37:11.359338

"""

# revision identifiers, used by Alembic.
revision = '39411aacf9b8'
down_revision = '9a6664f3b8d4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('bgpvpns', sa.Column('vni', sa.Integer))
