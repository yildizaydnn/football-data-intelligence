from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_provider
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.exceptions import ProviderError
from app.main import create_app
from tests.fakes import FakeProvider

SETTINGS = Settings(
    _env_file=None, default_league_id=203, default_season=2024, api_football_daily_limit=100
)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider(remaining=90)


@pytest.fixture
def client(db_session: Session, provider: FakeProvider) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_provider] = lambda: provider
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def league_id(client: TestClient) -> int:
    """Veriyi gerçek API yolu üzerinden yükler: POST /sync."""
    assert client.post("/api/v1/sync", json={"full": True}).status_code == 200
    return client.get("/api/v1/leagues").json()[0]["id"]


class TestSync:
    def test_sync_then_status_and_usage(self, client: TestClient) -> None:
        response = client.post("/api/v1/sync")

        assert response.status_code == 200
        run = response.json()
        assert run["status"] == "partial"
        assert (run["trigger"], run["requests_made"], run["inserted"]) == ("manual", 3, 12)

        state = client.get("/api/v1/sync/status").json()
        assert state["running"] is None
        assert [r["id"] for r in state["recent"]] == [run["id"]]

        usage = client.get("/api/v1/sync/usage").json()
        assert (usage["requests_used"], usage["daily_limit"], usage["remaining"]) == (3, 100, 87)
        assert (usage["next_sync_cost"], usage["can_sync"]) == (1, True)  # artık sadece maçlar
        assert state["schedule"] == {"enabled": False, "cron": "0 4 * * *", "next_run_at": None}

    def test_failed_sync_returns_run_with_failed_status(
        self, client: TestClient, provider: FakeProvider
    ) -> None:
        provider.fail_on["get_league"] = ProviderError("API-Football HTTP 500", requests_made=3)

        run = client.post("/api/v1/sync").json()

        assert (run["status"], run["error_message"]) == ("failed", "API-Football HTTP 500")

    def test_quota_exceeded_returns_429(self, client: TestClient, provider: FakeProvider) -> None:
        client.app.dependency_overrides[get_settings] = lambda: Settings(
            _env_file=None, default_league_id=203, default_season=2024, api_football_daily_limit=1
        )

        response = client.post("/api/v1/sync")

        assert response.status_code == 429
        assert response.json()["error"]["code"] == "quota_exceeded"
        assert provider.calls == []

    def test_concurrent_sync_returns_409(self, client: TestClient, db_session: Session) -> None:
        from app.core.enums import SyncTrigger
        from app.repositories.sync_repository import SyncRunRepository

        SyncRunRepository(db_session).try_start(SyncTrigger.SCHEDULED)

        response = client.post("/api/v1/sync")

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "sync_in_progress"


class TestReadEndpoints:
    def test_leagues_and_seasons(self, client: TestClient, league_id: int) -> None:
        league = client.get(f"/api/v1/leagues/{league_id}").json()
        seasons = client.get(f"/api/v1/leagues/{league_id}/seasons").json()

        assert (league["name"], league["external_id"]) == ("Süper Lig", 203)
        assert [(s["year"], s["is_current"]) for s in seasons] == [(2024, True)]  # 2023'te veri yok

    def test_standings(self, client: TestClient, league_id: int) -> None:
        body = client.get(f"/api/v1/leagues/{league_id}/standings").json()

        assert body["season"] == 2024
        first = body["rows"][0]
        assert (first["position"], first["team"]["name"], first["points"]) == (1, "Fenerbahçe", 3)
        assert first["form"] == ["win"]
        assert first["goal_difference"] == 2

    def test_fixtures_list_filters_and_pagination(self, client: TestClient, league_id: int):
        url = f"/api/v1/leagues/{league_id}/fixtures"

        everything = client.get(url).json()
        finished = client.get(url, params={"status": "finished", "limit": 1}).json()

        assert everything["total"] == 5
        assert (finished["total"], len(finished["items"]), finished["limit"]) == (2, 1, 1)
        item = finished["items"][0]
        assert item["home_team"]["name"] == "Galatasaray"
        assert item["kickoff_at"].startswith("2024-09-21T16:00:00")

    def test_fixture_detail(self, client: TestClient, league_id: int) -> None:
        fixture_id = client.get(f"/api/v1/leagues/{league_id}/fixtures").json()["items"][0]["id"]

        body = client.get(f"/api/v1/fixtures/{fixture_id}").json()

        assert body["id"] == fixture_id
        assert body["changes"] == []

    def test_teams_and_team_stats(self, client: TestClient, league_id: int) -> None:
        teams = client.get(f"/api/v1/leagues/{league_id}/teams").json()
        fb = next(t for t in teams if t["name"] == "Fenerbahçe")

        stats = client.get(f"/api/v1/leagues/{league_id}/teams/{fb['id']}/stats").json()

        assert len(teams) == 4
        assert stats["overall"]["won"] == 1
        assert stats["overall"]["win_rate"] == 1.0
        assert stats["away"]["played"] == 1
        assert stats["current_streak"] == {"result": "win", "count": 1}
        assert stats["timeline"][0]["opponent"]["name"] == "Galatasaray"

    def test_overview(self, client: TestClient, league_id: int) -> None:
        body = client.get(f"/api/v1/leagues/{league_id}/overview").json()

        assert body["league"]["name"] == "Süper Lig"
        assert body["summary"]["total_matches"] == 5
        assert body["summary"]["by_status"]["finished"] == 2
        assert body["top_teams"][0]["team"]["name"] == "Fenerbahçe"
        assert body["last_sync"]["status"] == "partial"
        assert [f["external_id"] for f in body["live"]] == [1003]
        rounds = body["summary"]["goals_by_round"]
        assert [(r["number"], r["goals"]) for r in rounds] == [(6, 6)]
        assert body["summary"]["current_round"]["number"] == 6


