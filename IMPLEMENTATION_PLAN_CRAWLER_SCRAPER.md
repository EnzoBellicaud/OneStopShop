# Crawler + Scraper Decision Engine Implementation Plan

Status: In Progress  
Date: 2026-04-23  
Branch: feature/crawler-queue-decision-v1

## Objective
Implement a crawler-first ingestion flow where:
1. The crawler discovers and queues candidate pages.
2. The scraper decides per page: neglect or map.
3. Mapped pages are normalized and upserted consistently across partner university sites.
4. LLM fallback uses a model pool to reduce rate-limit failures.

## Architecture Lock
1. Crawler is queue-only. No mapping/business decision in crawler stage.
2. Scraper owns all page-level decisions and mapping rules.
3. Existing upsert behavior remains the source of truth.
4. All ingested items remain draft.
5. Keep implementation incremental and test-first.

## Current Snapshot
### Environment
1. Docker stack is running and healthy.
2. Services up: oss-api, oss-postgres (healthy), oss-scraper-worker.

### Validation already done
1. content.test_scraper_service: 6 tests passed.
2. content app suite: 26 tests passed.

### Files already modified
1. [README.md](README.md)
2. [backend/content/management/commands/run_scrape_once.py](backend/content/management/commands/run_scrape_once.py)
3. [backend/content/scrapers/extractors.py](backend/content/scrapers/extractors.py)
4. [backend/content/scrapers/ollama_client.py](backend/content/scrapers/ollama_client.py)
5. [backend/content/scrapers/service.py](backend/content/scrapers/service.py)
6. [backend/content/scrapers/source_registry.py](backend/content/scrapers/source_registry.py)
7. [backend/content/scrapers/types.py](backend/content/scrapers/types.py)
8. [backend/content/test_scraper_service.py](backend/content/test_scraper_service.py)

## What Is Implemented So Far
1. Crawl mode flag added to one-shot command.
2. Depth-1 link extraction added with include/exclude filtering and same-domain checks.
3. Source definition extended with crawl control fields.
4. Initial crawler queue flow integrated into scraper service.
5. Ollama model pool rotation added with cooldown handling (all-cooldown returns `[]` — host GREEN, container needs rebuild).
6. Partner seed entries added for all 9 universities (disabled by default).
7. Initial tests for crawl extraction and model rotation added.
8. Three RED tests added (waiting for GREEN implementation):
   - `test_crawl_mode_neglects_non_offer_pages` (Phase A).
   - `test_partial_crawl_failures_do_not_flag_existing_offers_stale` (Phase B).
   - `test_available_models_returns_empty_when_all_models_in_cooldown` (Phase C — host code correct, container stale; run `docker compose up -d --build`).

## Next Session Start Point
Run `docker compose up -d --build && docker compose exec api python manage.py test content.test_scraper_service` — confirm 3 failures above, then GREEN Phase A, then Phase B. Phase C should pass after rebuild.

### Phase A GREEN hint
In `_process_source` (service.py around line 269), add relevance gate BEFORE upsert:
- If `extracted.title == source.name` AND `extracted.summary.startswith("Auto-extracted from")` AND `extracted.confidence < self.llm_threshold` → append neglect log with `reason: "non_relevant_page"` and `continue`.
- Also add reason codes: `missing_core_fields` (already exists), `non_relevant_page`, `duplicate_url`, `blocked_pattern`, `unsupported_language` (add as needed).

### Phase B GREEN hint
- Add `page_errors` counter in `_process_source` return dict. Increment when crawl-mode `RequestException` is caught.
- In main `run()` loop: if `result["page_errors"] > 0`, increment `stats["errors"]`, mark run status as SUCCESS with error count (or add a PARTIAL status), AND DO NOT add source.key to `successful_source_keys` (so `_flag_stale_candidates` skips this source).

## Remaining Work (Authoritative Backlog)

## Phase A: Decision Quality Gate (Highest Priority)
Goal: Prevent non-offer pages from being mapped as offers.

Tasks:
1. Add explicit relevance gate before upsert in [backend/content/scrapers/service.py](backend/content/scrapers/service.py).
2. Use decision states consistently: neglect or map.
3. Add reason codes for neglect (non_relevant_page, missing_core_fields, duplicate_url, blocked_pattern, unsupported_language).
4. Require minimum confidence and content-derived fields before map path.
5. Ensure placeholder title/summary fallback does not auto-qualify pages.

Tests to add/update:
1. Negative test: navigation/info page must be neglected.
2. Positive test: valid offer-like page is mapped.
3. Regression: existing non-crawl single-source behavior unchanged.

Definition of done:
1. No unconditional mapping for crawl pages.
2. Decision reason is always recorded.

## Phase B: Stale-Marking Safety on Partial Crawl Failures (High Priority)
Goal: Avoid stale-flagging due to transient crawl errors.

