"""Add program_praktyki_pozycja table (Zał. 2a program section)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-18 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'program_praktyki_pozycja',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('harmonogram_id', sa.Integer(), nullable=False),
        sa.Column('efekt_id', sa.Integer(), nullable=False),
        sa.Column('opis_realizacji', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['harmonogram_id'], ['harmonogram.id'], ),
        sa.ForeignKeyConstraint(['efekt_id'], ['efekt_uczenia.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('harmonogram_id', 'efekt_id', name='uq_program_harmonogram_efekt'),
    )


def downgrade():
    op.drop_table('program_praktyki_pozycja')
