import json
import logging
import os
import re

import requests

from content.scrapers.types import ExtractedPayload, SourceDefinition

LOGGER = logging.getLogger(__name__)
JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3-coder:480b-cloud")
        self.timeout_seconds = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))

    def extract_fallback(
        self,
        html: str,
        source: SourceDefinition,
        deterministic_payload: ExtractedPayload,
    ) -> ExtractedPayload | None:
        prompt = self._build_prompt(html, source, deterministic_payload)
        url = f"{self.base_url.rstrip('/')}/api/generate"

        try:
            response = requests.post(
                url,
                json={
                    "model": self.model,
                    "stream": False,
                    "format": "json",
                    "prompt": prompt,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # pragma: no cover - depends on local Ollama runtime
            LOGGER.warning("Ollama fallback unavailable for %s: %s", source.key, exc)
            return None

        text = payload.get("response", "")
        parsed = self._parse_response(text)
        if not parsed:
            return None

        title = parsed.get("title") or deterministic_payload.title
        summary = parsed.get("summary") or deterministic_payload.summary
        confidence = parsed.get("confidence", deterministic_payload.confidence)

        llm_details = {
            "llm": {
                "model": self.model,
                "base_url": self.base_url,
                "used": True,
            }
        }

        merged_details = {**deterministic_payload.details, **llm_details}

        return ExtractedPayload(
            title=title,
            summary=summary,
            details=merged_details,
            confidence=float(confidence),
            method="llm_fallback",
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
