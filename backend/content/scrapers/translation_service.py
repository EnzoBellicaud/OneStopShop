"""
Lazy translation of offer title/summary into the UI's supported languages.

Translations are produced by the scraper worker (which already has Ollama
access) and cached on ``Offer.details["i18n"]`` so the API can serve them as a
fast pure read with fallback to the original text. Shape:

    details["i18n"] = {
        "source_lang": "en",                       # detected language of the original
        "it": {"title": "...", "summary": "..."},  # cached translations
        "fr": {"title": "...", "summary": "..."},
    }

For the source language we keep no entry — the API serves the original columns.
"""

import logging

from content.models import Offer
from content.scrapers.ollama_client import OllamaClient

LOGGER = logging.getLogger(__name__)

# Must mirror the frontend SUPPORTED_LOCALES (src/i18n/index.js).
SUPPORTED_LANGUAGES = ("en", "it", "fr")


def _missing_languages(offer: Offer) -> list[str]:
    """Target languages that still need a cached translation for this offer."""
    i18n = (offer.details or {}).get("i18n") or {}
    source_lang = i18n.get("source_lang")
    missing = []
    for lang in SUPPORTED_LANGUAGES:
        if source_lang and lang == source_lang:
            continue  # original columns already hold this language
        if lang in i18n:
            continue  # already cached
        missing.append(lang)
    return missing


def offer_needs_translation(offer: Offer) -> bool:
    return bool(_missing_languages(offer))


def translate_offer_record(offer: Offer, client: OllamaClient) -> bool:
    """
    Fill any missing translations for a single offer. Returns True if the offer
    was updated. Stops early (and returns what it has) when the LLM is
    unavailable, so the next worker pass can resume.
    """
    details = dict(offer.details or {})
    i18n = dict(details.get("i18n") or {})
    source_lang = i18n.get("source_lang")
    changed = False

    for lang in _missing_languages(offer):
        # The source language may only become known mid-loop (first call detects
        # it); once known, skip it — the original columns already hold it.
        if source_lang and lang == source_lang:
            continue

        result = client.translate_offer(offer.title, offer.summary, lang)
        if result is None:
            break  # LLM unavailable — resume on a later run

        detected = result.get("source_lang")
        if detected and not source_lang:
            source_lang = detected
            i18n["source_lang"] = source_lang
            changed = True
            if detected == lang:
                # The original is already in this language; serve the columns.
                continue

        i18n[lang] = {"title": result["title"], "summary": result["summary"]}
        changed = True

    if changed:
        details["i18n"] = i18n
        offer.details = details
        offer.save(update_fields=["details"])
    return changed


def run_offer_translation_batch(limit: int = 20) -> dict:
    """
    Translate up to ``limit`` published offers that still need translations.

    Returns a small summary dict for logging.
    """
    client = OllamaClient()
    processed = 0
    updated = 0
    scanned = 0

    queryset = Offer.objects.filter(status=Offer.OfferStatus.PUBLISHED).order_by("updated_at")
    for offer in queryset.iterator():
        scanned += 1
        if not offer_needs_translation(offer):
            continue
        processed += 1
        if translate_offer_record(offer, client):
            updated += 1
        if processed >= limit:
            break

    summary = {"scanned": scanned, "processed": processed, "updated": updated}
    LOGGER.info("Offer translation batch: %s", summary)
    return summary
