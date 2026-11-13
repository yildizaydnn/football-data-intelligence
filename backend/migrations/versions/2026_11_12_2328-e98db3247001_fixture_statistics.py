"""fixture statistics

Revision ID: e98db3247001
Revises: 440291e463bf
Create Date: 2026-11-12 23:28:41.264696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e98db3247001'
down_revision: Union[str, Sequence[str], None] = '440291e463bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('fixture_statistics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fixture_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=40), nullable=False),
    sa.Column('value', sa.Double(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['fixture_id'], ['fixtures.id'], name=op.f('fk_fixture_statistics_fixture_id_fixtures'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_fixture_statistics_team_id_teams')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fixture_statistics')),
    sa.UniqueConstraint('fixture_id', 'team_id', 'key', name='uq_fixture_statistics_entry')
    )
    op.create_index(op.f('ix_fixture_statistics_fixture_id'), 'fixture_statistics', ['fixture_id'], unique=False)
    op.add_column('fixtures', sa.Column('statistics_fetched_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('fixtures', 'statistics_fetched_at')
    op.drop_index(op.f('ix_fixture_statistics_fixture_id'), table_name='fixture_statistics')
    op.drop_table('fixture_statistics')
