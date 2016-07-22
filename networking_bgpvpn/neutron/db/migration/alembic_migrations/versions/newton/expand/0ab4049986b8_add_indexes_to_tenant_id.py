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

"""add indexes to tenant_id

Revision ID: 0ab4049986b8
Create Date: 2016-07-22 14:19:04.888614

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '0ab4049986b8'
down_revision = '3600132c6147'


def upgrade():
    for table in [
        'bgpvpns',
        'bgpvpn_network_associations',
        'bgpvpn_router_associations',
    ]:
        op.create_index(op.f('ix_%s_tenant_id' % table),
                        table, ['tenant_id'], unique=False)
