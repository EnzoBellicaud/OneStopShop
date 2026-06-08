from django.db.models.signals import post_delete, post_save


def _connect():
    from content.models import OfferType
    from content.scrapers.offer_type_catalog import invalidate_catalog

    def _bust(sender, **kwargs):
        invalidate_catalog()

    post_save.connect(
        _bust, sender=OfferType, weak=False,
        dispatch_uid="content.signals.offertype_post_save",
    )
    post_delete.connect(
        _bust, sender=OfferType, weak=False,
        dispatch_uid="content.signals.offertype_post_delete",
    )
