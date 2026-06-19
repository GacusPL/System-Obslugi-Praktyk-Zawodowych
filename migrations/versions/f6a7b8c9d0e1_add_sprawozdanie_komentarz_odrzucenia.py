"""Add komentarz_odrzucenia to sprawozdanie (rejection comment for UOPZ)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sprawozdanie', schema=None) as batch_op:
        batch_op.add_column(sa.Column('komentarz_odrzucenia', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('sprawozdanie', schema=None) as batch_op:
        batch_op.drop_column('komentarz_odrzucenia')
