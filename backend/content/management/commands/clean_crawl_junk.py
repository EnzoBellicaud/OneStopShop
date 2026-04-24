from django.core.management.base import BaseCommand
from django.db.models import Q

from content.models import Offer, SourceType
from content.scrapers.extractors import _GENERIC_TITLE_KEYWORDS


class Command(BaseCommand):
    help = "Remove known-bad crawl offers: generic-title pages and redirect duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted without deleting.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        try:
            source_type = SourceType.objects.get(name="scraping")
        except SourceType.DoesNotExist:
            self.stdout.write(self.style.WARNING("No 'scraping' source type found — nothing to clean."))
            return

        scraping_offers = Offer.objects.filter(source_type=source_type)

        # --- Generic-title pages (P1 blocklist) ---
        generic_filter = Q()
        for keyword in _GENERIC_TITLE_KEYWORDS:
            generic_filter |= Q(title__iexact=keyword)

        generic_qs = scraping_offers.filter(generic_filter)
        generic_count = generic_qs.count()
        if dry_run:
            self.stdout.write(f"[dry-run] Would delete {generic_count} generic-title offers.")
            for o in generic_qs.values_list("title", "link")[:20]:
                self.stdout.write(f"  - {o[0]!r}  {o[1]}")
        else:
            generic_qs.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {generic_count} generic-title offers."))

        # --- Redirect duplicates: same title + org appearing 3+ times (homepage spam) ---
        from django.db.models import Count
        duplicate_titles = (
            scraping_offers
            .values("title", "organization_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gte=3)
        )
        dup_deleted = 0
        for row in duplicate_titles:
            dupes = scraping_offers.filter(
                title=row["title"],
                organization_id=row["organization_id"],
            ).order_by("created_at")
            keep = dupes.first()
            to_delete = dupes.exclude(id=keep.id)
            dup_count = to_delete.count()
            if dry_run:
                self.stdout.write(
                    f"[dry-run] Would delete {dup_count} duplicate offers titled {row['title']!r}."
                )
            else:
                to_delete.delete()
                dup_deleted += dup_count

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Deleted {dup_deleted} duplicate-title offers."))
        else:
            self.stdout.write("[dry-run] No changes made.")
