from django.core.management.base import BaseCommand

from content.matching_service import run_matching_for_offers
from content.models import Offer


class Command(BaseCommand):
    help = "Run the hybrid matching engine against all published offers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--offer-id",
            nargs="*",
            metavar="UUID",
            help="Limit matching to specific offer UUIDs (default: all published).",
        )

    def handle(self, *args, **options):
        offer_ids = options.get("offer_id")
        if offer_ids:
            ids = offer_ids
            self.stdout.write(f"Running matching for {len(ids)} specified offer(s)…")
        else:
            ids = list(
                Offer.objects.filter(status=Offer.OfferStatus.PUBLISHED).values_list("id", flat=True)
            )
            self.stdout.write(f"Running matching for all {len(ids)} published offer(s)…")

        if not ids:
            self.stdout.write(self.style.WARNING("No offers to process."))
            return

        stats = run_matching_for_offers(ids)
        self.stdout.write(self.style.SUCCESS(
            f"Done. offers={stats['offers']} candidates={stats['candidates']} "
            f"created={stats['created']} skipped={stats['skipped']} "
            f"below_threshold={stats['below_threshold']}"
        ))
