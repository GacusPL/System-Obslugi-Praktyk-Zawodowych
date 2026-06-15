"""Add 'signed_karta_sprawozdanie' to dokument typ CHECK constraint

Revision ID: a1b2c3d4e5f6
Revises: 34bce5e124df
Create Date: 2026-06-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '34bce5e124df'
branch_labels = None
depends_on = None

OLD_TYPES = "typ IN ('zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr4b', 'zal_nr5', 'zal_nr6', 'zal_nr7', 'zal_nr8')"
NEW_TYPES = "typ IN ('zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr4b', 'zal_nr5', 'zal_nr6', 'zal_nr7', 'zal_nr8', 'signed_karta_sprawozdanie')"


def upgrade():
    with op.batch_alter_table('dokument', schema=None) as batch_op:
        batch_op.drop_constraint('check_dokument_typ', type_='check')
        batch_op.create_check_constraint('check_dokument_typ', NEW_TYPES)


def downgrade():
    with op.batch_alter_table('dokument', schema=None) as batch_op:
        batch_op.drop_constraint('check_dokument_typ', type_='check')
        batch_op.create_check_constraint('check_dokument_typ', OLD_TYPES)
