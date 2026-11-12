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

  fixtures: ({ leagueId, season, status, teamId, dateFrom, dateTo, limit, offset }: FixtureQuery) =>
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
            limit,
            offset,
          },
        },
      }),
    ),

  fixture: (fixtureId: number) =>
    unwrap(api.GET("/api/v1/fixtures/{fixture_id}", { params: { path: { fixture_id: fixtureId } } })),

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

  syncStatus: () => unwrap(api.GET("/api/v1/sync/status")),

  syncUsage: () => unwrap(api.GET("/api/v1/sync/usage")),

  triggerSync: (full = false) => unwrap(api.POST("/api/v1/sync", { body: { full } })),
};
