from django.core.management.base import BaseCommand

from content.scrapers.link_checker import check_offer_links


class Command(BaseCommand):
    help = "Check published offer URLs and archive any that return 404/410 repeatedly."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be archived without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write("Dry-run mode — no changes will be saved.")

        summary = check_offer_links(dry_run=dry_run)

        self.stdout.write(
            f"Link check complete: {summary['checked']} checked, "
            f"{summary['ok']} ok, "
            f"{summary['soft_errors']} soft errors (not yet at threshold), "
            f"{summary['archived']} archived."
        )
