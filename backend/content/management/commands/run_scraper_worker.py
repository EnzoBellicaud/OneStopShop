import logging
import os
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.scrapers.queue_service import run_crawler, run_url_scraper_batch
from content.scrapers.link_checker import check_offer_links
from content.scrapers.translation_service import run_offer_translation_batch

LOGGER = logging.getLogger(__name__)


def _loop(fn: callable, interval: float, stop: threading.Event) -> None:
    """Run fn, sleep interval seconds, repeat — guarantees no overlap."""
    while not stop.is_set():
        try:
            fn()
        except Exception:
            LOGGER.exception("Worker loop error in %s", fn.__name__)
        stop.wait(interval)


def _archive_expired_offers():
    from django.utils import timezone as tz
    from content.models import Offer
    today = tz.localdate()
    updated = (
        Offer.objects.filter(
            deadline__lt=today,
            status__in=(Offer.OfferStatus.PUBLISHED, Offer.OfferStatus.DRAFT),
        )
        .update(status=Offer.OfferStatus.ARCHIVED)
    )
    if updated:
        import logging
        logging.getLogger(__name__).info("Archived %d expired offer(s).", updated)


class Command(BaseCommand):
    help = "Run crawler + URL scraper scheduler as a background worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--run-once",
            action="store_true",
            help="Execute one crawler run and one scraper batch then exit.",
        )

    def handle(self, *args, **options):
        crawler_interval = int(os.getenv("CRAWLER_INTERVAL_SECONDS", "1"))
        scraper_interval = int(os.getenv("SCRAPER_INTERVAL_SECONDS", "1"))
        translation_interval = int(os.getenv("TRANSLATION_INTERVAL_MINUTES", "10"))
        translation_batch = int(os.getenv("TRANSLATION_BATCH_SIZE", "20"))
        run_on_start = os.getenv("SCRAPER_RUN_ON_START", "true").lower() == "true"

        if options.get("run_once"):
            self.stdout.write("Crawler run...")
            crawler_summary = run_crawler()
            self.stdout.write(f"Crawler: {crawler_summary}")
            self.stdout.write("Scraper batch...")
            scraper_summary = run_url_scraper_batch()
            self.stdout.write(f"Scraper: {scraper_summary}")
            return

        stop = threading.Event()

        if run_on_start:
            self.stdout.write("Startup crawler run...")
            self.stdout.write(f"Crawler: {run_crawler()}")
            self.stdout.write("Startup scraper batch...")
            self.stdout.write(f"Scraper: {run_url_scraper_batch()}")
            self.stdout.write("Startup offer translation...")
            self.stdout.write(f"Translation: {run_offer_translation_batch(limit=translation_batch)}")

        # Crawler and scraper run in threads: each waits N seconds AFTER the
        # previous run completes, so no overlap and no APScheduler skip warnings.
        threading.Thread(
            target=_loop, args=(run_crawler, crawler_interval, stop), daemon=True, name="crawler"
        ).start()
        threading.Thread(
            target=_loop, args=(run_url_scraper_batch, scraper_interval, stop), daemon=True, name="scraper"
        ).start()

        # Cron jobs (infrequent) stay on APScheduler.
        scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone_name())
        scheduler.add_job(
            run_offer_translation_batch,
            "interval",
            id="translate-offers",
            minutes=translation_interval,
            kwargs={"limit": translation_batch},
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        scheduler.add_job(
            _archive_expired_offers,
            "cron",
            id="archive-expired-offers",
            hour=2,
            minute=0,
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            check_offer_links,
            "cron",
            id="check-offer-links",
            hour=3,
            minute=0,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()

        self.stdout.write(
            f"Worker running — crawler every {crawler_interval}s after completion, "
            f"scraper every {scraper_interval}s after completion, "
            f"translation every {translation_interval} min. Press Ctrl+C to stop."
        )

        try:
            stop.wait()
        except (KeyboardInterrupt, SystemExit):
            stop.set()
            scheduler.shutdown(wait=False)
            self.stdout.write("Worker stopped.")
