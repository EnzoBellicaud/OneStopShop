import logging
import os
import time
from datetime import timedelta
from copy import deepcopy
from dataclasses import replace

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.db.models import Q
from django.utils import timezone

from content.models import (
    Domain,
    Offer,
    OfferDomain,
    OfferType,
    Organization,
    ScrapingJob,
    ScrapingRun,
    SourceType,
    TargetProfile,
    User,
)
from content.scrapers.extractors import count_links_in_html, extract_links_from_html, extract_deterministic, is_generic_page
from content.scrapers.offer_type_classifier import OfferTypeClassifier
from content.scrapers.ollama_client import OllamaClient
from content.scrapers.source_registry import get_sources
from content.scrapers.types import ExtractedPayload, SourceDefinition
from content.seeding import uuid_from_token

_classifier = OfferTypeClassifier()

LOGGER = logging.getLogger(__name__)


def _ts() -> str:
    return timezone.now().isoformat().replace("+00:00", "Z")


class ScrapeService:
    def __init__(
        self,
        source_keys: list[str] | None = None,
        dry_run: bool = False,
        use_llm_fallback: bool = True,
        crawl: bool = False,
    ):
        self.source_keys = source_keys
        self.dry_run = dry_run
        self.use_llm_fallback = use_llm_fallback
        self.crawl = crawl
        self.request_timeout_seconds = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "30"))
        self.user_agent = os.getenv(
            "SCRAPER_USER_AGENT",
            "SUNRISE-OSS-Scraper/1.0 (+https://github.com/EnzoBellicaud/OneStopShop)",
        )
        self.llm_threshold = float(os.getenv("SCRAPER_LLM_FALLBACK_THRESHOLD", "0.60"))
        self.ollama_client = OllamaClient()

    def run(self) -> dict:
        sources = get_sources(self.source_keys)
        if not sources:
            return {
                "sources": 0,
                "offers_processed": 0,
                "offers_created": 0,
                "offers_updated": 0,
                "offers_unchanged": 0,
                "offers_flagged_stale": 0,
                "offers_deleted": 0,
                "errors": 0,
                "llm_calls": 0,
                "urls_neglected": 0,
                "links_discovered": 0,
                "links_skipped": 0,
                "links_mapped": 0,
                "model_switches": 0,
            }

        source_type = SourceType.objects.get(name="scraping")
        ingestion_user = self._get_ingestion_user()

        stats = {
            "sources": 0,
            "offers_processed": 0,
            "offers_created": 0,
            "offers_updated": 0,
            "offers_unchanged": 0,
            "offers_flagged_stale": 0,
            "offers_deleted": 0,
            "errors": 0,
            "llm_calls": 0,
            "urls_neglected": 0,
            "links_discovered": 0,
            "links_skipped": 0,
            "links_mapped": 0,
            "model_switches": 0,
        }
        seen_keys: set[tuple[str, str, str]] = set()
        successful_source_keys: set[str] = set()
        successful_source_urls: set[str] = set()

        for source in sources:
            stats["sources"] += 1
            LOGGER.info("[%s] Starting scrape — %s", source.key, source.url)
            job = self._sync_job(source)
            run = ScrapingRun.objects.create(
                job=job,
                source_key=source.key,
                status=ScrapingRun.RunStatus.RUNNING,
                started_at=timezone.now(),
            )

            try:
                result = self._process_source(source, source_type, ingestion_user)
                run.status = ScrapingRun.RunStatus.SUCCESS
                run.offers_processed = result["offers_processed"]
                run.offers_created = result["offers_created"]
                run.offers_updated = result["offers_updated"]
                run.offers_unchanged = result["offers_unchanged"]
                run.llm_calls_count = result["llm_calls"]
                run.urls_neglected = result["urls_neglected"]
                run.log = result["logs"]

                stats["offers_processed"] += run.offers_processed
                stats["offers_created"] += run.offers_created
                stats["offers_updated"] += run.offers_updated
                stats["offers_unchanged"] += run.offers_unchanged
                stats["llm_calls"] += run.llm_calls_count
                stats["urls_neglected"] += run.urls_neglected
                stats["links_discovered"] += result["links_discovered"]
                stats["links_skipped"] += result["links_skipped"]
                stats["links_mapped"] += result["links_mapped"]
                stats["model_switches"] += result["model_switches"]
                seen_keys.update(result["seen_keys"])
                successful_source_urls.update(result["skip_links"])

                LOGGER.info(
                    "[%s] Done — discovered=%d skipped=%d neglected=%d mapped=%d created=%d updated=%d unchanged=%d llm_calls=%d errors=%d",
                    source.key,
                    result["links_discovered"],
                    result["links_skipped"],
                    result["urls_neglected"],
                    result["links_mapped"],
                    result["offers_created"],
                    result["offers_updated"],
                    result["offers_unchanged"],
                    result["llm_calls"],
                    result["page_errors"],
                )

                page_errors = result["page_errors"]
                if page_errors > 0:
                    stats["errors"] += page_errors
                    run.errors_count = page_errors
                    LOGGER.warning(
                        "Crawl run for %s had %d page fetch failures; skipping stale-marking for this source.",
                        source.key,
                        page_errors,
                    )
                else:
                    successful_source_keys.add(source.key)
            except Exception as exc:  # pragma: no cover - runtime network behavior
                run.status = ScrapingRun.RunStatus.FAILED
                run.errors_count = 1
                run.log = [self._build_error_log(source, exc)]
                stats["errors"] += 1
                if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
                    status_code = exc.response.status_code
                    if status_code in {404, 410}:
                        deleted_count = self._delete_offers_for_invalid_source(source, source_type)
                        run.offers_deleted = deleted_count
                        stats["offers_deleted"] += deleted_count
                        if deleted_count > 0:
                            run.log.append(
                                {
                                    "ts": _ts(),
                                    "event": "url_failed",
                                    "level": "warn",
                                    "source_key": source.key,
                                    "url": source.url,
                                    "http_status": status_code,
                                    "action": "deleted_invalid_source_offers",
                                    "offers_deleted": deleted_count,
                                    "message": f"Deleted {deleted_count} invalid offers (HTTP {status_code})",
                                }
                            )
                        LOGGER.warning(
                            "Scraping source not found for %s (HTTP %s). Deleted %s invalid offers.",
                            source.key,
                            status_code,
                            deleted_count,
                        )
                    else:
                        LOGGER.exception("Scraping failed for %s", source.key)
                else:
                    LOGGER.exception("Scraping failed for %s", source.key)
            finally:
                now = timezone.now()
                run.completed_at = now
                run.save()
                job.last_run_at = now
                job.next_run_at = now + timedelta(minutes=source.interval_minutes)
                job.save(update_fields=["last_run_at", "next_run_at", "updated_at"])

        stale_count = self._flag_stale_candidates(
            sources,
            seen_keys,
            successful_source_keys,
            ingestion_user,
        )
        stats["offers_flagged_stale"] = stale_count

        deleted_invalid_count = self._cleanup_invalid_offer_links(
            source_type,
            skip_links=successful_source_urls,
        )
        stats["offers_deleted"] += deleted_invalid_count

        return stats

    def _get_ingestion_user(self) -> User:
        username = os.getenv("INGESTION_BOT_USERNAME", "ingestion_bot")
        user = User.objects.filter(username=username).first()
        if user:
            return user

        return User.objects.create(
            id=uuid_from_token("user_ingestion_bot"),
            username=username,
            email="ingestion-bot@oss.local",
            password_hash="seeded-not-for-auth",
        )

    def _sync_job(self, source: SourceDefinition) -> ScrapingJob:
        job, _ = ScrapingJob.objects.update_or_create(
            key=source.key,
            defaults={
                "name": source.name,
                "source_domain": self._domain_from_url(source.url),
                "status": ScrapingJob.JobStatus.ACTIVE,
                "is_active": source.enabled,
                "run_interval_minutes": source.interval_minutes,
                "use_llm_fallback": source.llm_fallback_enabled,
            },
        )
        return job

    @staticmethod
    def _domain_from_url(url: str) -> str:
        without_scheme = url.split("//", 1)[-1]
        return without_scheme.split("/", 1)[0]

    def _process_source(self, source: SourceDefinition, source_type: SourceType, ingestion_user: User) -> dict:
        use_crawl = self.crawl or source.crawl_enabled

        if use_crawl:
            try:
                page_urls, links_skipped = self._discover_urls_bfs(source)
            except requests.RequestException as exc:
                raise requests.RequestException(
                    f"Seed URL crawl failed for {source.key}: {exc}"
                ) from exc
        else:
            page_urls = [source.url]
            links_skipped = 0

        LOGGER.info("[%s] mode=%s urls=%d", source.key, "crawl" if use_crawl else "direct", len(page_urls))

        offers_processed = 0
        offers_created = 0
        offers_updated = 0
        offers_unchanged = 0
        llm_calls = 0
        urls_neglected = 0
        model_switches = 0
        links_mapped = 0
        page_errors = 0
        logs: list[dict] = []
        seen_keys: set[tuple[str, str, str]] = set()
        seen_canonical_urls: set[str] = set()
        skip_links: set[str] = set(page_urls if use_crawl else [source.url])

        for page_url in page_urls:
            try:
                html, canonical_url = self._fetch_html_url(page_url)
            except requests.RequestException as exc:
                if not use_crawl:
                    raise
                page_errors += 1
                LOGGER.warning("[%s] Fetch error — %s: %s", source.key, page_url, exc)
                logs.append(
                    {
                        "ts": _ts(),
                        "event": "url_failed",
                        "level": "warn",
                        "source_key": source.key,
                        "url": page_url,
                        "reason": "fetch_error",
                        "message": str(exc),
                    }
                )
                continue

            if use_crawl and canonical_url in seen_canonical_urls:
                LOGGER.debug("[%s] SKIP %s — redirects to already-seen %s", source.key, page_url, canonical_url)
                continue
            if use_crawl:
                seen_canonical_urls.add(canonical_url)

            effective_url = canonical_url if use_crawl else page_url
            page_source = replace(source, url=effective_url)

            extracted = extract_deterministic(html, page_source)

            if use_crawl and is_generic_page(extracted.title):
                urls_neglected += 1
                LOGGER.info("[%s] NEGLECT %s — generic_page_title (%r)", source.key, page_url, extracted.title)
                logs.append(
                    {
                        "ts": _ts(),
                        "event": "url_failed",
                        "level": "info",
                        "source_key": source.key,
                        "url": page_url,
                        "reason": "generic_page_title",
                        "message": f"Generic title: {extracted.title!r}",
                    }
                )
                continue

            if use_crawl:
                # Crawl mode: LLM is the primary relevance + extraction judge.
                if self.use_llm_fallback and source.llm_fallback_enabled:
                    LOGGER.debug("[%s] LLM assessing — %s", source.key, page_url)
                    is_relevant, llm_payload, reason = self.ollama_client.assess_and_extract(
                        html, page_source, extracted
                    )
                    logs.extend(self.ollama_client.flush_cooldown_events())
                    model_switches += self.ollama_client.last_switch_count
                    if llm_payload is not None:
                        llm_calls += 1
                    if not is_relevant:
                        urls_neglected += 1
                        LOGGER.info("[%s] NEGLECT %s — %s", source.key, page_url, reason or "non_relevant_page")
                        logs.append(
                            {
                                "ts": _ts(),
                                "event": "url_failed",
                                "level": "info",
                                "source_key": source.key,
                                "url": page_url,
                                "reason": reason or "non_relevant_page",
                            }
                        )
                        continue
                    if llm_payload is not None and llm_payload.confidence >= extracted.confidence:
                        extracted = llm_payload
                else:
                    # LLM disabled: degraded placeholder gate.
                    if (
                        extracted.title == source.name
                        and extracted.summary.startswith("Auto-extracted from")
                    ):
                        urls_neglected += 1
                        logs.append(
                            {
                                "ts": _ts(),
                                "event": "url_failed",
                                "level": "info",
                                "source_key": source.key,
                                "url": page_url,
                                "reason": "non_relevant_page",
                            }
                        )
                        continue
            else:
                # Non-crawl: LLM as quality fallback only.
                if self.use_llm_fallback and source.llm_fallback_enabled:
                    if extracted.confidence < self.llm_threshold or not extracted.summary or not extracted.title:
                        llm_payload = self.ollama_client.extract_fallback(html, page_source, extracted)
                        logs.extend(self.ollama_client.flush_cooldown_events())
                        if llm_payload is not None:
                            llm_calls += 1
                            model_switches += self.ollama_client.last_switch_count
                            LOGGER.info(
                                "[%s] LLM fallback — conf_before=%.2f conf_after=%.2f adopted=%s",
                                source.key, extracted.confidence, llm_payload.confidence,
                                llm_payload.confidence >= extracted.confidence,
                            )
                            if llm_payload.confidence >= extracted.confidence:
                                extracted = llm_payload

            if not extracted.title and not extracted.summary:
                logs.append(
                    {
                        "ts": _ts(),
                        "event": "url_failed",
                        "level": "warn",
                        "source_key": source.key,
                        "url": page_url,
                        "reason": "missing_core_fields",
                    }
                )
                continue

            action, natural_key, _ = self._upsert_offer(page_source, source_type, ingestion_user, extracted)
            LOGGER.info("[%s] MAP %s — %s (conf=%.2f method=%s)", source.key, action.upper(), page_url, extracted.confidence, extracted.method)
            if action == "skipped":
                continue
            offers_processed += 1
            links_mapped += 1
            offers_created += int(action == "created")
            offers_updated += int(action == "updated")
            offers_unchanged += int(action == "unchanged")
            seen_keys.add(natural_key)
            logs.append(
                {
                    "ts": _ts(),
                    "event": "url_processed",
                    "level": "info",
                    "source_key": source.key,
                    "url": page_url,
                    "method": extracted.method,
                    "confidence": extracted.confidence,
                    "action": action,
                }
            )

        return {
            "offers_processed": offers_processed,
            "offers_created": offers_created,
            "offers_updated": offers_updated,
            "offers_unchanged": offers_unchanged,
            "llm_calls": llm_calls,
            "urls_neglected": urls_neglected,
            "links_discovered": len(page_urls),
            "links_skipped": links_skipped,
            "links_mapped": links_mapped,
            "model_switches": model_switches,
            "page_errors": page_errors,
            "seen_keys": seen_keys,
            "skip_links": skip_links | seen_canonical_urls,
            "logs": logs,
        }

    def _discover_urls_bfs(self, source: SourceDefinition) -> tuple[list[str], int]:
        """BFS crawl up to source.crawl_depth levels from seed URL.

        Returns (discovered_urls, total_skipped).
        Raises requests.RequestException if the seed fetch fails.
        """
        seed_html, seed_canonical = self._fetch_html_url(source.url)

        frontier: list[str] = [seed_canonical]
        visited: set[str] = {seed_canonical}
        discovered: list[str] = []
        total_skipped = 0

        for _ in range(source.crawl_depth):
            if len(discovered) >= source.crawl_max_pages:
                break
            next_frontier: list[str] = []
            for frontier_url in frontier:
                remaining = source.crawl_max_pages - len(discovered)
                if remaining <= 0:
                    break
                try:
                    if frontier_url == seed_canonical:
                        html = seed_html
                    else:
                        html, _ = self._fetch_html_url(frontier_url)
                except requests.RequestException as exc:
                    LOGGER.warning("[%s] BFS fetch error — %s: %s", source.key, frontier_url, exc)
                    total_skipped += 1
                    continue

                links, skipped = extract_links_from_html(
                    html=html,
                    seed_url=frontier_url,
                    include_patterns=source.crawl_match_patterns,
                    exclude_patterns=source.crawl_exclude_patterns,
                    max_links=remaining,
                )
                raw_count = count_links_in_html(html, frontier_url)
                allowed_count = len(links) + skipped
                filtered_out = max(0, raw_count - allowed_count)
                total_skipped += filtered_out + skipped
                for link in links:
                    if link not in visited and len(discovered) < source.crawl_max_pages:
                        visited.add(link)
                        discovered.append(link)
                        next_frontier.append(link)

            frontier = next_frontier
            if not frontier:
                break

        LOGGER.info(
            "[%s] BFS discovery done — depth=%d discovered=%d skipped=%d",
            source.key, source.crawl_depth, len(discovered), total_skipped,
        )
        return discovered, total_skipped

    def _fetch_html_url(self, url: str) -> tuple[str, str]:
        response = requests.get(
            url,
            headers={"User-Agent": self.user_agent, "Accept-Language": "en-US,en;q=0.9"},
            timeout=self.request_timeout_seconds,
            verify=False,
        )
        response.raise_for_status()
        return response.text, response.url

    def _upsert_offer(
        self,
        source: SourceDefinition,
        source_type: SourceType,
        ingestion_user: User,
        extracted: ExtractedPayload,
    ) -> tuple[str, tuple[str, str, str] | None, Offer | None]:
        organization = Organization.objects.get(id=uuid_from_token(source.organization_token))

        resolved_offer_type_name = extracted.offer_type
        if not resolved_offer_type_name:
            classifier_text = f"{extracted.title} {extracted.summary}".strip()
            resolved_offer_type_name, confidence = _classifier.classify(classifier_text)
            if resolved_offer_type_name:
                LOGGER.info(
                    "[%s] TF-IDF classified → %s (score=%.3f)",
                    source.key, resolved_offer_type_name, confidence,
                )
            else:
                LOGGER.info("[%s] No offer type determined — discarding", source.key)
                return "skipped", None, None

        offer_type = OfferType.objects.filter(name=resolved_offer_type_name).first()
        if offer_type is None:
            LOGGER.warning("[%s] offer_type %r not found in DB — discarding", source.key, resolved_offer_type_name)
            return "skipped", None, None
        target_profile = TargetProfile.objects.get(name=source.target_profile)

        natural_key = (source.url, str(organization.id), str(offer_type.id))

        existing = Offer.objects.filter(
            link=source.url,
            organization=organization,
            offer_type=offer_type,
        ).first()

        current_timestamp = timezone.now().isoformat()

        scraping_metadata = {
            "managed": True,
            "source_key": source.key,
            "quality": source.quality,
            "method": extracted.method,
            "confidence": extracted.confidence,
            "last_seen_at": current_timestamp,
            "stale_candidate": False,
        }

        merged_details = {
            **(extracted.details or {}),
            "scraping": scraping_metadata,
        }

        if existing is None:
            if self.dry_run:
                return "created", natural_key, None

            offer = Offer.objects.create(
                title=extracted.title,
                summary=extracted.summary,
                link=source.url,
                country=source.country,
                details=merged_details,
                source_type=source_type,
                target_profile=target_profile,
                organization=organization,
                status=Offer.OfferStatus.DRAFT,
                created_by=ingestion_user,
                updated_by=ingestion_user,
                offer_type=offer_type,
            )
            self._replace_domains(offer, source.domain_names)
            return "created", natural_key, offer

        existing_domain_names = set(existing.domains.values_list("name", flat=True))
        source_domain_names = set(source.domain_names)

        changed = (
            existing.title != extracted.title
            or existing.summary != extracted.summary
            or existing.country != source.country
            or existing.target_profile_id != target_profile.id
            or existing_domain_names != source_domain_names
            or self._normalized_details_for_compare(existing.details)
            != self._normalized_details_for_compare(merged_details)
        )

        if not changed:
            if not self.dry_run:
                existing.details = merged_details
                existing.updated_by = ingestion_user
                existing.save(update_fields=["details", "updated_by", "updated_at"])
            return "unchanged", natural_key, existing

        if self.dry_run:
            return "updated", natural_key, None

        existing.title = extracted.title
        existing.summary = extracted.summary
        existing.country = source.country
        existing.details = merged_details
        existing.source_type = source_type
        existing.target_profile = target_profile
        existing.updated_by = ingestion_user
        existing.save(
            update_fields=[
                "title",
                "summary",
                "country",
                "details",
                "source_type",
                "target_profile",
                "updated_by",
                "updated_at",
            ]
        )
        self._replace_domains(existing, source.domain_names)
        return "updated", natural_key, existing

    def _replace_domains(self, offer: Offer, domain_names: list[str]) -> None:
        domain_map = {
            domain.name: domain
            for domain in Domain.objects.filter(name__in=domain_names)
        }
        OfferDomain.objects.filter(offer=offer).delete()
        OfferDomain.objects.bulk_create(
            [
                OfferDomain(offer=offer, domain=domain_map[name])
                for name in domain_names
                if name in domain_map
            ]
        )

    def _delete_offers_for_invalid_source(self, source: SourceDefinition, source_type: SourceType) -> int:
        offer_queryset = Offer.objects.filter(source_type=source_type).filter(
            Q(details__scraping__source_key=source.key) | Q(link=source.url)
        )
        offer_count = offer_queryset.count()
        if self.dry_run:
            return offer_count
        offer_queryset.delete()
        return offer_count

    def _cleanup_invalid_offer_links(self, source_type: SourceType, skip_links: set[str]) -> int:
        deleted_count = 0
        offers = (
            Offer.objects.filter(source_type=source_type)
            .exclude(link__isnull=True)
            .exclude(link="")
            .only("id", "link", "details")
        )

        for offer in offers.iterator():
            if offer.link in skip_links:
                continue
            status_code = self._fetch_status_code(offer.link)
            if status_code is None:
                time.sleep(2)
                status_code = self._fetch_status_code(offer.link)

            if status_code in {404, 410}:
                deleted_count += 1
                if not self.dry_run:
                    offer.delete()
                    LOGGER.debug("DELETED offer link=%s status=%s", offer.link, status_code)
            elif status_code is None or status_code >= 500:
                if not self.dry_run:
                    details = offer.details or {}
                    scraping = details.get("scraping", {})
                    if not scraping.get("stale_candidate"):
                        scraping["stale_candidate"] = True
                        scraping["stale_marked_at"] = timezone.now().isoformat()
                        scraping["stale_reason"] = "url_fetch_error"
                        details["scraping"] = scraping
                        offer.details = details
                        offer.save(update_fields=["details", "updated_at"])
                        LOGGER.debug("STALE_FLAGGED offer link=%s status=%s", offer.link, status_code)

        LOGGER.info("Link cleanup done — deleted=%d", deleted_count)
        return deleted_count

    def _fetch_status_code(self, url: str) -> int | None:
        headers = {"User-Agent": self.user_agent, "Accept-Language": "en-US,en;q=0.9"}
        kwargs = {"headers": headers, "timeout": self.request_timeout_seconds, "allow_redirects": True, "verify": False}
        try:
            response = requests.head(url, **kwargs)
            if response.status_code == 405:
                response = requests.get(url, **kwargs)
            return response.status_code
        except requests.RequestException:
            return None

    def _flag_stale_candidates(
        self,
        sources: list[SourceDefinition],
        seen_keys: set[tuple[str, str, str]],
        successful_source_keys: set[str],
        ingestion_user: User,
    ) -> int:
        source_keys = {source.key for source in sources}
        stale_count = 0
        LOGGER.info("Flagging stale candidates — sources=%d", len(source_keys))
        for offer in Offer.objects.filter(
            source_type__name="scraping",
            details__scraping__source_key__in=list(source_keys),
        ):
            details = offer.details or {}
            scraping = details.get("scraping")
            if not isinstance(scraping, dict):
                continue
            source_key = scraping.get("source_key")
            if source_key not in successful_source_keys:
                continue

            natural_key = (offer.link, str(offer.organization_id), str(offer.offer_type_id))
            if natural_key in seen_keys:
                continue

            if scraping.get("stale_candidate"):
                continue

            stale_count += 1
            LOGGER.debug("STALE %s — missing from latest fetch (source=%s)", offer.link, source_key)
            if self.dry_run:
                continue

            scraping["stale_candidate"] = True
            scraping["stale_marked_at"] = timezone.now().isoformat()
            scraping["stale_reason"] = "missing_from_latest_source_fetch"
            details["scraping"] = scraping
            offer.details = details
            offer.updated_by = ingestion_user
            offer.save(update_fields=["details", "updated_by", "updated_at"])

        LOGGER.info("Stale flagging done — marked=%d", stale_count)
        return stale_count

    @staticmethod
    def _normalized_details_for_compare(details: dict | None) -> dict:
        if not isinstance(details, dict):
            return {}

        normalized = deepcopy(details)
        scraping = normalized.get("scraping")
        if isinstance(scraping, dict):
            for key in ("last_seen_at", "stale_candidate", "stale_marked_at", "stale_reason"):
                scraping.pop(key, None)
            normalized["scraping"] = scraping
        return normalized

    @staticmethod
    def _build_error_log(source: SourceDefinition, exc: Exception) -> dict:
        entry = {
            "ts": timezone.now().isoformat().replace("+00:00", "Z"),
            "event": "url_failed",
            "level": "error",
            "source_key": source.key,
            "url": source.url,
            "message": str(exc),
            "error_type": exc.__class__.__name__,
        }
        if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
            entry["http_status"] = exc.response.status_code
        return entry


def run_scrape(
    source_keys: list[str] | None = None,
    dry_run: bool = False,
    use_llm_fallback: bool = True,
    crawl: bool = False,
) -> dict:
    service = ScrapeService(
        source_keys=source_keys,
        dry_run=dry_run,
        use_llm_fallback=use_llm_fallback,
        crawl=crawl,
    )
    return service.run()
