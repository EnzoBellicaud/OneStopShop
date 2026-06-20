from django.core.management.base import BaseCommand

from content.scrapers.translation_service import run_offer_translation_batch


class Command(BaseCommand):
    help = "Translate published offers' title/summary into the supported UI languages (cached on Offer.details)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of offers to translate in this run.",
        )

    def handle(self, *args, **options):
        summary = run_offer_translation_batch(limit=options["limit"])
        self.stdout.write(
            f"Translation batch: scanned={summary['scanned']} "
            f"processed={summary['processed']} updated={summary['updated']}"
        )
