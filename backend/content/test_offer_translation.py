"""Tests for lazy offer translation caching and language-aware serialization."""

from django.test import RequestFactory, TestCase

from content.models import (
    Offer,
    OfferType,
    Organization,
    SourceType,
    TargetProfile,
    User,
)
from content.scrapers.translation_service import (
    _missing_languages,
    offer_needs_translation,
    translate_offer_record,
)
from content.views.offers import _offer_to_dict, _resolve_lang


class FakeClient:
    """Stand-in for OllamaClient that records calls and returns canned data."""

    def __init__(self, source_lang="en", available=True):
        self.source_lang = source_lang
        self.available = available
        self.calls = []

    def translate_offer(self, title, summary, target_lang):
        self.calls.append(target_lang)
        if not self.available:
            return None
        return {
            "title": f"[{target_lang}] {title}",
            "summary": f"[{target_lang}] {summary}",
            "source_lang": self.source_lang,
        }


def _make_offer(**overrides):
    target_profile = TargetProfile.objects.create(name="student")
    source_type = SourceType.objects.create(name="manual")
    offer_type = OfferType.objects.create(name="course")
    organization = Organization.objects.create(
        name="Test University",
        type=Organization.OrganizationType.UNIVERSITY,
        country="IT",
        website="https://test.edu",
    )
    user = User.objects.create(username="u", email="u@e.com", password_hash="h")
    defaults = dict(
        title="Original title",
        summary="Original summary",
        link="https://test.edu/x",
        country="IT",
        offer_type=offer_type,
        organization=organization,
        source_type=source_type,
        target_profile=target_profile,
        created_by=user,
        updated_by=user,
        status=Offer.OfferStatus.PUBLISHED,
    )
    defaults.update(overrides)
    return Offer.objects.create(**defaults)


class ResolveLangTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_query_param_wins(self):
        req = self.rf.get("/api/offers", {"lang": "it"})
        self.assertEqual(_resolve_lang(req), "it")

    def test_unsupported_query_param_ignored(self):
        req = self.rf.get("/api/offers", {"lang": "de"})
        self.assertIsNone(_resolve_lang(req))

    def test_accept_language_fallback(self):
        req = self.rf.get("/api/offers", HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9")
        self.assertEqual(_resolve_lang(req), "fr")

    def test_no_language(self):
        req = self.rf.get("/api/offers")
        self.assertIsNone(_resolve_lang(req))


class OfferToDictTranslationTests(TestCase):
    def test_serves_cached_translation(self):
        offer = _make_offer(details={"i18n": {"it": {"title": "Titolo", "summary": "Sommario"}}})
        data = _offer_to_dict(offer, "it")
        self.assertEqual(data["title"], "Titolo")
        self.assertEqual(data["summary"], "Sommario")

    def test_falls_back_to_original_when_missing(self):
        offer = _make_offer(details={"i18n": {"it": {"title": "Titolo", "summary": "Sommario"}}})
        data = _offer_to_dict(offer, "fr")  # no French cached
        self.assertEqual(data["title"], "Original title")
        self.assertEqual(data["summary"], "Original summary")

    def test_no_lang_returns_original(self):
        offer = _make_offer(details={"i18n": {"it": {"title": "Titolo", "summary": "Sommario"}}})
        data = _offer_to_dict(offer, None)
        self.assertEqual(data["title"], "Original title")


class TranslateRecordTests(TestCase):
    def test_fills_missing_and_skips_source_language(self):
        offer = _make_offer()  # source detected as "en"
        client = FakeClient(source_lang="en")

        changed = translate_offer_record(offer, client)

        self.assertTrue(changed)
        offer.refresh_from_db()
        i18n = offer.details["i18n"]
        self.assertEqual(i18n["source_lang"], "en")
        # it + fr cached, en skipped (it's the source → serve original columns)
        self.assertIn("it", i18n)
        self.assertIn("fr", i18n)
        self.assertNotIn("en", i18n)
        self.assertEqual(i18n["it"]["title"], "[it] Original title")
        # The first call detects the source language ("en"); it is then skipped
        # from caching since the original columns already hold English.
        self.assertNotIn("en", i18n)

    def test_idempotent_no_calls_when_complete(self):
        offer = _make_offer()
        translate_offer_record(offer, FakeClient(source_lang="en"))
        offer.refresh_from_db()

        self.assertFalse(offer_needs_translation(offer))
        second = FakeClient(source_lang="en")
        changed = translate_offer_record(offer, second)
        self.assertFalse(changed)
        self.assertEqual(second.calls, [])

    def test_unavailable_llm_leaves_offer_untouched(self):
        offer = _make_offer()
        changed = translate_offer_record(offer, FakeClient(available=False))
        self.assertFalse(changed)
        offer.refresh_from_db()
        self.assertNotIn("i18n", offer.details)

    def test_non_supported_source_translates_all(self):
        offer = _make_offer(title="Svensk titel", summary="Sammanfattning")
        client = FakeClient(source_lang="sv")
        translate_offer_record(offer, client)
        offer.refresh_from_db()
        i18n = offer.details["i18n"]
        self.assertEqual(i18n["source_lang"], "sv")
        # All three supported languages get cached (none equals source "sv")
        self.assertEqual(set(client.calls), {"en", "it", "fr"})
        self.assertIn("en", i18n)


class MissingLanguagesTests(TestCase):
    def test_missing_when_empty(self):
        offer = _make_offer()
        self.assertEqual(set(_missing_languages(offer)), {"en", "it", "fr"})

    def test_source_language_excluded(self):
        offer = _make_offer(details={"i18n": {"source_lang": "en", "it": {"title": "a", "summary": "b"}}})
        self.assertEqual(_missing_languages(offer), ["fr"])
