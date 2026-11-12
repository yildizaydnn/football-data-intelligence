import type { components } from "./schema";

type Schemas = components["schemas"];

export type League = Schemas["LeagueOut"];
export type Season = Schemas["SeasonOut"];
export type Team = Schemas["TeamOut"];
export type TeamRef = Schemas["TeamRef"];
export type Fixture = Schemas["FixtureOut"];
export type FixtureDetail = Schemas["FixtureDetailOut"];
export type FixturePage = Schemas["Paginated_FixtureOut_"];
export type Standings = Schemas["StandingsOut"];
export type StandingRow = Schemas["StandingRowOut"];
export type TeamStats = Schemas["TeamStatsOut"];
export type SplitStats = Schemas["SplitStatsOut"];
export type Overview = Schemas["OverviewOut"];
export type RoundGoals = Schemas["RoundGoalsOut"];
export type SyncRun = Schemas["SyncRunOut"];
export type SyncState = Schemas["SyncStateOut"];
export type SyncUsage = Schemas["SyncUsageOut"];

export type MatchStatus = Fixture["status"];
export type MatchResult = StandingRow["form"][number];
