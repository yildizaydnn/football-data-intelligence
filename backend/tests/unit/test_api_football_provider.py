from collections.abc import Iterator
from datetime import date

import httpx
import pytest
import respx
from tenacity import wait_none

from app.core.exceptions import ProviderError, QuotaExceededError
from app.providers.api_football.client import RATE_LIMIT_WINDOW_SECONDS, ApiFootballClient
from app.providers.api_football.provider import ApiFootballProvider
from tests.conftest import load_json

BASE_URL = "https://api.test"
QUOTA = {"x-ratelimit-requests-remaining": "87"}


@pytest.fixture
def sleeps() -> list[float]:
    """Client'ın beklediği süreler; testler gerçekten uyumaz."""
    return []


@pytest.fixture
def client(sleeps: list[float]) -> Iterator[ApiFootballClient]:
    with ApiFootballClient(
        BASE_URL, "secret", max_attempts=3, wait=wait_none(), sleep=sleeps.append
    ) as c:
        yield c


@pytest.fixture
def provider(client: ApiFootballClient) -> ApiFootballProvider:
    return ApiFootballProvider(client)


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


class TestProviderParsing:
    def test_get_league(self, provider: ApiFootballProvider, api: respx.MockRouter) -> None:
        route = api.get("/leagues").respond(json=load_json("leagues.json"), headers=QUOTA)

        result = provider.get_league(203)

        [league] = result.data
        assert league.league.id == 203
        assert league.country.name == "Turkey"
        assert [s.year for s in league.seasons if s.current] == [2024]
        assert result.requests_remaining == 87
        assert result.requests_made == 1
        assert route.calls.last.request.url.params["id"] == "203"
        assert route.calls.last.request.headers["x-apisports-key"] == "secret"

    def test_get_teams_tolerates_missing_venue(
        self, provider: ApiFootballProvider, api: respx.MockRouter
    ) -> None:
        api.get("/teams").respond(json=load_json("teams.json"), headers=QUOTA)

        result = provider.get_teams(203, 2024)

        assert len(result.data) == 4
        trabzon = result.data[-1]
        assert trabzon.team.code is None
        assert trabzon.venue.name is None

    def test_get_fixtures_keeps_incomplete_items(
        self, provider: ApiFootballProvider, api: respx.MockRouter
    ) -> None:
        # Eksik alanlı kayıt provider'da atılmaz; atlama kararı transformer'ındır.
        api.get("/fixtures").respond(json=load_json("fixtures.json"), headers=QUOTA)

        result = provider.get_fixtures(203, 2024)

        assert [f.fixture.id for f in result.data] == [1001, 1002, 1003, 1004, 1005, 1006]
        assert result.data[0].fixture.status.short == "FT"
        assert result.data[3].goals.home is None
        assert result.data[5].teams.home.id is None

    def test_get_fixtures_with_date_range(
        self, provider: ApiFootballProvider, api: respx.MockRouter
    ) -> None:
        route = api.get("/fixtures").respond(json=load_json("fixtures.json"))

        provider.get_fixtures(203, 2024, date_from=date(2024, 9, 1), date_to=date(2024, 9, 30))

        params = route.calls.last.request.url.params
        assert (params["from"], params["to"], params["timezone"]) == (
            "2024-09-01",
            "2024-09-30",
            "UTC",
        )

    def test_date_range_requires_both_ends(self, provider: ApiFootballProvider) -> None:
        with pytest.raises(ValueError):
            provider.get_fixtures(203, 2024, date_from=date(2024, 9, 1))

    def test_missing_quota_header_returns_none(
        self, provider: ApiFootballProvider, api: respx.MockRouter
    ) -> None:
        api.get("/leagues").respond(json=load_json("leagues.json"))

        assert provider.get_league(203).requests_remaining is None


class TestClientErrors:
    def test_retries_on_5xx_then_succeeds(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        api.get("/leagues").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(200, json=load_json("leagues.json"), headers=QUOTA),
            ]
        )

        result = client.get("/leagues")

        assert result.requests_made == 2
        assert result.requests_remaining == 87

    def test_retries_on_timeout(self, client: ApiFootballClient, api: respx.MockRouter) -> None:
        api.get("/leagues").mock(
            side_effect=[
                httpx.ReadTimeout("timeout"),
                httpx.Response(200, json=load_json("leagues.json")),
            ]
        )

        assert client.get("/leagues").requests_made == 2

    def test_gives_up_after_max_attempts(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        route = api.get("/leagues").respond(429)

        with pytest.raises(ProviderError) as exc_info:
            client.get("/leagues")

        assert route.call_count == 3
        assert exc_info.value.requests_made == 3

    def test_does_not_retry_client_errors(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        route = api.get("/leagues").respond(403, text="forbidden")

        with pytest.raises(ProviderError):
            client.get("/leagues")

        assert route.call_count == 1

    def test_daily_limit_in_body_raises_quota_error(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        route = api.get("/fixtures").respond(json=load_json("error_quota.json"))

        with pytest.raises(QuotaExceededError):
            client.get("/fixtures")

        assert route.call_count == 1

    def test_body_error_raises_provider_error(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        api.get("/fixtures").respond(json=load_json("error_token.json"))

        with pytest.raises(ProviderError, match="token"):
            client.get("/fixtures")

    def test_per_minute_rate_limit_in_body_waits_for_next_window(
        self, client: ApiFootballClient, api: respx.MockRouter, sleeps: list[float]
    ) -> None:
        rate_limited = {"errors": {"rateLimit": "Too many requests"}, "response": []}
        api.get("/leagues").mock(
            side_effect=[
                httpx.Response(200, json=rate_limited),
                httpx.Response(200, json=load_json("leagues.json")),
            ]
        )

        assert client.get("/leagues").requests_made == 2
        assert sleeps == [RATE_LIMIT_WINDOW_SECONDS]

    def test_http_429_honours_retry_after_header(
        self, client: ApiFootballClient, api: respx.MockRouter, sleeps: list[float]
    ) -> None:
        api.get("/leagues").mock(
            side_effect=[
                httpx.Response(429, headers={"retry-after": "12"}),
                httpx.Response(200, json=load_json("leagues.json")),
            ]
        )

        assert client.get("/leagues").requests_made == 2
        assert sleeps == [12.0]

    def test_retry_after_is_capped_at_one_window(
        self, client: ApiFootballClient, api: respx.MockRouter, sleeps: list[float]
    ) -> None:
        api.get("/leagues").mock(
            side_effect=[
                httpx.Response(429, headers={"retry-after": "3600"}),
                httpx.Response(200, json=load_json("leagues.json")),
            ]
        )

        client.get("/leagues")

        assert sleeps == [RATE_LIMIT_WINDOW_SECONDS]

    def test_server_errors_keep_short_backoff(
        self, client: ApiFootballClient, api: respx.MockRouter, sleeps: list[float]
    ) -> None:
        api.get("/leagues").mock(
            side_effect=[
                httpx.Response(503),
                httpx.Response(200, json=load_json("leagues.json")),
            ]
        )

        client.get("/leagues")

        assert sleeps == [0]  # wait_none: dakika beklemesi yalnızca rate limit için

    def test_invalid_json_raises_provider_error(
        self, client: ApiFootballClient, api: respx.MockRouter
    ) -> None:
        api.get("/leagues").respond(200, text="<html>bakımda</html>")

        with pytest.raises(ProviderError, match="JSON"):
            client.get("/leagues")
