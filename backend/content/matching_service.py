"""
Hybrid matching engine for connecting user needs with offers.

Entry point: run_matching_for_offers(offer_ids)
This is called after offers are published or updated.

Flow per (offer, need) pair:
  1. Fast filter — target_profile, countries, domain, keyword overlap
  2. Simple scoring — keyword-based if LLM unavailable
  3. Upsert — create MatchingHit if score >= threshold
"""

import logging
import re
from decimal import Decimal

from django.db import IntegrityError, transaction

from content.models import MatchingHit, Offer, UserNeed

LOGGER = logging.getLogger(__name__)

# Common stopwords to exclude from keyword matching
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with",
    "is", "are", "was", "be", "on", "at", "by", "from", "as", "we",
    "our", "your", "this", "that", "have", "has", "will", "can", "it",
    "its", "not", "but", "if", "all", "any", "more", "new", "you",
    "do", "does", "did", "would", "should", "could", "may", "might",
    "also", "some", "these", "their", "they", "about", "into", "how",
}

_MIN_KEYWORD_OVERLAP = 1
_MIN_SCORE = Decimal("0.40")  # Minimum match score to create a MatchingHit


def _tokenize(text: str) -> set[str]:
    """Extract keywords from text, excluding stopwords."""
    if not text:
        return set()
    words = re.findall(r"\b\w+\b", text.lower())
    return {word for word in words if len(word) > 2 and word not in _STOPWORDS}


def _keyword_overlap(need: UserNeed, offer: Offer) -> int:
    """Count shared keywords between need and offer."""
    need_keywords = _tokenize(need.title) | _tokenize(need.description or "")
    offer_keywords = _tokenize(offer.title) | _tokenize(offer.summary or "")
    return len(need_keywords & offer_keywords)


def _passes_fast_filter(
    need: UserNeed,
    offer: Offer,
    need_domain_ids: set,
    offer_domain_ids: set,
) -> bool:
    """Check if need and offer meet basic matching criteria."""
    # target_profile must match when the need has one set
    if need.target_profile_id is not None and need.target_profile_id != offer.target_profile_id:
        return False

    # if need specifies countries, offer must be in them
    if need.countries and offer.country not in need.countries:
        return False

    # if need specifies domains, offer must share at least one
    if need_domain_ids and not (need_domain_ids & offer_domain_ids):
        return False

    # at least one keyword in common
    if _keyword_overlap(need, offer) < _MIN_KEYWORD_OVERLAP:
        return False

    return True


def _keyword_score(need: UserNeed, offer: Offer) -> tuple[Decimal, str]:
    """Score based on keyword overlap (fallback when LLM is unavailable)."""
    overlap = _keyword_overlap(need, offer)
    # Simple scoring: more keywords = higher score (0.4 to 0.9)
    score = Decimal("0.4") + Decimal(min(overlap, 5)) * Decimal("0.1")
    score = min(score, Decimal("0.9"))
    reason = f"Keyword match: {overlap} shared terms between need and offer."
    return score, reason


def run_matching_for_offers(offer_ids: list) -> dict:
    """
    For each offer in offer_ids, match against all active user needs.
    Creates MatchingHit records for strong matches.
    
    Returns: dict with statistics about the matching run
    """
    stats = {
        "offers": 0,
        "candidates": 0,
        "created": 0,
        "skipped": 0,
        "below_threshold": 0,
    }

    if not offer_ids:
        return stats

    # Fetch published offers
    offers = list(
        Offer.objects.filter(id__in=offer_ids, status=Offer.OfferStatus.PUBLISHED)
        .select_related("offer_type", "organization", "target_profile")
        .prefetch_related("domains")
    )
    if not offers:
        LOGGER.info("No published offers found in provided IDs")
        return stats

    # Fetch active needs that are looking for matches
    active_needs = list(
        UserNeed.objects.filter(status=UserNeed.NeedStatus.ACTIVE)
        .select_related("user", "target_profile")
        .prefetch_related("domains")
    )
    if not active_needs:
        stats["offers"] = len(offers)
        LOGGER.info("No active needs to match against")
        return stats

    # Pre-fetch existing pairs to skip duplicates
    existing_pairs = set(
        MatchingHit.objects.filter(
            need__in=active_needs,
            offer__in=offers,
        ).values_list("need_id", "offer_id")
    )

    # Pre-compute domain id sets for fast filtering
    offer_domain_map = {o.id: {d.id for d in o.domains.all()} for o in offers}
    need_domain_map = {n.id: {d.id for d in n.domains.all()} for n in active_needs}

    stats["offers"] = len(offers)

    # Process each offer against each need
    with transaction.atomic():
        for offer in offers:
            offer_domains = offer_domain_map[offer.id]
            
            for need in active_needs:
                # Skip if match already exists
                if (need.id, offer.id) in existing_pairs:
                    stats["skipped"] += 1
                    continue

                # Apply fast filter
                if not _passes_fast_filter(
                    need, offer, need_domain_map[need.id], offer_domains
                ):
                    continue

                stats["candidates"] += 1

                # Score the pair
                score, reason = _keyword_score(need, offer)

                # Skip below threshold
                if score < _MIN_SCORE:
                    stats["below_threshold"] += 1
                    LOGGER.debug(
                        "Below threshold %.2f — need=%s offer=%s",
                        score,
                        need.id,
                        offer.id,
                    )
                    continue

                # Create the match
                try:
                    MatchingHit.objects.create(
                        user=need.user,
                        need=need,
                        offer=offer,
                        match_score=score,
                        match_reason=reason,
                    )
                    stats["created"] += 1
                    LOGGER.info(
                        "MatchingHit created score=%.2f need=%s offer=%s",
                        score,
                        need.id,
                        offer.id,
                    )
                except IntegrityError:
                    stats["skipped"] += 1
                    LOGGER.debug("Duplicate match pair: need=%s offer=%s", need.id, offer.id)

    LOGGER.info("Matching complete — %s", stats)
    return stats
