"""Dakikalık istek sınırına takılmamak için istekleri aralıklandırır."""

import threading
import time
from collections import deque
from collections.abc import Callable
from functools import lru_cache


class RateLimiter:
    """Kayan pencere: son `period` saniyede en fazla `max_calls` istek.

    Sınır dolduysa en eski isteğin pencereden çıkmasını bekler. Bekleme kilit tutularak
    yapılır; aynı anda istek atmak isteyen thread'ler sıraya girer.
    """

    def __init__(
        self,
        max_calls: int,
        period: float = 60.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_calls < 1:
            raise ValueError("max_calls en az 1 olmalı")
        self._max_calls = max_calls
        self._period = period
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Bir istek hakkı alır; beklenen süreyi döner (0: beklemeden)."""
        with self._lock:
            self._forget_old(self._clock())
            waited = 0.0
            if len(self._calls) >= self._max_calls:
                waited = self._calls[0] + self._period - self._clock()
                if waited > 0:
                    self._sleep(waited)
                self._forget_old(self._clock())
            self._calls.append(self._clock())
            return max(waited, 0.0)

    def _forget_old(self, now: float) -> None:
        while self._calls and now - self._calls[0] >= self._period:
            self._calls.popleft()


@lru_cache
def shared_rate_limiter(requests_per_minute: int) -> RateLimiter:
    """Süreç genelinde tek limiter: her sync kendi client'ını açsa da sınır ortak sayılır."""
    return RateLimiter(requests_per_minute)
