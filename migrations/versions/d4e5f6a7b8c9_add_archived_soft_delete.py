"""Add archived (soft-delete) flag to praktyka, zaklad_pracy, uzytkownik

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-18 01:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    for table in ('praktyka', 'zaklad_pracy', 'uzytkownik'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    for table in ('uzytkownik', 'zaklad_pracy', 'praktyka'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('archived')
