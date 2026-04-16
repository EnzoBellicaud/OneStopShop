import json
import re

from bs4 import BeautifulSoup

from content.scrapers.types import ExtractedPayload, SourceDefinition

WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def _extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    payloads: list[dict] = []
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = node.get_text(strip=True)
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            payloads.append(parsed)
        elif isinstance(parsed, list):
            payloads.extend([item for item in parsed if isinstance(item, dict)])
    return payloads


def extract_deterministic(html: str, source: SourceDefinition) -> ExtractedPayload:
    soup = BeautifulSoup(html, "html.parser")

    page_title = ""
    h1 = soup.find("h1")
    if h1:
        page_title = _normalize_text(h1.get_text(" ", strip=True))

    if not page_title and soup.title and soup.title.string:
        page_title = _normalize_text(soup.title.string)

    meta_description = ""
    description_meta = soup.find("meta", attrs={"name": "description"})
    if description_meta and description_meta.get("content"):
        meta_description = _normalize_text(description_meta["content"])

    if not meta_description:
        og_description = soup.find("meta", attrs={"property": "og:description"})
        if og_description and og_description.get("content"):
            meta_description = _normalize_text(og_description["content"])

    if not meta_description:
        first_paragraph = soup.find("p")
        if first_paragraph:
            meta_description = _normalize_text(first_paragraph.get_text(" ", strip=True))

    json_ld = _extract_json_ld(soup)

    details = {
        "source_url": source.url,
        "source_name": source.name,
        "json_ld_detected": bool(json_ld),
        "json_ld_sample": json_ld[:2],
    }

    confidence = 0.25
    if page_title:
        confidence += 0.35
    if meta_description:
        confidence += 0.25
    if json_ld:
        confidence += 0.15

    title = page_title or source.name
    summary = meta_description or f"Auto-extracted from {source.url}"

    return ExtractedPayload(
        title=title,
        summary=summary,
        details=details,
        confidence=min(confidence, 1.0),
        method="deterministic",
    )