Tasks:
1. Track page-level fetch failures per source run in [backend/content/scrapers/service.py](backend/content/scrapers/service.py).
2. If crawl run has page fetch failures, do not treat source as fully successful for stale-marking.
3. Mark run as partial where relevant and log this explicitly.

Tests to add/update:
1. Crawl with one failing page should not stale-flag unaffected existing offers.
2. Full success crawl still allows stale-marking behavior.

Definition of done:
1. Transient crawl errors do not produce false stale candidates.

## Phase C: Model Cooldown Hardening (Medium Priority)
Goal: Avoid model-thrashing when all models are cooling down.

Tasks:
1. If all models are in cooldown, return None cleanly and log a single event in [backend/content/scrapers/ollama_client.py](backend/content/scrapers/ollama_client.py).
2. Do not immediately re-hit models still in cooldown.
3. Keep deterministic fallback path operational.

Tests to add/update:
1. All-model-cooldown scenario should not loop or thrash.
2. Rotation resumes once cooldown expires.

Definition of done:
1. No repeated immediate retries against cooled-down models.

## Phase D: Crawl Controls Consistency (Medium Priority)
Goal: Ensure new config fields either work or are explicitly deferred.

Tasks:
1. Either implement crawl_delay_ms behavior in [backend/content/scrapers/service.py](backend/content/scrapers/service.py) or remove/defer field from [backend/content/scrapers/types.py](backend/content/scrapers/types.py).
2. Either implement mapping_profile routing behavior or remove/defer for v1.
3. Keep configuration semantics truthful and minimal.

Tests to add/update:
1. If delay is implemented, test request pacing behavior.
2. If not implemented, remove field-related assumptions from tests/docs.

Definition of done:
1. No dead configuration fields in active v1 contract.

## Phase E: Telemetry and API Contract Stabilization
Goal: Keep counters useful and backward compatible.

Tasks:
1. Confirm run log/counters are coherent in [backend/content/scrapers/service.py](backend/content/scrapers/service.py).
2. Ensure scraping run API responses remain compatible in [backend/content/views.py](backend/content/views.py).
3. Add/adjust API tests in [backend/content/tests.py](backend/content/tests.py).

Definition of done:
1. Existing consumers of scraping runs do not break.
2. New counters are present and accurate.

## Phase F: Seed Rollout Procedure
Goal: Roll out safely across 9 sources.

Tasks:
1. Keep all crawler seeds disabled by default in [backend/content/scrapers/source_registry.py](backend/content/scrapers/source_registry.py).
2. Pilot enable 2 sources only.
3. Validate decision quality and telemetry.
4. Expand gradually to remaining 7 sources.

Definition of done:
1. Pilot runs stable before broader enablement.

## Phase G: Documentation and Operator Runbook
Goal: Make execution/recovery clear for handoff.

Tasks:
1. Finalize command examples in [README.md](README.md).
2. Document model-pool env variables and expected behavior.
3. Add troubleshooting note for Docker API compatibility mismatch on Windows.

Definition of done:
1. Another engineer can run, validate, and troubleshoot without chat context.

## TDD Execution Rules for Remaining Work
1. For each phase, add or update tests first (RED).
2. Implement minimal code to pass (GREEN).
3. Refactor only after green tests.
4. Validate in containerized environment.

## Run and Verify Commands
From repo root:

1. docker compose up -d --build
2. docker compose ps
3. docker compose exec api python manage.py test content.test_scraper_service
4. docker compose exec api python manage.py test content
5. Invoke-RestMethod -Uri "http://localhost:8000/api/health"

Optional crawl run:
1. docker compose exec api python manage.py run_scrape_once --crawl --source-key unibz_crawler_seed

## Resume Checklist (If Work Stops)
1. Confirm branch: feature/crawler-queue-decision-v1
2. Rebuild containers and verify health endpoint.
3. Continue from Phase A first.
4. Keep each phase test-backed before moving on.

## Acceptance Criteria for This Story
1. Crawler queues only depth-1 same-domain eligible links.
2. Scraper emits explicit decision (neglect or map) per queued page.
3. Non-relevant pages are neglected with reason code.
4. Mapped pages pass canonical validation before upsert.
5. Partial crawl failures do not create false stale flags.
6. Model-pool fallback handles rate limits without thrashing.
7. Content tests stay green in Docker.

## Partner University Seed URLs
1. https://www.tu-ilmenau.de/
2. https://www.unibz.it/
3. https://www.uitm.edu.eu/
4. https://www.utc.fr/
5. https://www.euc.ac.cy/
6. https://www.mdu.se/
7. https://www.univpm.it/
8. https://www.unmo.ba/
9. https://www.ipvc.pt/

## Notes
This file is the single resume source for implementation status and next actions.