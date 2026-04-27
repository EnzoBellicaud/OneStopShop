import os

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.scrapers.queue_service import run_crawler, run_url_scraper_batch


class Command(BaseCommand):
    help = "Run crawler + URL scraper scheduler as a background worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--run-once",
            action="store_true",
            help="Execute one crawler run and one scraper batch then exit.",
        )

    def handle(self, *args, **options):
        crawler_interval = int(os.getenv("CRAWLER_INTERVAL_MINUTES", "360"))
        scraper_interval = int(os.getenv("SCRAPER_INTERVAL_MINUTES", "5"))
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
            minutes=crawler_interval,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        scheduler.add_job(
            run_url_scraper_batch,
            "interval",
            id="scrape-url-queue",
            minutes=scraper_interval,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )

        if run_on_start:
            self.stdout.write("Startup crawler run...")
            crawler_summary = run_crawler()
            self.stdout.write(f"Crawler: {crawler_summary}")
            self.stdout.write("Startup scraper batch...")
            scraper_summary = run_url_scraper_batch()
            self.stdout.write(f"Scraper: {scraper_summary}")

        self.stdout.write(
            f"Worker running — crawler every {crawler_interval} min, "
            f"scraper every {scraper_interval} min. Press Ctrl+C to stop."
        )

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Worker stopped.")
