import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import Settings
from app.scheduler.jobs import run_scheduled_sync

logger = logging.getLogger(__name__)

DAILY_SYNC_JOB_ID = "daily_fixture_sync"


def create_scheduler(settings: Settings) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_scheduled_sync,
        CronTrigger.from_crontab(settings.sync_cron, timezone="UTC"),
        id=DAILY_SYNC_JOB_ID,
        max_instances=1,  # bir önceki çalışma sürerken yenisi başlamaz
        coalesce=True,  # uygulama kapalıyken kaçan çalışmalar tek seferde telafi edilir
        misfire_grace_time=60 * 60,
    )
    return scheduler


def start_scheduler(settings: Settings) -> BackgroundScheduler | None:
    """Ayarlar uygunsa scheduler'ı başlatır.

    Birden fazla worker/instance çalışırsa her biri kendi scheduler'ını başlatır; aynı anda
    tek sync'e izin veren DB kilidi sayesinde fazladan istek atılmaz.
    """
    if not settings.scheduler_enabled:
        logger.info("Scheduler kapalı (SCHEDULER_ENABLED=false)")
        return None
    if not settings.api_football_key:
        logger.warning("Scheduler başlatılmadı: API_FOOTBALL_KEY tanımlı değil")
        return None

    scheduler = create_scheduler(settings)
    scheduler.start()
    job = scheduler.get_job(DAILY_SYNC_JOB_ID)
    logger.info("Scheduler başladı; sonraki sync: %s", job.next_run_time if job else "-")
    return scheduler
