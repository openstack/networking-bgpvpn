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

"""Add 'extra-routes' to router association table

Revision ID: 4610803bdf0d
Revises: 9a6664f3b8d4
Create Date: 2017-06-26 17:39:11.086696

"""

# revision identifiers, used by Alembic.
revision = '4610803bdf0d'
down_revision = '39411aacf9b8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('bgpvpn_router_associations',
                  sa.Column('advertise_extra_routes',
                            sa.Boolean(), nullable=False,
                            server_default=sa.true()))
