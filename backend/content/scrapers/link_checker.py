"""Periodic link health checker — archives published offers whose URLs are dead."""
import logging
import os
import time
from datetime import timedelta

import requests
from django.utils import timezone

logger = logging.getLogger(__name__)

# HTTP status codes that mean the page is definitively gone.
_DEAD_STATUSES = {404, 410}

# After this many consecutive failures the offer is archived.
_DEFAULT_THRESHOLD = 3

# Only re-check offers not checked within this window (avoids hammering servers daily).
_RECHECK_DAYS = 7


def check_offer_links(dry_run: bool = False) -> dict:
    """Check every published offer's link and archive those that are dead.

    Returns a summary dict: {checked, ok, soft_errors, archived}.
    """
    from content.models import Offer  # local import keeps this importable at module load

    threshold = int(os.getenv("LINK_CHECK_ERROR_THRESHOLD", str(_DEFAULT_THRESHOLD)))
    timeout = int(os.getenv("LINK_CHECK_TIMEOUT_SECONDS", "10"))
    delay = float(os.getenv("LINK_CHECK_DELAY_SECONDS", "0.5"))
    user_agent = os.getenv("SCRAPER_USER_AGENT", "OSS-LinkChecker/1.0")

    stale_cutoff = timezone.now() - timedelta(days=_RECHECK_DAYS)

    from django.db.models import Q
    # Only re-check offers never checked, or not checked in the last RECHECK_DAYS days.
    offers = list(
        Offer.objects.filter(status=Offer.OfferStatus.PUBLISHED)
        .filter(Q(link_last_checked__isnull=True) | Q(link_last_checked__lt=stale_cutoff))
        .values("id", "title", "link", "link_errors")
    )

    session = requests.Session()
    session.headers["User-Agent"] = user_agent

    checked = ok = soft_errors = archived = 0
    now = timezone.now()

    for offer in offers:
        is_dead = False
        try:
            resp = session.head(offer["link"], allow_redirects=True, timeout=timeout)
            if resp.status_code in _DEAD_STATUSES:
                is_dead = True
            else:
                # 2xx, 3xx, 4xx (non-dead), 5xx — not conclusively dead
                is_dead = False
        except requests.exceptions.RequestException:
            # DNS failure, connection refused, timeout — treat as a failure
            is_dead = True

        if is_dead:
            new_errors = offer["link_errors"] + 1
            if new_errors >= threshold:
                if not dry_run:
                    Offer.objects.filter(id=offer["id"]).update(
                        status=Offer.OfferStatus.ARCHIVED,
                        link_errors=new_errors,
                        link_last_checked=now,
                    )
                logger.info("Archived dead-link offer %s — %s", offer["id"], offer["link"])
                archived += 1
            else:
                if not dry_run:
                    Offer.objects.filter(id=offer["id"]).update(
                        link_errors=new_errors,
                        link_last_checked=now,
                    )
                logger.debug(
                    "Offer %s link error %d/%d — %s",
                    offer["id"], new_errors, threshold, offer["link"],
                )
                soft_errors += 1
        else:
            if not dry_run:
                Offer.objects.filter(id=offer["id"]).update(
                    link_errors=0,
                    link_last_checked=now,
                )
            ok += 1

        checked += 1
        time.sleep(delay)

    return {"checked": checked, "ok": ok, "soft_errors": soft_errors, "archived": archived}
