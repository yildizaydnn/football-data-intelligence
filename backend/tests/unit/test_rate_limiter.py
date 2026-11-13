import pytest

from app.providers.api_football.rate_limiter import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def _limiter(clock: FakeClock, max_calls: int = 3) -> RateLimiter:
    return RateLimiter(max_calls, 60.0, clock=clock, sleep=clock.sleep)


def test_calls_within_limit_do_not_wait(clock: FakeClock) -> None:
    limiter = _limiter(clock)

    assert [limiter.acquire() for _ in range(3)] == [0.0, 0.0, 0.0]
    assert clock.sleeps == []


def test_waits_until_oldest_call_leaves_the_window(clock: FakeClock) -> None:
    limiter = _limiter(clock)
    limiter.acquire()  # t=0
    clock.now = 10
    limiter.acquire()  # t=10
    clock.now = 20
    limiter.acquire()  # t=20

    clock.now = 25
    assert limiter.acquire() == pytest.approx(35)  # t=0'daki istek t=60'ta pencereden çıkar
    assert clock.now == pytest.approx(60)

    # Sıradaki hak t=10'daki isteğin çıkmasını bekler.
    assert limiter.acquire() == pytest.approx(10)


def test_window_frees_up_after_period(clock: FakeClock) -> None:
    limiter = _limiter(clock, max_calls=1)
    limiter.acquire()

    clock.now = 61
    assert limiter.acquire() == 0.0
    assert clock.sleeps == []


def test_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError):
        RateLimiter(0)
