from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import Offer


class Command(BaseCommand):
    help = "Archive published/draft offers whose deadline has passed."

    def handle(self, *args, **options):
        today = timezone.localdate()
        updated = (
            Offer.objects.filter(
                deadline__lt=today,
                status__in=(Offer.OfferStatus.PUBLISHED, Offer.OfferStatus.DRAFT),
            )
            .update(status=Offer.OfferStatus.ARCHIVED)
        )
        self.stdout.write(f"Archived {updated} expired offer(s) (deadline < {today}).")