class TestErrors:
    def test_not_found_format(self, client: TestClient) -> None:
        response = client.get("/api/v1/leagues/9999")

        assert response.status_code == 404
        assert response.json() == {
            "error": {"code": "not_found", "message": "Lig bulunamadı: 9999"}
        }

    def test_validation_error_format(self, client: TestClient, league_id: int) -> None:
        response = client.get(f"/api/v1/leagues/{league_id}/fixtures", params={"status": "xyz"})

        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "validation_error"
        assert error["details"][0]["field"] == "query.status"

    def test_unknown_route_uses_same_format(self, client: TestClient) -> None:
        response = client.get("/api/v1/yok")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"

    def test_unexpected_error_is_hidden(self, client: TestClient, league_id: int) -> None:
        from app.api.deps import get_standings_service

        class Broken:
            def get_standings(self, *_):
                raise RuntimeError("secret internals")

        client.app.dependency_overrides[get_standings_service] = Broken

        response = client.get(f"/api/v1/leagues/{league_id}/standings")

        assert response.status_code == 500
        assert response.json()["error"] == {
            "code": "internal_error",
            "message": "Beklenmeyen bir hata oluştu",
        }


def test_openapi_has_readable_operation_ids(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert paths["/api/v1/leagues/{league_id}/standings"]["get"]["operationId"] == "get_standings"
    assert paths["/api/v1/sync"]["post"]["operationId"] == "trigger_sync"


class TestSyncToken:
    @pytest.fixture
    def protected(self, client: TestClient) -> TestClient:
        client.app.dependency_overrides[get_settings] = lambda: Settings(
            _env_file=None, default_league_id=203, default_season=2024, sync_api_token="s3cret"
        )
        return client

    def test_missing_token_is_rejected(self, protected: TestClient, provider: FakeProvider):
        response = protected.post("/api/v1/sync")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"
        assert provider.calls == []

    def test_wrong_token_is_rejected(self, protected: TestClient) -> None:
        response = protected.post("/api/v1/sync", headers={"X-Sync-Token": "nope"})

        assert response.status_code == 401

    def test_valid_token_is_accepted(self, protected: TestClient) -> None:
        response = protected.post("/api/v1/sync", headers={"X-Sync-Token": "s3cret"})

        assert response.status_code == 200

    def test_read_endpoints_stay_public(self, protected: TestClient) -> None:
        assert protected.get("/api/v1/sync/usage").status_code == 200


class TestMultiLeagueAndRules:
    def test_manual_sync_targets_given_league_and_season(
        self, client: TestClient, league_id: int
    ) -> None:
        run = client.post("/api/v1/sync", json={"league_id": league_id, "season": 2024}).json()

        assert (run["league_external_id"], run["season"]) == (203, 2024)
        assert run["requests_made"] == 1  # lig zaten yüklü: sadece maçlar

    def test_usage_cost_depends_on_league_and_season(
        self, client: TestClient, league_id: int
    ) -> None:
        loaded = client.get("/api/v1/sync/usage", params={"league_id": league_id}).json()
        new_season = client.get(
            "/api/v1/sync/usage", params={"league_id": league_id, "season": 2021}
        ).json()

        assert loaded["next_sync_cost"] == 1
        assert new_season["next_sync_cost"] == 3  # sezon yok: referans veri de çekilir

    def test_unknown_league_in_sync_request_is_404(self, client: TestClient) -> None:
        assert client.post("/api/v1/sync", json={"league_id": 9999}).status_code == 404

    def test_rules_endpoint_reflects_league_spec(self, client: TestClient, league_id: int) -> None:
        rules = client.get(f"/api/v1/leagues/{league_id}/rules").json()

        assert rules["name"] == "Süper Lig"
        assert rules["league_external_id"] == 203
        assert rules["tiebreakers"][:2] == ["points", "h2h_points"]
        assert rules["points"] == {"win": 3, "draw": 1, "loss": 0}
        assert rules["verified"] is False

    def test_standings_rows_carry_zones_from_rules(
        self, client: TestClient, league_id: int
    ) -> None:
        body = client.get(f"/api/v1/leagues/{league_id}/standings").json()

        zones = {row["position"]: row["zone"] for row in body["rows"]}
        assert zones[1]["kind"] == "champions_league"
        assert body["rules"]["name"] == "Süper Lig"
        assert all("deduction" in row for row in body["rows"])


def test_fixture_statistics_endpoint(client: TestClient, provider: FakeProvider, league_id: int):
    fixtures = client.get(f"/api/v1/leagues/{league_id}/fixtures", params={"status": "finished"})
    fixture = next(f for f in fixtures.json()["items"] if f["external_id"] == 1002)
    provider.statistics[1002] = [
        {"team": {"id": 549}, "statistics": [{"type": "Ball Possession", "value": "48%"}]},
        {"team": {"id": 998}, "statistics": [{"type": "Ball Possession", "value": "52%"}]},
    ]

    body = client.get(f"/api/v1/fixtures/{fixture['id']}/statistics").json()

    assert body["availability"] == "available"
    assert body["lines"] == [{"key": "possession", "home": 48.0, "away": 52.0}]


def test_insight_endpoints(client: TestClient, league_id: int) -> None:
    from app.api.deps import get_text_generator
    from app.providers.llm.base import GeneratedText

    class Fake:
        def generate(self, *, system: str, prompt: str) -> GeneratedText:
            return GeneratedText("Fenerbahçe 3 puanla önde.", "fake")

    client.app.dependency_overrides[get_text_generator] = lambda: Fake()
    teams = {t["name"]: t["id"] for t in client.get(f"/api/v1/leagues/{league_id}/teams").json()}

    status = client.get("/api/v1/insights/status").json()
    body = client.post(
        f"/api/v1/leagues/{league_id}/insights",
        json={"team_a_id": teams["Fenerbahçe"], "team_b_id": teams["Galatasaray"]},
    ).json()

    assert status["enabled"] is True
    assert body["content"] == "Fenerbahçe 3 puanla önde."
    assert body["team_a"]["name"] == "Galatasaray"  # çift sıralı döner
    assert body["head_to_head"]["matches"] == 1
    assert body["unverified_numbers"] == []


def test_insight_disabled_returns_503(client: TestClient, league_id: int) -> None:
    from app.api.deps import get_text_generator

    client.app.dependency_overrides[get_text_generator] = lambda: None
    teams = [t["id"] for t in client.get(f"/api/v1/leagues/{league_id}/teams").json()]

    response = client.post(
        f"/api/v1/leagues/{league_id}/insights",
        json={"team_a_id": teams[0], "team_b_id": teams[1]},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_not_configured"


def test_sync_history_can_be_filtered_by_league(
    client: TestClient, db_session: Session, league_id: int
) -> None:
    from app.core.enums import SyncStatus, SyncTrigger
    from app.repositories.sync_repository import SyncRunRepository

    other = SyncRunRepository(db_session).try_start(SyncTrigger.MANUAL, 39, 2024)
    SyncRunRepository(db_session).finish(other, SyncStatus.SUCCESS)

    everything = client.get("/api/v1/sync/status").json()["recent"]
    only_this = client.get("/api/v1/sync/status", params={"league_id": league_id}).json()["recent"]

    assert {r["league_external_id"] for r in everything} == {203, 39}
    assert {r["league_external_id"] for r in only_this} == {203}
