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

"""Add standard FK and constraints, and defs for existing objects

Revision ID: 9d7f1ae5fa56
Revises: 23ce05e0a19f
Create Date: 2018-04-19 12:44:54.352253

"""

# revision identifiers, used by Alembic.
revision = '9d7f1ae5fa56'
down_revision = '23ce05e0a19f'
depends_on = ('7a9482036ecd',)

from alembic import op
import sqlalchemy as sa

# adapted from b12a3ef66e62_add_standardattr_to_qos_policies.py

standardattrs = sa.Table(
    'standardattributes', sa.MetaData(),
    sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column('resource_type', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True))


def upgrade():
    for table in ('bgpvpns', 'bgpvpn_network_associations',
                  'bgpvpn_router_associations', 'bgpvpn_port_associations'):
        upgrade_table(table)


def upgrade_table(table):
    table_model = sa.Table(
        table, sa.MetaData(),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('standard_attr_id', sa.BigInteger(), nullable=True))

    generate_records_for_existing(table, table_model)
    # add the constraint now that everything is populated on that table
    op.alter_column(table, 'standard_attr_id', nullable=False,
                    existing_type=sa.BigInteger(), existing_nullable=True,
                    existing_server_default=False)
    op.create_unique_constraint(
        constraint_name='uniq_%s0standard_attr_id' % table,
        table_name=table, columns=['standard_attr_id'])
    op.create_foreign_key(
        constraint_name=None, source_table=table,
        referent_table='standardattributes',
        local_cols=['standard_attr_id'], remote_cols=['id'],
        ondelete='CASCADE')


def generate_records_for_existing(table, table_model):
    session = sa.orm.Session(bind=op.get_bind())
    values = []
    with session.begin(subtransactions=True):
        for row in session.query(table_model):
            # NOTE(kevinbenton): without this disabled, pylint complains
            # about a missing 'dml' argument.
            # pylint: disable=no-value-for-parameter
            res = session.execute(
                standardattrs.insert().values(resource_type=table)
            )
            session.execute(
                table_model.update().values(
                    standard_attr_id=res.inserted_primary_key[0]).where(
                        table_model.c.id == row[0])
            )
    # this commit is necessary to allow further operations
    session.commit()
    return values
