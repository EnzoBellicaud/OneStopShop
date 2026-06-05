from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    url: str
    organization_token: str
    target_profile: str
    country: str
    domain_names: list[str]
    interval_minutes: int = 360
    llm_fallback_enabled: bool = True
    enabled: bool = True
    quality: str = "real"
    crawl_enabled: bool = False
    crawl_depth: int = 1
    crawl_max_pages: int = 25
    crawl_match_patterns: list[str] = field(default_factory=list)
    crawl_exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class ExtractedPayload:
    title: str
    summary: str
    details: dict = field(default_factory=dict)
    confidence: float = 0.0
    method: str = "deterministic"
    offer_type: str | None = None  # set by LLM; None means use source default


@dataclass
class PageDecision:
    page_url: str
    decision: str
    reason: str
    payload: ExtractedPayload | None = None
