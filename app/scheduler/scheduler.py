import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config.settings import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone=ZoneInfo(settings.timezone))
        self._started = False

    def _daily_placeholder_job(self) -> None:
        logger.info("Daily pipeline placeholder executed at %s", datetime.now())

    def start(self) -> None:
        if self._started:
            return

        trigger = CronTrigger(hour=settings.scheduler_hour, minute=settings.scheduler_minute)
        self._scheduler.add_job(
            self._daily_placeholder_job,
            trigger=trigger,
            id="daily_pipeline_placeholder",
            replace_existing=True,
        )
        self._scheduler.start()
        self._started = True
        logger.info(
            "Scheduler started with timezone=%s at %02d:%02d",
            settings.timezone,
            settings.scheduler_hour,
            settings.scheduler_minute,
        )

    def shutdown(self) -> None:
        if not self._started:
            return
        self._scheduler.shutdown(wait=False)
        self._started = False
        logger.info("Scheduler stopped")


scheduler_service = SchedulerService()
