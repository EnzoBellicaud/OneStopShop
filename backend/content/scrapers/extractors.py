import json
import re
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from content.scrapers.types import ExtractedPayload, SourceDefinition

WHITESPACE_RE = re.compile(r"\s+")

_GENERIC_TITLE_KEYWORDS: frozenset[str] = frozenset({
    "contact", "contact us", "apply", "application", "applications", "login",
    "sign in", "log in", "search", "cookie", "cookies", "privacy", "privacy policy",
    "imprint", "impressum", "sitemap", "404", "page not found", "error",
    "news", "events", "event", "newsletter", "alumni", "donate", "shop",
    "career", "careers", "jobs", "press", "media", "awards", "recognition",
    "gallery", "map", "campus map", "home", "welcome", "about", "about us",
    "accessibility", "legal notice", "terms", "disclaimer",
})


_COMPOSITE_SEPARATORS = (" - ", " | ", " — ", " · ", " : ")


def is_generic_page(title: str) -> bool:
    normalized = WHITESPACE_RE.sub(" ", title).strip().lower()
    if normalized in _GENERIC_TITLE_KEYWORDS:
        return True
    for sep in _COMPOSITE_SEPARATORS:
        if sep in normalized:
            base = normalized.split(sep)[0].strip()
            if base in _GENERIC_TITLE_KEYWORDS:
                return True
    return False


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


def _normalize_link(url: str) -> str:
    parsed = urlparse(url)
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def extract_depth1_links(
    html: str,
    seed_url: str,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    max_links: int = 25,
) -> tuple[list[str], int]:
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    soup = BeautifulSoup(html, "html.parser")
    seed = urlparse(seed_url)
    seed_host = seed.netloc.lower()

    links: list[str] = []
    seen: set[str] = set()
    skipped = 0

    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith("javascript:") or href.startswith("mailto:"):
            skipped += 1
            continue

        absolute = _normalize_link(urljoin(seed_url, href))
        parsed = urlparse(absolute)
        host = parsed.netloc.lower()
        if host != seed_host:
            skipped += 1
            continue

        path = parsed.path or "/"
        if include_patterns and not any(pattern in path for pattern in include_patterns):
            skipped += 1
            continue

        if exclude_patterns and any(pattern in path for pattern in exclude_patterns):
            skipped += 1
            continue

        if absolute in seen:
            continue

        if len(links) >= max_links:
            skipped += 1
            continue

        seen.add(absolute)
        links.append(absolute)

    return links, skipped


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
