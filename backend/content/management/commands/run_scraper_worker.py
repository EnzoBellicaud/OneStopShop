import os

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.scrapers.queue_service import run_crawler, run_url_scraper_batch
from content.scrapers.link_checker import check_offer_links
from content.scrapers.translation_service import run_offer_translation_batch


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

        scheduler = BlockingScheduler(timezone=timezone.get_current_timezone_name())

        scheduler.add_job(
            run_crawler,
            "interval",
            id="crawl-discover-urls",
            seconds=crawler_interval,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        scheduler.add_job(
            run_url_scraper_batch,
            "interval",
            id="scrape-url-queue",
            seconds=scraper_interval,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )
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

        if run_on_start:
            self.stdout.write("Startup crawler run...")
            crawler_summary = run_crawler()
            self.stdout.write(f"Crawler: {crawler_summary}")
            self.stdout.write("Startup scraper batch...")
            scraper_summary = run_url_scraper_batch()
            self.stdout.write(f"Scraper: {scraper_summary}")
            self.stdout.write("Startup offer translation...")
            translation_summary = run_offer_translation_batch(limit=translation_batch)
            self.stdout.write(f"Translation: {translation_summary}")

        self.stdout.write(
            f"Worker running — crawler every {crawler_interval}s, "
            f"scraper every {scraper_interval}s, "
            f"translation every {translation_interval} min. Press Ctrl+C to stop."
        )

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Worker stopped.")
