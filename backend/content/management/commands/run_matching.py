"""
Management command to run the matching service.

Usage:
  # Match all published offers
  python manage.py run_matching

  # Match specific offers
  python manage.py run_matching --offer-id <id1> --offer-id <id2>
"""

from django.core.management.base import BaseCommand, CommandError

from content.matching_service import run_matching_for_offers
from content.models import Offer


class Command(BaseCommand):
    help = "Run the matching service to create MatchingHit records"

    def add_arguments(self, parser):
        parser.add_argument(
            "--offer-id",
            type=str,
            action="append",
            dest="offer_ids",
            help="Specific offer ID to match (can be used multiple times)",
        )

    def handle(self, *args, **options):
        offer_ids = options.get("offer_ids") or []

        if offer_ids:
            # Validate that provided IDs are valid UUIDs
            try:
                ids = [str(oid) for oid in offer_ids]
                self.stdout.write(f"Running matching for {len(ids)} specified offer(s)…")
            except (ValueError, TypeError) as e:
                raise CommandError(f"Invalid offer ID format: {e}")
        else:
            # Match all published offers
            ids = list(
                Offer.objects.filter(status=Offer.OfferStatus.PUBLISHED).values_list(
                    "id", flat=True
                )
            )
            self.stdout.write(f"Running matching for all {len(ids)} published offer(s)…")

        if not ids:
            self.stdout.write(self.style.WARNING("No offers to process."))
            return

        stats = run_matching_for_offers(ids)
        
        # Format the output
        msg = (
            f"Done. offers={stats['offers']} candidates={stats['candidates']} "
            f"created={stats['created']} skipped={stats['skipped']} "
            f"below_threshold={stats['below_threshold']}"
        )
        self.stdout.write(self.style.SUCCESS(msg))
