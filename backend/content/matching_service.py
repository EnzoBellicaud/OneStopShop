import re
import logging
from decimal import Decimal
from django.db import transaction
from collections import defaultdict
from collections.abc import Iterable
from content.models import MatchingHit, Offer, UserNeed

LOGGER = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with",
    "is", "are", "was", "be", "on", "at", "by", "from", "as", "we",
    "our", "your", "this", "that", "have", "has", "will", "can", "it",
    "its", "not", "but", "if", "all", "any", "more", "new", "you",
    "do", "does", "did", "would", "should", "could", "may", "might",
    "also", "some", "these", "their", "they", "about", "into", "how",
}

_MIN_KEYWORD_OVERLAP = 1
_MIN_SCORE = Decimal("0.40")


# ============================================================
# TOKENIZATION
# ============================================================

def _tokenize(text: str) -> set[str]:
    """
    Convert text into normalized keywords.

    IMPORTANT:
    Tokenization is relatively expensive because of regex.
    Therefore we compute it ONCE per offer/need and reuse it.
    """
    if not text:
        return set()

    words = re.findall(r"\b\w+\b", text.lower())

    return {
        word
        for word in words
        if len(word) > 2 and word not in _STOPWORDS
    }


# ============================================================
# FAST FILTERS
# ============================================================

def _passes_filters(
    need,
    offer,
    need_domains,
    offer_domains,
):
    """
    Cheap filters.

    Order matters:
      1. profile
      2. country
      3. domains

    These checks are O(1) and should execute
    before any expensive scoring.
    """

    if (
        need.target_profile_id is not None
        and need.target_profile_id != offer.target_profile_id
    ):
        return False

    if need.countries and offer.country not in need.countries:
        return False

    if need_domains and not (need_domains & offer_domains):
        return False

    return True


# ============================================================
# SCORING
# ============================================================

def _keyword_overlap(need, offer) -> int:
    """
    Calculate the number of overlapping keywords between a need and an offer.
    """
    need_keywords = _tokenize(need.title) | _tokenize(need.description or "")
    offer_keywords = _tokenize(offer.title) | _tokenize(offer.summary or "")
    return len(need_keywords & offer_keywords)


def _score_from_overlap(overlap: int) -> tuple[Decimal, str]:
    """
    Convert keyword overlap into score.

    Current logic preserved.
    """

    score = Decimal("0.4") + Decimal(min(overlap, 5)) * Decimal("0.1")
    score = min(score, Decimal("0.9"))

    return (
        score,
        f"Keyword match: {overlap} shared terms."
    )


def _keyword_score(need, offer) -> tuple[Decimal, str]:
    """
    Calculate keyword-based score for a need-offer pair.
    """
    overlap = _keyword_overlap(need, offer)
    return _score_from_overlap(overlap)


def _passes_fast_filter(need, offer, need_domains, offer_domains) -> bool:
    """
    Wrapper around _passes_filters for backward compatibility with tests.
    """
    return _passes_filters(need, offer, need_domains, offer_domains)


# ============================================================
# MATCHING ENGINE
# ============================================================

