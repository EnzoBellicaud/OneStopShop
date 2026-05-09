import uuid
from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from content.models import (
    Domain,
    Offer,
    OfferDomain,
    OfferType,
    Organization,
    ScrapingRun,
    SourceType,
    TargetProfile,
    User,
)
import ollama
from content.scrapers.extractors import extract_links_from_html
from content.scrapers.ollama_client import OllamaClient
from content.scrapers.service import run_scrape
from content.scrapers.types import ExtractedPayload, SourceDefinition
from content.seeding import uuid_from_token


class ScrapeServiceBehaviorTests(TestCase):
    def setUp(self):
        self.source_type_scraping = SourceType.objects.create(name="scraping", description="")
        self.offer_type = OfferType.objects.create(name="training", description="")
        self.target_profile = TargetProfile.objects.create(name="student", description="")
        self.domain = Domain.objects.create(name="AI")
        self.organization = Organization.objects.create(
            id=uuid_from_token("unibz"),
            name="UNIBZ",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://www.unibz.it",
        )
        self.user = User.objects.create(
            id=uuid.uuid4(),
            username="seed-user",
            email="seed-user@example.com",
            password_hash="not-used",
        )
        self.source = SourceDefinition(
            key="test_source",
            name="Test Source",
            url="https://example.edu/test-source",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
        )

    def _create_offer(self, details: dict) -> Offer:
        offer = Offer.objects.create(
            id=uuid.uuid4(),
            title="Stable Title",
            summary="Stable Summary",
            link=self.source.url,
            country="IT",
            details=details,
            status=Offer.OfferStatus.DRAFT,
            source_type=self.source_type_scraping,
            target_profile=self.target_profile,
            organization=self.organization,
            offer_type=self.offer_type,
            created_by=self.user,
            updated_by=self.user,
        )
        OfferDomain.objects.create(offer=offer, domain=self.domain)
        return offer

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.requests.get")
    def test_http_404_marks_run_failed_and_deletes_invalid_source_offers(self, mock_get, mock_get_sources):
        self._create_offer(
            {
                "source_name": "Test Source",
                "scraping": {
                    "source_key": "test_source",
                    "stale_candidate": False,
                },
            }
        )

        mock_get_sources.return_value = [self.source]
        response = requests.Response()
        response.status_code = 404
        response.url = self.source.url
        mock_get.side_effect = requests.exceptions.HTTPError(
            "404 Client Error: Not Found",
            response=response,
        )

        summary = run_scrape(use_llm_fallback=False)

        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["offers_flagged_stale"], 0)
        self.assertEqual(summary["offers_deleted"], 1)

        run = ScrapingRun.objects.get(source_key="test_source")
        self.assertEqual(run.status, ScrapingRun.RunStatus.FAILED)
        self.assertEqual(run.errors_count, 1)
        self.assertEqual(run.offers_deleted, 1)
        self.assertEqual(run.log[0]["error_type"], "HTTPError")
        self.assertEqual(run.log[0]["http_status"], 404)
        self.assertEqual(run.log[1]["action"], "deleted_invalid_source_offers")
        self.assertEqual(run.log[1]["offers_deleted"], 1)

        self.assertFalse(Offer.objects.filter(link=self.source.url).exists())

    @patch("content.scrapers.service.requests.head")
    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_cleanup_deletes_orphaned_legacy_scraping_offer_with_404_link(
        self,
        mock_get,
        mock_extract,
        mock_get_sources,
        mock_head,
    ):
        orphan_link = "https://example.edu/retired-page"
        self._create_offer(
            {
                "source_name": "Retired Source",
            }
        )
        orphan_offer = Offer.objects.get(link=self.source.url)
        orphan_offer.link = orphan_link
        orphan_offer.save(update_fields=["link", "updated_at"])

        mock_get_sources.return_value = [self.source]

        source_response = Mock()
        source_response.text = "<html><h1>live source</h1></html>"
        source_response.raise_for_status.return_value = None
        source_response.url = self.source.url

        orphan_head_response = Mock()
        orphan_head_response.status_code = 404

        def _get_side_effect(url, **kwargs):
            if url == self.source.url:
                return source_response
            raise AssertionError(f"Unexpected GET: {url}")

        def _head_side_effect(url, **kwargs):
            if url == orphan_link:
                return orphan_head_response
            raise AssertionError(f"Unexpected HEAD: {url}")

        mock_get.side_effect = _get_side_effect
        mock_head.side_effect = _head_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Stable Title",
            summary="Stable Summary",
            details={"source_name": "Test Source", "extra": "stable"},
            confidence=0.9,
            method="deterministic",
        )

        summary = run_scrape(use_llm_fallback=False)

        self.assertEqual(summary["offers_processed"], 1)
        self.assertEqual(summary["errors"], 0)
        self.assertEqual(summary["offers_deleted"], 1)
        self.assertFalse(Offer.objects.filter(link=orphan_link).exists())

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_unchanged_offer_is_counted_as_unchanged_and_freshened(
        self,
        mock_get,
        mock_extract,
        mock_get_sources,
    ):
        self._create_offer(
            {
                "source_name": "Test Source",
                "extra": "stable",
                "scraping": {
                    "managed": True,
                    "source_key": "test_source",
                    "quality": "real",
                    "method": "deterministic",
                    "confidence": 0.9,
                    "last_seen_at": "2020-01-01T00:00:00+00:00",
                    "stale_candidate": True,
                    "stale_reason": "old-flag",
                },
            }
        )

        mock_get_sources.return_value = [self.source]
        mock_response = Mock()
        mock_response.text = "<html><h1>ignored</h1></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        mock_extract.return_value = ExtractedPayload(
            title="Stable Title",
            summary="Stable Summary",
            details={"source_name": "Test Source", "extra": "stable"},
            confidence=0.9,
            method="deterministic",
        )

        summary = run_scrape(use_llm_fallback=False)

        self.assertEqual(summary["offers_processed"], 1)
        self.assertEqual(summary["offers_unchanged"], 1)
        self.assertEqual(summary["offers_updated"], 0)
        self.assertEqual(summary["errors"], 0)

        offer = Offer.objects.get(link=self.source.url)
        scraping = offer.details["scraping"]
        self.assertFalse(scraping["stale_candidate"])
        self.assertNotEqual(scraping["last_seen_at"], "2020-01-01T00:00:00+00:00")

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.requests.get")
    def test_crawl_mode_discovers_and_processes_depth1_links(self, mock_get, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=2,
            crawl_match_patterns=["/offers/"],
            crawl_exclude_patterns=["/offers/skip"],
        )
        mock_get_sources.return_value = [crawl_source]

        root_response = Mock()
        root_response.text = """
        <html><body>
            <a href=\"/offers/a\">A</a>
            <a href=\"https://example.edu/offers/b\">B</a>
            <a href=\"https://example.edu/offers/skip\">Skip</a>
            <a href=\"https://outside.edu/offers/c\">Outside</a>
        </body></html>
        """
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        a_response = Mock()
        a_response.text = "<html><h1>Offer A</h1><p>Summary A</p></html>"
        a_response.raise_for_status.return_value = None
        a_response.url = "https://example.edu/offers/a"

        b_response = Mock()
        b_response.text = "<html><h1>Offer B</h1><p>Summary B</p></html>"
        b_response.raise_for_status.return_value = None
        b_response.url = "https://example.edu/offers/b"

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url == "https://example.edu/offers/a":
                return a_response
            if url == "https://example.edu/offers/b":
                return b_response
            raise AssertionError(f"Unexpected URL requested during crawl: {url}")

        mock_get.side_effect = _request_side_effect

        summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=False)

        self.assertEqual(summary["offers_processed"], 2)
        self.assertEqual(summary["offers_created"], 2)
        self.assertEqual(summary["links_discovered"], 2)
        self.assertEqual(summary["links_skipped"], 2)
        self.assertEqual(summary["links_mapped"], 2)
        self.assertEqual(
            Offer.objects.filter(link__in=["https://example.edu/offers/a", "https://example.edu/offers/b"]).count(),
            2,
        )

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_crawl_mode_neglects_non_offer_pages(self, mock_get, mock_extract, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=1,
            crawl_match_patterns=["/offers/"],
        )
        mock_get_sources.return_value = [crawl_source]

        root_response = Mock()
        root_response.text = "<html><body><a href='/offers/a'>A</a></body></html>"
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        page_response = Mock()
        page_response.text = "<html><body><h1>About our campus</h1><p>General information</p></body></html>"
        page_response.raise_for_status.return_value = None
        page_response.url = "https://example.edu/offers/a"

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url == "https://example.edu/offers/a":
                return page_response
            raise AssertionError(f"Unexpected URL requested: {url}")

        mock_get.side_effect = _request_side_effect
        mock_extract.return_value = ExtractedPayload(
            title=crawl_source.name,
            summary=f"Auto-extracted from https://example.edu/offers/a",
            details={"source_name": crawl_source.name},
            confidence=0.2,
            method="deterministic",
        )

        summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=False)

        self.assertEqual(summary["links_discovered"], 1)
        self.assertEqual(summary["links_mapped"], 0)
        self.assertEqual(summary["offers_created"], 0)
        self.assertFalse(Offer.objects.filter(link="https://example.edu/offers/a").exists())

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_crawl_mode_llm_neglects_navigation_page(self, mock_get, mock_extract, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=1,
            crawl_match_patterns=["/home/"],
        )
        mock_get_sources.return_value = [crawl_source]

        root_response = Mock()
        root_response.text = "<html><body><a href='/home/alumni'>Alumni</a></body></html>"
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        page_response = Mock()
        page_response.text = "<html><body><h1>Alumni Network</h1><p>Connect with graduates.</p></body></html>"
        page_response.raise_for_status.return_value = None
        page_response.url = "https://example.edu/home/alumni"

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url == "https://example.edu/home/alumni":
                return page_response
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = _request_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Alumni Network",
            summary="Connect with graduates.",
            details={},
            confidence=0.85,
            method="deterministic",
        )

        with patch("content.scrapers.service.OllamaClient") as MockOllamaClient:
            mock_ollama = Mock()
            mock_ollama.assess_and_extract.return_value = (False, None, "alumni_page")
            mock_ollama.flush_cooldown_events.return_value = []
            mock_ollama.last_switch_count = 0
            MockOllamaClient.return_value = mock_ollama

            summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=True)

        self.assertEqual(summary["links_discovered"], 1)
        self.assertEqual(summary["links_mapped"], 0)
        self.assertEqual(summary["offers_created"], 0)
        self.assertFalse(Offer.objects.filter(link="https://example.edu/home/alumni").exists())

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_partial_crawl_failures_do_not_flag_existing_offers_stale(self, mock_get, mock_extract, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=3,
            crawl_match_patterns=["/offers/"],
        )
        mock_get_sources.return_value = [crawl_source]

        existing_offer = self._create_offer(
            {
                "source_name": crawl_source.name,
                "scraping": {
                    "managed": True,
                    "source_key": crawl_source.key,
                    "quality": "real",
                    "method": "deterministic",
                    "confidence": 0.9,
                    "last_seen_at": "2020-01-01T00:00:00+00:00",
                    "stale_candidate": False,
                },
            }
        )
        existing_offer.link = "https://example.edu/offers/old"
        existing_offer.save(update_fields=["link", "updated_at"])

        root_response = Mock()
        root_response.text = """
        <html><body>
            <a href='/offers/new'>New</a>
            <a href='/offers/old'>Old</a>
        </body></html>
        """
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        new_response = Mock()
        new_response.text = "<html><h1>New offer</h1><p>A valid summary</p></html>"
        new_response.raise_for_status.return_value = None
        new_response.url = "https://example.edu/offers/new"

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url == "https://example.edu/offers/new":
                return new_response
            if url == "https://example.edu/offers/old":
                raise requests.exceptions.RequestException("temporary fetch failure")
            raise AssertionError(f"Unexpected URL requested: {url}")

        mock_get.side_effect = _request_side_effect

        def _extract_side_effect(html, source):
            return ExtractedPayload(
                title=f"Offer for {source.url}",
                summary="Valid summary",
                details={"source_name": source.name},
                confidence=0.85,
                method="deterministic",
            )

        mock_extract.side_effect = _extract_side_effect

        summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=False)

        self.assertGreater(summary["errors"], 0)
        refreshed_old = Offer.objects.get(link="https://example.edu/offers/old")
        self.assertFalse(refreshed_old.details["scraping"].get("stale_candidate", False))

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_crawl_generic_title_blocked_without_llm(self, mock_get, mock_extract, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=1,
            crawl_match_patterns=["/en/"],
        )
        mock_get_sources.return_value = [crawl_source]

        root_response = Mock()
        root_response.text = "<html><body><a href='/en/contact'>Contact</a></body></html>"
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        contact_response = Mock()
        contact_response.text = "<html><h1>Contact Us</h1><p>Reach us here.</p></html>"
        contact_response.raise_for_status.return_value = None
        contact_response.url = "https://example.edu/en/contact"

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url == "https://example.edu/en/contact":
                return contact_response
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = _request_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Contact Us",
            summary="Reach us here.",
            details={},
            confidence=0.85,
            method="deterministic",
        )

        summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=False)

        self.assertEqual(summary["links_mapped"], 0)
        self.assertEqual(summary["offers_created"], 0)
        self.assertFalse(Offer.objects.filter(link="https://example.edu/en/contact").exists())

    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_crawl_redirect_dedup_creates_single_offer(self, mock_get, mock_extract, mock_get_sources):
        crawl_source = SourceDefinition(
            key="test_crawl_source",
            name="Crawler Source",
            url="https://example.edu/root",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
            crawl_enabled=True,
            crawl_max_pages=5,
            crawl_match_patterns=["/en/"],
        )
        mock_get_sources.return_value = [crawl_source]

        canonical_url = "https://example.edu/en/homepage"

        root_response = Mock()
        root_response.text = (
            "<html><body>"
            "<a href='/en/page-a'>A</a>"
            "<a href='/en/page-b'>B</a>"
            "</body></html>"
        )
        root_response.raise_for_status.return_value = None
        root_response.url = crawl_source.url

        redirect_response = Mock()
        redirect_response.text = "<html><h1>Master Program</h1><p>Full description here.</p></html>"
        redirect_response.raise_for_status.return_value = None
        redirect_response.url = canonical_url

        live_canonical_response = Mock()
        live_canonical_response.status_code = 200
        live_canonical_response.raise_for_status.return_value = None

        def _request_side_effect(url, **kwargs):
            if url == crawl_source.url:
                return root_response
            if url in ("https://example.edu/en/page-a", "https://example.edu/en/page-b"):
                return redirect_response
            if url == canonical_url:
                return live_canonical_response
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = _request_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Master Program",
            summary="Full description here.",
            details={},
            confidence=0.9,
            method="deterministic",
        )

        summary = run_scrape(source_keys=[crawl_source.key], use_llm_fallback=False)

        self.assertEqual(summary["links_discovered"], 2)
        self.assertEqual(summary["links_mapped"], 1)
        self.assertEqual(summary["offers_created"], 1)
        self.assertEqual(Offer.objects.filter(link=canonical_url).count(), 1)


    @patch("content.scrapers.service.requests.head")
    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_cleanup_flags_stale_when_link_returns_5xx(self, mock_get, mock_extract, mock_get_sources, mock_head):
        """Offer whose URL returns 5xx during cleanup gets stale_candidate=True, not deleted."""
        mock_get_sources.return_value = [self.source]

        source_response = Mock()
        source_response.text = "<html><h1>Test Source</h1><p>Summary.</p></html>"
        source_response.raise_for_status.return_value = None
        source_response.url = self.source.url

        stale_link = "https://example.edu/old-broken-page"
        stale_offer = self._create_offer({
            "scraping": {
                "managed": True,
                "source_key": "retired_source_not_in_this_run",
                "stale_candidate": False,
            }
        })
        stale_offer.link = stale_link
        stale_offer.save(update_fields=["link", "updated_at"])

        server_error_response = Mock()
        server_error_response.status_code = 503

        def _get_side_effect(url, **kwargs):
            if url == self.source.url:
                return source_response
            raise AssertionError(f"Unexpected GET: {url}")

        def _head_side_effect(url, **kwargs):
            if url == stale_link:
                return server_error_response
            raise AssertionError(f"Unexpected HEAD: {url}")

        mock_get.side_effect = _get_side_effect
        mock_head.side_effect = _head_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Test Source",
            summary="Summary.",
            details={},
            confidence=0.85,
            method="deterministic",
        )

        summary = run_scrape(use_llm_fallback=False)

        self.assertEqual(summary["offers_deleted"], 0)
        stale_offer.refresh_from_db()
        scraping = stale_offer.details["scraping"]
        self.assertTrue(scraping["stale_candidate"])
        self.assertEqual(scraping["stale_reason"], "url_fetch_error")
        self.assertIn("stale_marked_at", scraping)

    @patch("content.scrapers.service.requests.head")
    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_cleanup_flags_stale_when_link_connection_fails(self, mock_get, mock_extract, mock_get_sources, mock_head):
        """Offer whose URL raises connection error (None status) gets stale_candidate=True after retry."""
        mock_get_sources.return_value = [self.source]

        source_response = Mock()
        source_response.text = "<html><h1>Test Source</h1><p>Summary.</p></html>"
        source_response.raise_for_status.return_value = None
        source_response.url = self.source.url

        stale_link = "https://example.edu/unreachable-page"
        stale_offer = self._create_offer({
            "scraping": {
                "managed": True,
                "source_key": "retired_source_not_in_this_run",
                "stale_candidate": False,
            }
        })
        stale_offer.link = stale_link
        stale_offer.save(update_fields=["link", "updated_at"])

        head_call_counts = {"stale": 0}

        def _get_side_effect(url, **kwargs):
            if url == self.source.url:
                return source_response
            raise AssertionError(f"Unexpected GET: {url}")

        def _head_side_effect(url, **kwargs):
            if url == stale_link:
                head_call_counts["stale"] += 1
                raise requests.exceptions.ConnectionError("unreachable")
            raise AssertionError(f"Unexpected HEAD: {url}")

        mock_get.side_effect = _get_side_effect
        mock_head.side_effect = _head_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Test Source",
            summary="Summary.",
            details={},
            confidence=0.85,
            method="deterministic",
        )

        with patch("content.scrapers.service.time.sleep"):
            summary = run_scrape(use_llm_fallback=False)

        self.assertEqual(head_call_counts["stale"], 2)
        self.assertEqual(summary["offers_deleted"], 0)
        stale_offer.refresh_from_db()
        scraping = stale_offer.details["scraping"]
        self.assertTrue(scraping["stale_candidate"])
        self.assertEqual(scraping["stale_reason"], "url_fetch_error")

    @patch("content.scrapers.service.requests.head")
    @patch("content.scrapers.service.get_sources")
    @patch("content.scrapers.service.extract_deterministic")
    @patch("content.scrapers.service.requests.get")
    def test_cleanup_does_not_double_flag_already_stale_offers(self, mock_get, mock_extract, mock_get_sources, mock_head):
        """Already-stale offer with 5xx link is not re-written (idempotent)."""
        mock_get_sources.return_value = [self.source]

        source_response = Mock()
        source_response.text = "<html><h1>Test Source</h1><p>Summary.</p></html>"
        source_response.raise_for_status.return_value = None
        source_response.url = self.source.url

        stale_link = "https://example.edu/already-stale-page"
        stale_offer = self._create_offer({
            "scraping": {
                "managed": True,
                "source_key": "retired_source_not_in_this_run",
                "stale_candidate": True,
                "stale_reason": "url_fetch_error",
                "stale_marked_at": "2020-01-01T00:00:00+00:00",
            }
        })
        stale_offer.link = stale_link
        stale_offer.save(update_fields=["link", "updated_at"])

        server_error_response = Mock()
        server_error_response.status_code = 500

        def _get_side_effect(url, **kwargs):
            if url == self.source.url:
                return source_response
            raise AssertionError(f"Unexpected GET: {url}")

        def _head_side_effect(url, **kwargs):
            if url == stale_link:
                return server_error_response
            raise AssertionError(f"Unexpected HEAD: {url}")

        mock_get.side_effect = _get_side_effect
        mock_head.side_effect = _head_side_effect
        mock_extract.return_value = ExtractedPayload(
            title="Test Source",
            summary="Summary.",
            details={},
            confidence=0.85,
            method="deterministic",
        )

        summary = run_scrape(use_llm_fallback=False)

        stale_offer.refresh_from_db()
        self.assertEqual(stale_offer.details["scraping"]["stale_marked_at"], "2020-01-01T00:00:00+00:00")


