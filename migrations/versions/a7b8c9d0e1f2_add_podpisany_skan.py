"""Add podpisany_skan table (signed scan slots P1-P6 for documentation stage)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'podpisany_skan',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('praktyka_id', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(length=10), nullable=False),
        sa.Column('nazwa_pliku', sa.String(length=255), nullable=False),
        sa.Column('sciezka_pliku', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Submitted'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("slot IN ('p1', 'p2', 'p3', 'p4', 'p5', 'p6')", name='check_podpisany_skan_slot'),
        sa.ForeignKeyConstraint(['praktyka_id'], ['praktyka.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('praktyka_id', 'slot', name='uq_podpisany_skan_praktyka_slot'),
    )


def downgrade():
    op.drop_table('podpisany_skan')
