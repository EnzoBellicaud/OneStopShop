import json

from django.core.management.base import BaseCommand

from content.scrapers.service import run_scrape


class Command(BaseCommand):
    help = "Run university scraping once and print summary."

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

    def handle(self, *args, **options):
        summary = run_scrape(
            source_keys=options.get("source_keys"),
            dry_run=bool(options.get("dry_run")),
            use_llm_fallback=not bool(options.get("disable_llm_fallback")),
        )
        self.stdout.write(json.dumps(summary, indent=2))
