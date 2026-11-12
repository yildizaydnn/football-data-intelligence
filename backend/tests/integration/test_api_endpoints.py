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