class ScraperUtilityTests(TestCase):
    def test_extract_links_from_html_filters_domain_and_patterns(self):
        html = """
        <html><body>
            <a href=\"/offers/one\">One</a>
            <a href=\"https://example.edu/offers/two?x=1#frag\">Two</a>
            <a href=\"https://example.edu/news/three\">Three</a>
            <a href=\"https://outside.edu/offers/four\">Outside</a>
        </body></html>
        """
        links, skipped = extract_links_from_html(
            html=html,
            seed_url="https://example.edu/root",
            include_patterns=["/offers/"],
            exclude_patterns=["/news/"],
            max_links=10,
        )

        self.assertIn("https://example.edu/offers/one", links)
        self.assertIn("https://example.edu/offers/two?x=1", links)
        self.assertNotIn("https://example.edu/news/three", links)
        self.assertNotIn("https://outside.edu/offers/four", links)
        self.assertEqual(len(links), 2)
        self.assertEqual(skipped, 0)

    @patch("content.scrapers.extractors.LinkExtractor")
    def test_extract_links_from_html_fallback_counts_skipped(self, mock_extractor):
        html = """
        <html><body>
            <a href="/home/one">One</a>
            <a href="/home/two">Two</a>
        </body></html>
        """
        first = Mock()
        first.extract_links.return_value = []
        second = Mock()
        second.extract_links.return_value = [
            Mock(url="https://example.edu/home/one"),
            Mock(url="https://example.edu/home/two"),
        ]
        mock_extractor.side_effect = [first, second]

        links, skipped = extract_links_from_html(
            html=html,
            seed_url="https://example.edu/root",
            include_patterns=["/home/"],
            max_links=1,
        )

        self.assertEqual(links, ["https://example.edu/home/one"])
        self.assertEqual(skipped, 1)

    def test_ollama_client_rotates_model_when_primary_rate_limited(self):
        client = OllamaClient()
        client.model_pool = ["model-primary", "model-secondary"]
        client.model_cooldown_seconds = 60

        success_response = Mock()
        success_response.response = '{"title": "Fallback Title", "summary": "Fallback Summary", "confidence": 0.91}'

        def _generate_side_effect(model, prompt, stream, format):
            if model == "model-primary":
                raise ollama.ResponseError("rate limited", status_code=429)
            return success_response

        mock_inner_client = Mock()
        mock_inner_client.generate.side_effect = _generate_side_effect
        client._client = mock_inner_client

        source = SourceDefinition(
            key="source",
            name="Source",
            url="https://example.edu/offers/a",
            organization_token="unibz",
            offer_type="training",
            target_profile="student",
            country="IT",
            domain_names=["AI"],
        )
        with patch("content.scrapers.ollama_client.time.sleep"):
            payload = client.extract_fallback(
                html="<html><h1>Title</h1></html>",
                source=source,
                deterministic_payload=ExtractedPayload(
                    title="Deterministic",
                    summary="Deterministic summary",
                    details={},
                    confidence=0.2,
                    method="deterministic",
                ),
            )

        self.assertIsNotNone(payload)
        self.assertEqual(payload.title, "Fallback Title")
        self.assertEqual(payload.details["llm"]["model"], "model-secondary")

    def test_available_models_returns_empty_when_all_models_in_cooldown(self):
        from content.scrapers import ollama_client as oc_module
        client = OllamaClient()
        client.model_pool = ["model-a", "model-b"]
        future = 9999999999.0
        original = dict(oc_module._SHARED_MODEL_COOLDOWN)
        oc_module._SHARED_MODEL_COOLDOWN.update({"model-a": future, "model-b": future})
        try:
            self.assertEqual(client._available_models(), [])
        finally:
            oc_module._SHARED_MODEL_COOLDOWN.clear()
            oc_module._SHARED_MODEL_COOLDOWN.update(original)

    def test_is_generic_page_blocks_known_keywords(self):
        from content.scrapers.extractors import is_generic_page

        # Exact matches
        self.assertTrue(is_generic_page("Contact Us"))
        self.assertTrue(is_generic_page("  SEARCH  "))
        self.assertTrue(is_generic_page("Privacy Policy"))
        self.assertTrue(is_generic_page("alumni"))
        self.assertTrue(is_generic_page("Awards"))
        # Composite-title patterns (title - site, title | site, etc.)
        self.assertTrue(is_generic_page("Contact - UNIBZ"))
        self.assertTrue(is_generic_page("Home | MDU"))
        self.assertTrue(is_generic_page("News — University of Mostar"))
        self.assertTrue(is_generic_page("Search · UTC"))
        self.assertTrue(is_generic_page("Events : UNIVPM"))
        # Should NOT block non-generic pages
        self.assertFalse(is_generic_page("Master in Software Engineering"))
        self.assertFalse(is_generic_page("Bachelor in Computer Science"))
        self.assertFalse(is_generic_page("Alumni Network"))
        self.assertFalse(is_generic_page("Embedded Systems Research Group"))
        self.assertFalse(is_generic_page("Research - Embedded Systems Group"))
        self.assertFalse(is_generic_page("PhD Program | Faculty of Engineering"))
