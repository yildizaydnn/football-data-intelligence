"""sync run league and season

Revision ID: 440291e463bf
Revises: 711d0ecc55c8
Create Date: 2026-11-12 23:08:48.215173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '440291e463bf'
down_revision: Union[str, Sequence[str], None] = '711d0ecc55c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sync_runs', sa.Column('league_external_id', sa.Integer(), nullable=True))
    op.add_column('sync_runs', sa.Column('season', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('sync_runs', 'season')
    op.drop_column('sync_runs', 'league_external_id')
