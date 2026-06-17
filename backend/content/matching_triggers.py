import logging
from collections.abc import Iterable

from django.db import transaction

from content.matching_service import run_matching_for_offers
from content.models import MatchingHit, Offer, UserNeed

LOGGER = logging.getLogger(__name__)


def _normalize_ids(ids: Iterable) -> list:
    return list(dict.fromkeys(value for value in ids if value))


def refresh_matches_for_offers(offer_ids: Iterable) -> None:
    """Refresh matching hits affected by offer create/update operations."""
    normalized_ids = _normalize_ids(offer_ids)
    if not normalized_ids:
        return

    def _refresh() -> None:
        published_ids = list(
            Offer.objects.filter(
                id__in=normalized_ids,
                status=Offer.OfferStatus.PUBLISHED,
            ).values_list("id", flat=True)
        )
        MatchingHit.objects.filter(offer_id__in=normalized_ids).delete()
        if not published_ids:
            return
        stats = run_matching_for_offers(published_ids)
        LOGGER.info("Offer matching refresh completed: %s", stats)

    transaction.on_commit(_refresh)


def refresh_matches_for_need(need_id) -> None:
    """Refresh matching hits affected by a user need create/update operation."""
    if not need_id:
        return

    def _refresh() -> None:
        MatchingHit.objects.filter(need_id=need_id).delete()
        active = UserNeed.objects.filter(
            id=need_id,
            status=UserNeed.NeedStatus.ACTIVE,
        ).exists()
        if not active:
            return

        published_ids = list(
            Offer.objects.filter(status=Offer.OfferStatus.PUBLISHED).values_list(
                "id",
                flat=True,
            )
        )
        if not published_ids:
            return
        stats = run_matching_for_offers(published_ids, need_ids=[need_id])
        LOGGER.info("Need matching refresh completed: need_id=%s stats=%s", need_id, stats)

    transaction.on_commit(_refresh)
