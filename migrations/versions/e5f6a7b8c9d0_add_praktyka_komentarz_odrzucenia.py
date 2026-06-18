"""Add komentarz_odrzucenia to praktyka (rejection comment for zgloszenie)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-18 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('praktyka', schema=None) as batch_op:
        batch_op.add_column(sa.Column('komentarz_odrzucenia', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('praktyka', schema=None) as batch_op:
        batch_op.drop_column('komentarz_odrzucenia')
