/**
 * Backend'e giden tüm çağrılar burada. Bileşenler fetch kullanmaz:
 * endpoints.ts → feature hook (ör. useStandings) → bileşen.
 */
import { api, unwrap } from "./client";
import type { MatchStatus } from "./types";

type LeagueScope = { leagueId: number; season?: number };

export type FixtureQuery = LeagueScope & {
  status?: MatchStatus;
  teamId?: number;
  dateFrom?: string;
  dateTo?: string;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

export const endpoints = {
  leagues: () => unwrap(api.GET("/api/v1/leagues")),

  seasons: (leagueId: number) =>
    unwrap(api.GET("/api/v1/leagues/{league_id}/seasons", { params: { path: { league_id: leagueId } } })),

  overview: ({ leagueId, season }: LeagueScope) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/overview", {
        params: { path: { league_id: leagueId }, query: { season } },
      }),
    ),

  standings: ({ leagueId, season }: LeagueScope) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/standings", {
        params: { path: { league_id: leagueId }, query: { season } },
      }),
    ),

  fixtures: ({
    leagueId,
    season,
    status,
    teamId,
    dateFrom,
    dateTo,
    order,
    limit,
    offset,
  }: FixtureQuery) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/fixtures", {
        params: {
          path: { league_id: leagueId },
          query: {
            season,
            status,
            team_id: teamId,
            date_from: dateFrom,
            date_to: dateTo,
            order,
            limit,
            offset,
          },
        },
      }),
    ),

  fixture: (fixtureId: number) =>
    unwrap(api.GET("/api/v1/fixtures/{fixture_id}", { params: { path: { fixture_id: fixtureId } } })),

  fixtureStatistics: (fixtureId: number) =>
    unwrap(
      api.GET("/api/v1/fixtures/{fixture_id}/statistics", {
        params: { path: { fixture_id: fixtureId } },
      }),
    ),

  teams: ({ leagueId, season }: LeagueScope) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/teams", {
        params: { path: { league_id: leagueId }, query: { season } },
      }),
    ),

  teamStats: ({ leagueId, season, teamId }: LeagueScope & { teamId: number }) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/teams/{team_id}/stats", {
        params: { path: { league_id: leagueId, team_id: teamId }, query: { season } },
      }),
    ),

  aiStatus: () => unwrap(api.GET("/api/v1/insights/status")),

  createInsight: ({
    leagueId,
    season,
    teamAId,
    teamBId,
  }: LeagueScope & { teamAId: number; teamBId: number }) =>
    unwrap(
      api.POST("/api/v1/leagues/{league_id}/insights", {
        params: { path: { league_id: leagueId } },
        body: { team_a_id: teamAId, team_b_id: teamBId, season },
      }),
    ),

  syncStatus: () => unwrap(api.GET("/api/v1/sync/status")),

  rules: ({ leagueId, season }: LeagueScope) =>
    unwrap(
      api.GET("/api/v1/leagues/{league_id}/rules", {
        params: { path: { league_id: leagueId }, query: { season } },
      }),
    ),

  syncUsage: ({ leagueId, season }: LeagueScope) =>
    unwrap(api.GET("/api/v1/sync/usage", { params: { query: { league_id: leagueId, season } } })),

  triggerSync: ({ leagueId, season, full = false }: LeagueScope & { full?: boolean }) =>
    unwrap(api.POST("/api/v1/sync", { body: { league_id: leagueId, season, full } })),
};
