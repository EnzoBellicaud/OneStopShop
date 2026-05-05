import json

from django.core.management.base import BaseCommand

from content.scrapers.queue_service import run_crawler, run_url_scraper_batch
from content.scrapers.service import run_scrape


class Command(BaseCommand):
    help = "Run scraping once and print summary."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-key",
            action="append",
            dest="source_keys",
            help="Optional source key filter. Can be provided multiple times.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Evaluate scraping results without writing DB changes.",
        )
        parser.add_argument(
            "--disable-llm-fallback",
            action="store_true",
            help="Disable Ollama fallback even when confidence is low.",
        )
        parser.add_argument(
            "--crawl",
            action="store_true",
            help="Legacy: force crawl mode via old ScrapeService path.",
        )
        parser.add_argument(
            "--queue",
            action="store_true",
            help="Use new queue flow: run crawler to populate CrawlUrl, then run scraper batch.",
        )

    def handle(self, *args, **options):
        use_queue = bool(options.get("queue"))
        use_llm = not bool(options.get("disable_llm_fallback"))
        source_keys = options.get("source_keys")

        if use_queue:
            self.stdout.write("--- Crawler phase ---")
            crawler_summary = run_crawler(source_keys=source_keys)
            self.stdout.write(json.dumps(crawler_summary, indent=2))

            self.stdout.write("--- Scraper batch phase ---")
            scraper_summary = run_url_scraper_batch(use_llm_fallback=use_llm)
            self.stdout.write(json.dumps(scraper_summary, indent=2))
        else:
            summary = run_scrape(
                source_keys=source_keys,
                dry_run=bool(options.get("dry_run")),
                use_llm_fallback=use_llm,
                crawl=bool(options.get("crawl")),
            )
            self.stdout.write(json.dumps(summary, indent=2))
