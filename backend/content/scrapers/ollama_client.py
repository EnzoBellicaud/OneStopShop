import datetime
import json
import logging
import os
import re
import time

import ollama

from content.scrapers.types import ExtractedPayload, SourceDefinition

LOGGER = logging.getLogger(__name__)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")

# Shared across all OllamaClient instances within the same process.
# Prevents a model that hit cooldown at the end of run N from being retried
# at the start of run N+1 before the cooldown has expired.
_SHARED_MODEL_COOLDOWN: dict[str, float] = {}

# Buffer for cooldown events emitted during _wait_for_available_model.
# Flushed into run.log by ScrapeService after each LLM call.
_COOLDOWN_LOG_BUFFER: list[dict] = []


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3-coder:480b-cloud")
        model_pool_raw = os.getenv("OLLAMA_MODEL_POOL", "")
        self.model_pool = [item.strip() for item in model_pool_raw.split(",") if item.strip()]
        if not self.model_pool:
            self.model_pool = [self.model]
        # Translation uses a dedicated (typically local, no-cloud-auth) model so
        # it works even when the cloud extraction model needs sign-in.
        self.translation_model = os.getenv("OLLAMA_TRANSLATION_MODEL", "qwen3:4b")
        self.timeout_seconds = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
        self.model_cooldown_seconds = int(os.getenv("OLLAMA_MODEL_COOLDOWN_SECONDS", "60"))
        self.cooldown_max_wait_seconds = int(os.getenv("OLLAMA_COOLDOWN_MAX_WAIT_SECONDS", "65"))
        self.request_delay_seconds = int(os.getenv("OLLAMA_REQUEST_DELAY_SECONDS", "2"))
        self.last_switch_count = 0
        self._client = ollama.Client(host=self.base_url, timeout=self.timeout_seconds)

    def _available_models(self) -> list[str]:
        now = time.time()
        return [
            model
            for model in self.model_pool
            if _SHARED_MODEL_COOLDOWN.get(model, 0) <= now
        ]

    def _wait_for_available_model(self) -> list[str]:
        models = self._available_models()
        if models:
            return models
        if not _SHARED_MODEL_COOLDOWN:
            return []
        soonest = min(_SHARED_MODEL_COOLDOWN.values())
        wait = max(0.0, soonest - time.time())
        if wait > self.cooldown_max_wait_seconds:
            LOGGER.debug(
                "All models in cooldown for %.0fs (max wait %.0fs) — skipping LLM",
                wait, self.cooldown_max_wait_seconds,
            )
            return []
        LOGGER.info("All models in cooldown — waiting %.1fs before retry", wait)
        actual_wait = round(wait + 0.5, 1)
        _COOLDOWN_LOG_BUFFER.append({
            "ts": _utc_now(),
            "event": "cooldown_wait",
            "level": "warn",
            "seconds": actual_wait,
            "message": f"All models in cooldown — waiting {wait:.1f}s before retry",
        })
        time.sleep(actual_wait)
        return self._available_models()

    def flush_cooldown_events(self) -> list[dict]:
        events = list(_COOLDOWN_LOG_BUFFER)
        _COOLDOWN_LOG_BUFFER.clear()
        return events

    def extract_fallback(
        self,
        html: str,
        source: SourceDefinition,
        deterministic_payload: ExtractedPayload,
    ) -> ExtractedPayload | None:
        prompt = self._build_prompt(html, source, deterministic_payload)
        self.last_switch_count = 0

        models = self._wait_for_available_model()
        if not models:
            LOGGER.debug("Ollama fallback skipped for %s: all models in cooldown", source.key)
            return None

        for index, model in enumerate(models):
            try:
                response = self._client.generate(
                    model=model,
                    prompt=prompt,
                    stream=False,
                    format="json",
                )
            except Exception as exc:  # pragma: no cover - depends on local Ollama runtime
                status_code = exc.status_code if isinstance(exc, ollama.ResponseError) else None
                _SHARED_MODEL_COOLDOWN[model] = time.time() + self.model_cooldown_seconds
                if status_code != 429:
                    LOGGER.warning("Ollama fallback unavailable for %s using %s: %s", source.key, model, exc)
                continue

            text = response.response
            parsed = self._parse_response(text)
            if not parsed:
                continue

            title = parsed.get("title") or deterministic_payload.title
            summary = parsed.get("summary") or deterministic_payload.summary
            confidence = parsed.get("confidence", deterministic_payload.confidence)

            self.last_switch_count = index
            LOGGER.info(
                "LLM fallback success — source=%s model=%s conf=%.2f title=%r",
                source.key, model, float(confidence), str(title)[:60],
            )
            llm_details = {
                "llm": {
                    "model": model,
                    "base_url": self.base_url,
                    "used": True,
                }
            }

            merged_details = {**deterministic_payload.details, **llm_details}

            time.sleep(self.request_delay_seconds)
            return ExtractedPayload(
                title=title,
                summary=summary,
                details=merged_details,
                confidence=float(confidence),
                method="llm_fallback",
            )

        return None

    def assess_and_extract(
        self,
        html: str,
        source: SourceDefinition,
        deterministic_payload: ExtractedPayload,
    ) -> tuple[bool, "ExtractedPayload | None", str]:
        """
        Judge relevance and extract offer data in one LLM call.

        Returns (is_relevant, payload, reason).
        When LLM is unavailable returns (True, None, '') — caller falls back to deterministic.
        """
        prompt = self._build_relevance_prompt(html, source, deterministic_payload)
        self.last_switch_count = 0

        models = self._wait_for_available_model()
        if not models:
            LOGGER.debug("Ollama relevance check skipped for %s: all models in cooldown", source.key)
            return True, None, ""

        for index, model in enumerate(models):
            try:
                response = self._client.generate(
                    model=model,
                    prompt=prompt,
                    stream=False,
                    format="json",
                )
            except Exception as exc:  # pragma: no cover - depends on local Ollama runtime
                status_code = exc.status_code if isinstance(exc, ollama.ResponseError) else None
                _SHARED_MODEL_COOLDOWN[model] = time.time() + self.model_cooldown_seconds
                if status_code != 429:
                    LOGGER.warning("Ollama relevance check unavailable for %s using %s: %s", source.key, model, exc)
                continue

            text = response.response
            parsed = self._parse_response(text)
            if not parsed:
                continue

            is_relevant = bool(parsed.get("is_offer", True))
            reason = str(parsed.get("reason", ""))
            title = parsed.get("title") or deterministic_payload.title
            summary = parsed.get("summary") or deterministic_payload.summary
            confidence = float(parsed.get("confidence", deterministic_payload.confidence))
            raw_offer_type = parsed.get("offer_type")
            offer_type = (
                raw_offer_type
                if isinstance(raw_offer_type, str) and raw_offer_type in OllamaClient._valid_offer_type_names()
                else None
            )

            self.last_switch_count = index
            LOGGER.info(
                "LLM assess success — source=%s model=%s is_offer=%s offer_type=%s conf=%.2f reason=%r",
                source.key, model, is_relevant, offer_type or "(will classify)", confidence, reason[:80] if reason else "",
            )
            llm_details = {
                **deterministic_payload.details,
                "llm": {
                    "model": model,
                    "base_url": self.base_url,
                    "used": True,
                },
            }

            extracted = ExtractedPayload(
                title=title,
                summary=summary,
                details=llm_details,
                confidence=confidence,
                method="llm_primary",
                offer_type=offer_type,
            )
            time.sleep(self.request_delay_seconds)
            return is_relevant, extracted, reason

        return True, None, ""

    # Human-readable names for the prompt, keyed by ISO-639-1 code.
    _LANGUAGE_NAMES = {
        "en": "English",
        "it": "Italian",
        "fr": "French",
    }

    def translate_offer(
        self,
        title: str,
        summary: str,
        target_lang: str,
    ) -> dict | None:
        """
        Translate an offer's title and summary into ``target_lang``.

        Returns a dict ``{"title", "summary", "source_lang"}`` on success, or
        ``None`` when the LLM is unavailable (caller keeps the original text).
        ``source_lang`` is the detected ISO-639-1 code of the original text.
        """
        target_name = self._LANGUAGE_NAMES.get(target_lang, target_lang)
        prompt = self._build_translation_prompt(title, summary, target_name)
        model = self.translation_model

        if _SHARED_MODEL_COOLDOWN.get(model, 0) > time.time():
            LOGGER.debug("Ollama translation skipped (target=%s): %s in cooldown", target_lang, model)
            return None

        try:
            # think=False keeps qwen3-style models from spending their output
            # budget on hidden reasoning (which yields an empty JSON response).
            response = self._client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                format="json",
                think=False,
            )
        except Exception as exc:  # pragma: no cover - depends on local Ollama runtime
            status_code = exc.status_code if isinstance(exc, ollama.ResponseError) else None
            _SHARED_MODEL_COOLDOWN[model] = time.time() + self.model_cooldown_seconds
            if status_code != 429:
                LOGGER.warning("Ollama translation unavailable using %s: %s", model, exc)
            return None

        parsed = self._parse_response(response.response)
        if not parsed:
            return None

        translated_title = str(parsed.get("title") or title).strip()
        translated_summary = str(parsed.get("summary") or summary).strip()
        source_lang = str(parsed.get("source_lang") or "").strip().lower()[:2] or None

        time.sleep(self.request_delay_seconds)
        return {
            "title": translated_title,
            "summary": translated_summary,
            "source_lang": source_lang,
        }

    @staticmethod
    def _build_translation_prompt(title: str, summary: str, target_name: str) -> str:
        return (
            "You translate academic opportunity listings. "
            f"Translate the title and summary below into {target_name}. "
            "Preserve meaning, proper nouns, organization names, and any URLs. "
            "If the text is already in the target language, return it unchanged. "
            "Respond with strict JSON only, keys: "
            "source_lang (ISO-639-1 code of the original text), title (string), summary (string). "
            "JSON only, no extra text.\n\n"
            f"Title: {title}\n\n"
            f"Summary: {summary}"
        )

    @staticmethod
    def _build_prompt(
        html: str,
        source: SourceDefinition,
        deterministic_payload: ExtractedPayload,
    ) -> str:
        trimmed_html = html[:14000]
        return (
            "Extract structured offer info as strict JSON with keys: "
            "title, summary, confidence (0..1). "
            "Use the source page and deterministic extraction as hints. "
            f"Source key: {source.key}. "
            f"Source URL: {source.url}. "
            f"Deterministic title: {deterministic_payload.title}. "
            f"Deterministic summary: {deterministic_payload.summary}. "
            "Return JSON only.\n\n"
            f"HTML:\n{trimmed_html}"
        )

    @staticmethod
    def _valid_offer_type_names() -> frozenset[str]:
        from content.scrapers.offer_type_catalog import get_offer_type_catalog
        return frozenset(t["name"] for t in get_offer_type_catalog())

    @staticmethod
    def _build_relevance_prompt(
        html: str,
        source: SourceDefinition,
        deterministic_payload: ExtractedPayload,
    ) -> str:
        from content.scrapers.offer_type_catalog import get_offer_type_catalog
        catalog = get_offer_type_catalog()
        type_lines = "\n".join(
            f"  {t['name']} — {t['description'] or t['name']}"
            for t in catalog
        )
        valid_keys = ", ".join(t["name"] for t in catalog)
        trimmed_html = html[:14000]
        return (
            "You are evaluating a university web page for a One Stop Shop academic offer catalog. "
            "Decide if this page describes a real opportunity, and classify its type precisely:\n"
            f"{type_lines}\n"
            "Mark is_offer=true even for service or infrastructure pages if they describe something a company or researcher could actually use. "
            "Navigation pages, contact pages, alumni pages, donation pages, and generic institutional info are NOT offers. "
            "Respond with strict JSON only, keys: "
            f"is_offer (bool), offer_type (one of: {valid_keys} — omit if is_offer=false), "
            "reason (string, required when is_offer is false), "
            "title (string), summary (string), confidence (0..1). "
            f"Source key: {source.key}. "
            f"Source URL: {source.url}. "
            f"Deterministic title hint: {deterministic_payload.title}. "
            f"Deterministic summary hint: {deterministic_payload.summary}. "
            "JSON only, no extra text.\n\n"
            f"HTML:\n{trimmed_html}"
        )

    @staticmethod
    def _parse_response(text: str) -> dict | None:
        if not text:
            return None

        try:
            direct = json.loads(text)
            if isinstance(direct, dict):
                return direct
        except json.JSONDecodeError:
            pass

        match = JSON_BLOCK_RE.search(text)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None
