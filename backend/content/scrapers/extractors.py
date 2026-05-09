import json
import re
from urllib.parse import urlparse, urlunparse

import trafilatura
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse
from scrapy.linkextractors import LinkExtractor

from content.scrapers.types import ExtractedPayload, SourceDefinition

WHITESPACE_RE = re.compile(r"\s+")

_GENERIC_TITLE_KEYWORDS: frozenset[str] = frozenset({
    # English
    "contact", "contact us", "apply", "application", "applications", "login",
    "sign in", "log in", "search", "cookie", "cookies", "privacy", "privacy policy",
    "imprint", "impressum", "sitemap", "404", "page not found", "error",
    "news", "events", "event", "newsletter", "alumni", "donate", "shop",
    "career", "careers", "jobs", "press", "media", "awards", "recognition",
    "gallery", "map", "campus map", "home", "welcome", "about", "about us",
    "accessibility", "legal notice", "terms", "disclaimer",
    # French
    "recherchez", "recherchez sur le site", "accueil", "actualites", "agenda",
    "nous contacter", "plan du site", "mentions legales",
    # Portuguese / Spanish
    "pesquisa", "inicio", "noticias", "contacto", "contactos", "sobre",
    "mapa do site", "aviso legal", "politica de privacidade",
    # German
    "suche", "startseite", "kontakt", "datenschutz",
    # Italian
    "cerca", "contatti", "notizie",
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


def count_links_in_html(html: str, seed_url: str) -> int:
    scrapy_response = HtmlResponse(
        url=seed_url,
        body=html.encode("utf-8", errors="replace"),
        encoding="utf-8",
    )
    extractor = LinkExtractor(unique=True)
    raw_links = extractor.extract_links(scrapy_response)

    seen: set[str] = set()
    for link in raw_links:
        normalized = _normalize_link(link.url)
        seen.add(normalized)

    return len(seen)


def extract_links_from_html(
    html: str,
    seed_url: str,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    max_links: int = 25,
) -> tuple[list[str], int]:
    """Extract links from HTML using Scrapy's LinkExtractor.

    Patterns are treated as regex substrings matched against the full URL.
    Returns (links, skipped_count) where skipped_count is links beyond max_links.
    """
    seed_host = urlparse(seed_url).netloc.lower()

    scrapy_response = HtmlResponse(
        url=seed_url,
        body=html.encode("utf-8", errors="replace"),
        encoding="utf-8",
    )
    extractor = LinkExtractor(
        allow=include_patterns or [],
        deny=exclude_patterns or [],
        allow_domains=[seed_host],
        unique=True,
    )
    raw_links = extractor.extract_links(scrapy_response)

    seen: set[str] = set()
    links: list[str] = []
    for link in raw_links:
        normalized = _normalize_link(link.url)
        if normalized not in seen:
            seen.add(normalized)
            links.append(normalized)

    if len(links) > max_links:
        skipped = len(links) - max_links
        return links[:max_links], skipped
    return links, 0


def extract_deterministic(html: str, source: SourceDefinition) -> ExtractedPayload:
    soup = BeautifulSoup(html, "html.parser")

    # Title: h1 → trafilatura fallback if h1 is generic → <title> tag
    page_title = ""
    h1 = soup.find("h1")
    if h1:
        page_title = _normalize_text(h1.get_text(" ", strip=True))

    if not page_title or is_generic_page(page_title):
        try:
            traf_meta = trafilatura.extract_metadata(filecontent=html)
            if traf_meta and traf_meta.title:
                candidate = _normalize_text(traf_meta.title)
                if candidate and not is_generic_page(candidate):
                    page_title = candidate
        except Exception:
            pass

    if not page_title and soup.title and soup.title.string:
        page_title = _normalize_text(soup.title.string)

    # Summary: meta description → OG → trafilatura main content → first <p>
    meta_description = ""
    description_meta = soup.find("meta", attrs={"name": "description"})
    if description_meta and description_meta.get("content"):
        meta_description = _normalize_text(description_meta["content"])

    if not meta_description:
        og_description = soup.find("meta", attrs={"property": "og:description"})
        if og_description and og_description.get("content"):
            meta_description = _normalize_text(og_description["content"])

    main_content = ""
    try:
        raw = trafilatura.extract(html, include_comments=False, favor_recall=True) or ""
        main_content = raw.strip()
    except Exception:
        pass

    if not meta_description and main_content:
        meta_description = main_content[:300]

    if not meta_description:
        first_paragraph = soup.find("p")
        if first_paragraph:
            meta_description = _normalize_text(first_paragraph.get_text(" ", strip=True))

    json_ld = _extract_json_ld(soup)

    # Content-aware confidence: rewards pages with real body content
    confidence = 0.25
    if page_title:
        confidence += 0.30
    if meta_description:
        confidence += 0.20
    if json_ld:
        confidence += 0.10
    if len(main_content) > 150:
        confidence += 0.15

    details = {
        "source_url": source.url,
        "source_name": source.name,
        "json_ld_detected": bool(json_ld),
        "json_ld_sample": json_ld[:2],
    }

    title = page_title or source.name
    summary = meta_description or f"Auto-extracted from {source.url}"

    return ExtractedPayload(
        title=title,
        summary=summary,
        details=details,
        confidence=min(confidence, 1.0),
        method="deterministic",
    )
