from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


def _connect():
    from content.models import OfferType
    from content.scrapers.offer_type_catalog import invalidate_catalog

    @receiver(post_save, sender=OfferType, weak=False)
    def _on_offertype_save(sender, **kwargs):
        invalidate_catalog()

    @receiver(post_delete, sender=OfferType, weak=False)
    def _on_offertype_delete(sender, **kwargs):
        invalidate_catalog()
