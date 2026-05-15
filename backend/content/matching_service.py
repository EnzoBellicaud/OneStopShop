"""
Hybrid matching engine: fast field/keyword filter → LLM scoring.

Entry point: run_matching_for_offers(offer_ids)
Called from UrlScraperService after each scrape batch (Option A).

Flow per (offer, need) pair:
  1. Fast filter  — target_profile, countries, domain, keyword overlap
  2. LLM scoring  — Ollama produces match_score (0-1) + match_reason
  3. Upsert       — create MatchingHit if score >= threshold
"""

import logging
import re
import time

from django.db import IntegrityError

from content.models import MatchingHit, Offer, UserNeed
from content.scrapers.ollama_client import OllamaClient

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
_LLM_MIN_SCORE = 0.40


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def _keyword_overlap(need: UserNeed, offer: Offer) -> int:
    need_words = _tokenize(f"{need.title} {need.description}")
    offer_words = _tokenize(f"{offer.title} {offer.summary}")
    return len(need_words & offer_words)


def _passes_fast_filter(
    need: UserNeed,
    offer: Offer,
    need_domain_ids: set,
    offer_domain_ids: set,
) -> bool:
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


def _keyword_score_fallback(need: UserNeed, offer: Offer) -> tuple[float, str]:
    """Used when Ollama is unavailable — score based on keyword overlap count."""
    overlap = _keyword_overlap(need, offer)
    score = min(0.85, 0.35 + overlap * 0.10)
    reason = f"Matched on {overlap} shared keyword(s) between need and offer (AI scoring unavailable)."
    return round(score, 2), reason


def _llm_score(need: UserNeed, offer: Offer, client: OllamaClient) -> tuple[float, str]:
    prompt = (
        "You are a relevance scoring engine for a university opportunity portal.\n"
        "Given a user need and an academic offer, score how well they match.\n"
        "0.0 = completely irrelevant, 1.0 = perfect match.\n"
        "Return strict JSON only: "
        "{\"match_score\": <float 0.0-1.0>, \"match_reason\": \"<1-2 sentence explanation>\"}\n\n"
        f"User need:\n"
        f"  title: {need.title}\n"
        f"  description: {need.description or '(none)'}\n\n"
        f"Offer:\n"
        f"  title: {offer.title}\n"
        f"  summary: {offer.summary or '(none)'}\n"
        f"  type: {offer.offer_type.name}\n"
        f"  organization: {offer.organization.name}\n"
        f"  country: {offer.country}\n\n"
        "JSON only, no extra text."
    )

    models = client._wait_for_available_model()
    if not models:
        LOGGER.debug("LLM unavailable — falling back to keyword scoring")
        return _keyword_score_fallback(need, offer)

    for model in models:
        try:
            response = client._client.generate(
                model=model, prompt=prompt, stream=False, format="json"
            )
        except Exception as exc:
            LOGGER.warning("LLM match scoring failed (%s): %s", model, exc)
            continue

        parsed = client._parse_response(response.response)
        if not parsed:
            continue

        try:
            score = float(parsed.get("match_score", 0))
            reason = str(parsed.get("match_reason", ""))
        except (TypeError, ValueError):
            continue

        score = max(0.0, min(1.0, score))
        time.sleep(client.request_delay_seconds)
        return score, reason

    LOGGER.warning("All LLM models failed — falling back to keyword scoring")
    return _keyword_score_fallback(need, offer)


def run_matching_for_offers(offer_ids: list) -> dict:
    """
    For each offer in offer_ids, run the hybrid matching pipeline against all
    active user needs and create MatchingHit records for strong matches.
    """
    stats = {"offers": 0, "candidates": 0, "created": 0, "skipped": 0, "below_threshold": 0}

    if not offer_ids:
        return stats

    offers = list(
        Offer.objects.filter(id__in=offer_ids, status=Offer.OfferStatus.PUBLISHED)
        .select_related("offer_type", "organization", "target_profile")
        .prefetch_related("domains")
    )
    if not offers:
        return stats

    active_needs = list(
        UserNeed.objects.filter(status=UserNeed.NeedStatus.ACTIVE)
        .select_related("user", "target_profile")
        .prefetch_related("domains")
    )
    if not active_needs:
        stats["offers"] = len(offers)
        return stats

    # Pre-fetch existing pairs to avoid per-pair DB hits
    existing_pairs = set(
        MatchingHit.objects.filter(
            need__in=active_needs,
            offer__in=offers,
        ).values_list("need_id", "offer_id")
    )

    # Pre-compute domain id sets (uses prefetch cache)
    offer_domain_map = {o.id: {d.id for d in o.domains.all()} for o in offers}
    need_domain_map = {n.id: {d.id for d in n.domains.all()} for n in active_needs}

    client = OllamaClient()
    stats["offers"] = len(offers)

    for offer in offers:
        offer_domains = offer_domain_map[offer.id]
        for need in active_needs:
            if (need.id, offer.id) in existing_pairs:
                stats["skipped"] += 1
                continue

            if not _passes_fast_filter(need, offer, need_domain_map[need.id], offer_domains):
                continue

            stats["candidates"] += 1
            score, reason = _llm_score(need, offer, client)

            if score < _LLM_MIN_SCORE:
                stats["below_threshold"] += 1
                LOGGER.debug(
                    "Below threshold %.2f — need=%s offer=%s", score, need.id, offer.id
                )
                continue

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
                    "MatchingHit created score=%.2f need=%s offer=%s", score, need.id, offer.id
                )
            except IntegrityError:
                stats["skipped"] += 1

    LOGGER.info("Matching complete — %s", stats)
    return stats
