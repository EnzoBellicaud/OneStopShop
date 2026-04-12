import os

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.scrapers.service import run_scrape


class Command(BaseCommand):
    help = "Run scraping scheduler as a background worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--run-once",
            action="store_true",
            help="Execute a single run then exit.",
        )

    def handle(self, *args, **options):
        if options.get("run_once"):
            summary = run_scrape()
            self.stdout.write(f"One-shot scraping summary: {summary}")
            return

        interval_minutes = int(os.getenv("SCRAPER_INTERVAL_MINUTES", "360"))
        run_on_start = os.getenv("SCRAPER_RUN_ON_START", "true").lower() == "true"

        scheduler = BlockingScheduler(timezone=timezone.get_current_timezone_name())
        scheduler.add_job(
            run_scrape,
            "interval",
            id="scrape-university-sources",
            minutes=interval_minutes,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        if run_on_start:
            summary = run_scrape()
            self.stdout.write(f"Startup scraping summary: {summary}")

        self.stdout.write(
            f"Scraper worker running every {interval_minutes} minute(s). Press Ctrl+C to stop."
        )

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Scraper worker stopped.")
