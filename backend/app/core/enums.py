from enum import StrEnum


class MatchStatus(StrEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class MatchResult(StrEnum):
    """Bir maçın belirli bir takım açısından sonucu."""

    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"


class SyncTrigger(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    INITIAL = "initial"


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
