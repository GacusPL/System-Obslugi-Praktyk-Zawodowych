"""Add Rejected status to karta_praktyki and komentarz_odrzucenia to documents

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

OLD_KARTA_STATUS = "status IN ('Draft', 'Under_Review', 'Approved', 'Closed')"
NEW_KARTA_STATUS = "status IN ('Draft', 'Under_Review', 'Approved', 'Rejected', 'Closed')"


def upgrade():
    with op.batch_alter_table('harmonogram', schema=None) as batch_op:
        batch_op.add_column(sa.Column('komentarz_odrzucenia', sa.Text(), nullable=True))

    with op.batch_alter_table('potwierdzenie_efektow', schema=None) as batch_op:
        batch_op.add_column(sa.Column('komentarz_odrzucenia', sa.Text(), nullable=True))

    with op.batch_alter_table('karta_praktyki', schema=None) as batch_op:
        batch_op.add_column(sa.Column('komentarz_odrzucenia', sa.Text(), nullable=True))
        batch_op.drop_constraint('check_karta_status', type_='check')
        batch_op.create_check_constraint('check_karta_status', NEW_KARTA_STATUS)


def downgrade():
    with op.batch_alter_table('karta_praktyki', schema=None) as batch_op:
        batch_op.drop_constraint('check_karta_status', type_='check')
        batch_op.create_check_constraint('check_karta_status', OLD_KARTA_STATUS)
        batch_op.drop_column('komentarz_odrzucenia')

    with op.batch_alter_table('potwierdzenie_efektow', schema=None) as batch_op:
        batch_op.drop_column('komentarz_odrzucenia')

    with op.batch_alter_table('harmonogram', schema=None) as batch_op:
        batch_op.drop_column('komentarz_odrzucenia')
