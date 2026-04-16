from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    url: str
    organization_token: str
    offer_type: str
    target_profile: str
    country: str
    domain_names: list[str]
    interval_minutes: int = 360
    llm_fallback_enabled: bool = True
    enabled: bool = True
    quality: str = "real"


@dataclass
class ExtractedPayload:
    title: str
    summary: str
    details: dict = field(default_factory=dict)
    confidence: float = 0.0
    method: str = "deterministic"