def run_matching_for_offers(offer_ids: Iterable, need_ids: Iterable | None = None) -> dict:
    """
    Optimized matching engine.

    Key improvements:

    1. Keywords computed once.
    2. Inverted keyword index.
    3. No full scan of all needs.
    4. Overlap computed once.
    5. bulk_create instead of create().
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

    normalized_offer_ids = list(dict.fromkeys(value for value in offer_ids if value))
    normalized_need_ids = list(dict.fromkeys(need_ids or []))
    if not normalized_offer_ids:
        return stats

    # --------------------------------------------------------
    # Load offers
    # --------------------------------------------------------

    offers = list(
        Offer.objects.filter(
            id__in=normalized_offer_ids,
            status=Offer.OfferStatus.PUBLISHED,
        )
        .select_related(
            "offer_type",
            "organization",
            "target_profile",
        )
        .prefetch_related("domains")
    )

    if not offers:
        return stats

    # --------------------------------------------------------
    # Load active needs
    # --------------------------------------------------------

    active_needs_query = UserNeed.objects.filter(status=UserNeed.NeedStatus.ACTIVE)
    if normalized_need_ids:
        active_needs_query = active_needs_query.filter(id__in=normalized_need_ids)

    active_needs = list(
        active_needs_query
        .select_related(
            "user",
            "target_profile",
        )
        .prefetch_related("domains")
    )

    if not active_needs:
        stats["offers"] = len(offers)
        return stats

    stats["offers"] = len(offers)

    # --------------------------------------------------------
    # Existing matches
    # --------------------------------------------------------

    existing_pairs = set(
        MatchingHit.objects.filter(
            need__in=active_needs,
            offer__in=offers,
        ).values_list(
            "need_id",
            "offer_id",
        )
    )

    # --------------------------------------------------------
    # Domain maps
    # --------------------------------------------------------

    offer_domain_map = {
        offer.id: {d.id for d in offer.domains.all()}
        for offer in offers
    }

    need_domain_map = {
        need.id: {d.id for d in need.domains.all()}
        for need in active_needs
    }

    # --------------------------------------------------------
    # Precompute keywords
    # --------------------------------------------------------

    offer_keywords = {
        offer.id:
        _tokenize(offer.title)
        | _tokenize(offer.summary or "")
        for offer in offers
    }

    need_keywords = {
        need.id:
        _tokenize(need.title)
        | _tokenize(need.description or "")
        for need in active_needs
    }

    # --------------------------------------------------------
    # Build inverted index
    #
    # Example:
    #
    # python -> {1,4,7}
    # aws    -> {4,9}
    # ai     -> {1,2,5}
    #
    # This avoids scanning every need.
    # --------------------------------------------------------

    keyword_index = defaultdict(set)

    for need in active_needs:
        for keyword in need_keywords[need.id]:
            keyword_index[keyword].add(need.id)

    need_lookup = {
        need.id: need
        for need in active_needs
    }

    hits_to_create = []

    # --------------------------------------------------------
    # Main matching loop
    # --------------------------------------------------------

    for offer in offers:

        offer_kw = offer_keywords[offer.id]

        # ----------------------------------------------
        # Candidate generation
        #
        # Instead of:
        #    all active needs
        #
        # We collect only needs sharing
        # at least one keyword.
        # ----------------------------------------------

        candidate_need_ids = set()

        for keyword in offer_kw:
            candidate_need_ids.update(
                keyword_index.get(keyword, set())
            )

        if not candidate_need_ids:
            continue

        offer_domains = offer_domain_map[offer.id]

        for need_id in candidate_need_ids:

            need = need_lookup[need_id]

            if (need.id, offer.id) in existing_pairs:
                stats["skipped"] += 1
                continue

            if not _passes_filters(
                need,
                offer,
                need_domain_map[need.id],
                offer_domains,
            ):
                continue

            overlap = len(
                offer_kw &
                need_keywords[need.id]
            )

            if overlap < _MIN_KEYWORD_OVERLAP:
                continue

            stats["candidates"] += 1

            score, reason = _score_from_overlap(overlap)

            if score < _MIN_SCORE:
                stats["below_threshold"] += 1
                continue

            hits_to_create.append(
                MatchingHit(
                    user=need.user,
                    need=need,
                    offer=offer,
                    match_score=score,
                    match_reason=reason,
                )
            )

    # --------------------------------------------------------
    # Bulk insert
    #
    # Huge performance improvement compared
    # to calling create() inside loops.
    # --------------------------------------------------------

    if hits_to_create:

        with transaction.atomic():

            created = MatchingHit.objects.bulk_create(
                hits_to_create,
                batch_size=1000,
                ignore_conflicts=True,
            )

            stats["created"] = len(created)

    LOGGER.info(
        "Matching completed: %s",
        stats,
    )

    return stats
