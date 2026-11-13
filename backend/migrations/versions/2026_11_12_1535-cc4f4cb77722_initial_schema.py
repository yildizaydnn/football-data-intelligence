"""initial schema

Revision ID: cc4f4cb77722
Revises: 
Create Date: 2026-11-12 15:35:14.183973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cc4f4cb77722'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('api_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('requests_used', sa.Integer(), nullable=False),
    sa.Column('daily_limit', sa.Integer(), nullable=False),
    sa.Column('remaining', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_api_usage')),
    sa.UniqueConstraint('date', name=op.f('uq_api_usage_date'))
    )
    op.create_table('leagues',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('logo_url', sa.String(length=255), nullable=True),
    sa.Column('external_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leagues'))
    )
    op.create_index(op.f('ix_leagues_external_id'), 'leagues', ['external_id'], unique=True)
    op.create_table('sync_runs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trigger', sa.Enum('manual', 'scheduled', 'initial', name='synctrigger', native_enum=False, length=20), nullable=False),
    sa.Column('status', sa.Enum('running', 'success', 'partial', 'failed', name='syncstatus', native_enum=False, length=20), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('requests_made', sa.Integer(), nullable=False),
    sa.Column('inserted', sa.Integer(), nullable=False),
    sa.Column('updated', sa.Integer(), nullable=False),
    sa.Column('skipped', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_runs'))
    )
    op.create_index(op.f('ix_sync_runs_status'), 'sync_runs', ['status'], unique=False)
    op.create_table('teams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=10), nullable=True),
    sa.Column('logo_url', sa.String(length=255), nullable=True),
    sa.Column('venue_name', sa.String(length=150), nullable=True),
    sa.Column('external_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_teams'))
    )
    op.create_index(op.f('ix_teams_external_id'), 'teams', ['external_id'], unique=True)
    op.create_table('seasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('league_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('is_current', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], name=op.f('fk_seasons_league_id_leagues'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_seasons')),
    sa.UniqueConstraint('league_id', 'year', name='uq_seasons_league_id_year')
    )
    op.create_table('fixtures',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.Column('home_team_id', sa.Integer(), nullable=False),
    sa.Column('away_team_id', sa.Integer(), nullable=False),
    sa.Column('kickoff_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('scheduled', 'live', 'finished', 'postponed', 'cancelled', name='matchstatus', native_enum=False, length=20), nullable=False),
    sa.Column('status_raw', sa.String(length=10), nullable=False),
    sa.Column('home_goals', sa.Integer(), nullable=True),
    sa.Column('away_goals', sa.Integer(), nullable=True),
    sa.Column('round', sa.String(length=50), nullable=True),
    sa.Column('external_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], name=op.f('fk_fixtures_away_team_id_teams')),
    sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], name=op.f('fk_fixtures_home_team_id_teams')),
    sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], name=op.f('fk_fixtures_season_id_seasons'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fixtures'))
    )
    op.create_index(op.f('ix_fixtures_away_team_id'), 'fixtures', ['away_team_id'], unique=False)
    op.create_index(op.f('ix_fixtures_external_id'), 'fixtures', ['external_id'], unique=True)
    op.create_index(op.f('ix_fixtures_home_team_id'), 'fixtures', ['home_team_id'], unique=False)
    op.create_index(op.f('ix_fixtures_kickoff_at'), 'fixtures', ['kickoff_at'], unique=False)
    op.create_index(op.f('ix_fixtures_season_id'), 'fixtures', ['season_id'], unique=False)
    op.create_index(op.f('ix_fixtures_status'), 'fixtures', ['status'], unique=False)
    op.create_table('fixture_changes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fixture_id', sa.Integer(), nullable=False),
    sa.Column('sync_run_id', sa.Integer(), nullable=True),
    sa.Column('field', sa.String(length=30), nullable=False),
    sa.Column('old_value', sa.String(length=50), nullable=True),
    sa.Column('new_value', sa.String(length=50), nullable=True),
    sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['fixture_id'], ['fixtures.id'], name=op.f('fk_fixture_changes_fixture_id_fixtures'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sync_run_id'], ['sync_runs.id'], name=op.f('fk_fixture_changes_sync_run_id_sync_runs'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fixture_changes'))
    )
    op.create_index(op.f('ix_fixture_changes_fixture_id'), 'fixture_changes', ['fixture_id'], unique=False)
    op.create_index(op.f('ix_fixture_changes_sync_run_id'), 'fixture_changes', ['sync_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fixture_changes_sync_run_id'), table_name='fixture_changes')
    op.drop_index(op.f('ix_fixture_changes_fixture_id'), table_name='fixture_changes')
    op.drop_table('fixture_changes')
    op.drop_index(op.f('ix_fixtures_status'), table_name='fixtures')
    op.drop_index(op.f('ix_fixtures_season_id'), table_name='fixtures')
    op.drop_index(op.f('ix_fixtures_kickoff_at'), table_name='fixtures')
    op.drop_index(op.f('ix_fixtures_home_team_id'), table_name='fixtures')
    op.drop_index(op.f('ix_fixtures_external_id'), table_name='fixtures')
    op.drop_index(op.f('ix_fixtures_away_team_id'), table_name='fixtures')
    op.drop_table('fixtures')
    op.drop_table('seasons')
    op.drop_index(op.f('ix_teams_external_id'), table_name='teams')
    op.drop_table('teams')
    op.drop_index(op.f('ix_sync_runs_status'), table_name='sync_runs')
    op.drop_table('sync_runs')
    op.drop_index(op.f('ix_leagues_external_id'), table_name='leagues')
    op.drop_table('leagues')
    op.drop_table('api_usage')
