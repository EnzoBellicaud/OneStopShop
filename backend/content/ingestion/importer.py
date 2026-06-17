from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from content.matching_triggers import refresh_matches_for_offers
from content.models import (
    CrawlUrl,
    Domain,
    Offer,
    OfferType,
    Organization,
    SourceType,
    TargetProfile,
    User,
)

_VALID_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
_VALID_COUNTRY_RE = re.compile(r"^[A-Za-z]{2}$")
_VALID_PROFILES = {"student", "company", "researcher"}

REQUIRED_COLUMNS = {"url", "offer_type", "organization", "target_profile", "country"}
DOMAIN_COLUMNS = [f"domain_{i}" for i in range(1, 6)]
ALL_COLUMNS = list(REQUIRED_COLUMNS) + ["title", "summary"] + DOMAIN_COLUMNS


def _extract_domains(row: dict) -> list[str]:
    """Read domain_1…domain_5 columns; fall back to legacy comma-separated 'domains' field."""
    values = [row.get(col, "").strip() for col in DOMAIN_COLUMNS]
    result = [v for v in values if v]
    if not result and row.get("domains"):
        result = [d.strip() for d in row["domains"].split(",") if d.strip()]
    return result


@dataclass
class PreviewResult:
    valid: list[dict] = field(default_factory=list)
    invalid: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"valid": self.valid, "invalid": self.invalid}


@dataclass
class ConfirmResult:
    drafts: int = 0
    published: int = 0
    matching: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"drafts": self.drafts, "published": self.published, "matching": self.matching}


class ImportService:
    def preview(self, file_obj, filename: str) -> PreviewResult:
        """Parse and validate file. No DB writes."""
        rows = self._parse(file_obj, filename)

        # Pre-load valid lookup values once for efficiency
        valid_offer_types = set(OfferType.objects.values_list("name", flat=True))
        valid_organizations = {n.lower(): n for n in Organization.objects.values_list("name", flat=True)}
        valid_domains = set(Domain.objects.values_list("name", flat=True))
        file_urls = {row.get("url", "").strip() for row in rows if row.get("url", "").strip()}
        existing_urls = set(Offer.objects.filter(link__in=file_urls).values_list("link", flat=True))

        valid: list[dict] = []
        invalid: list[dict] = []

        for i, row in enumerate(rows, start=2):
            errors, warnings = self._validate(
                row, i, valid_offer_types, valid_organizations, valid_domains, existing_urls
            )
            if errors:
                invalid.append({"row": i, "data": row, "errors": errors})
            else:
                valid.append({"row": i, "data": row, "warnings": warnings})

        return PreviewResult(valid=valid, invalid=invalid)

    def confirm(self, valid_rows: list[dict]) -> ConfirmResult:
        """Write confirmed rows to DB. Each entry carries its own 'status' field."""
        bot_username = getattr(settings, "INGESTION_BOT_USERNAME", "ingestion_bot")
        ingestion_user = User.objects.get(username=bot_username)
        source_type = SourceType.objects.get(name="manual")
        drafts = published = 0
        changed_offer_ids = []

        with transaction.atomic():
            for entry in valid_rows:
                row = entry["data"]
                row_status = entry.get("status", "draft")
                status = Offer.OfferStatus.PUBLISHED if row_status == "published" else Offer.OfferStatus.DRAFT
                offer = self._create_offer(row, status, source_type, ingestion_user)
                changed_offer_ids.append(offer.id)
                self._enqueue_url(offer, row["url"])
                if row_status == "published":
                    published += 1
                    published_offer_ids.append(offer.id)
                else:
                    drafts += 1

            refresh_matches_for_offers(changed_offer_ids)

        return ConfirmResult(drafts=drafts, published=published)

    # ── Private ──────────────────────────────────────────────────────────────

    def _parse(self, file_obj, filename: str) -> list[dict]:
        if filename.lower().endswith(".xlsx"):
            return self._parse_xlsx(file_obj)
        return self._parse_csv(file_obj)

    def _parse_csv(self, file_obj) -> list[dict]:
        text = io.TextIOWrapper(file_obj, encoding="utf-8-sig", errors="replace")
        reader = csv.DictReader(text)
        return [self._normalise_row(row) for row in reader]

    def _parse_xlsx(self, file_obj) -> list[dict]:
        try:
            import openpyxl  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("openpyxl is required for Excel import. Install it with: pip install openpyxl") from exc

        wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip().lower() if h else "" for h in rows[0]]
        result = []
        for row_values in rows[1:]:
            raw = {headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row_values) if i < len(headers)}
            result.append(self._normalise_row(raw))
        return result

    def _normalise_row(self, raw: dict) -> dict:
        return {
            k.strip().lower(): (v.strip() if isinstance(v, str) else v or "")
            for k, v in raw.items()
            if k is not None
        }

    def _validate(
        self,
        row: dict,
        row_num: int,
        valid_offer_types: set,
        valid_organizations: dict,
        valid_domains: set,
        existing_urls: set,
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []

        # Required field presence
        for col in REQUIRED_COLUMNS:
            if not row.get(col):
                errors.append(f"Missing required field: {col}")

        if errors:
            return errors, warnings

        # URL
        url = row["url"]
        if not _VALID_URL_RE.match(url):
            errors.append(f"Invalid URL: {url!r}")

        # offer_type
        if row["offer_type"].lower() not in {ot.lower() for ot in valid_offer_types}:
            errors.append(
                f"Unknown offer_type {row['offer_type']!r}. Valid: {', '.join(sorted(valid_offer_types))}"
            )

        # organization
        if row["organization"].lower() not in valid_organizations:
            errors.append(
                f"Unknown organization {row['organization']!r}. "
                f"Valid: {', '.join(sorted(valid_organizations.values()))}"
            )

        # target_profile
        if row["target_profile"].lower() not in _VALID_PROFILES:
            errors.append(
                f"Invalid target_profile {row['target_profile']!r}. Valid: {', '.join(sorted(_VALID_PROFILES))}"
            )

        # country
        if not _VALID_COUNTRY_RE.match(row["country"]):
            errors.append(f"Invalid country {row['country']!r}. Must be 2-letter ISO code (e.g. IT, SE)")

        if errors:
            return errors, warnings

        # Warnings (non-blocking)
        if url in existing_urls:
            warnings.append(f"URL already exists in system: {url}")

        for d in _extract_domains(row):
            if d not in valid_domains:
                warnings.append(f"Unknown domain {d!r} — will be skipped")

        return errors, warnings

    def _create_offer(self, row: dict, status: str, source_type: SourceType, ingestion_user: User) -> Offer:
        org = Organization.objects.get(name__iexact=row["organization"])
        offer_type = OfferType.objects.get(name__iexact=row["offer_type"])
        target_profile = TargetProfile.objects.get(name__iexact=row["target_profile"])

        offer, created = Offer.objects.get_or_create(
            link=row["url"],
            organization=org,
            offer_type=offer_type,
            defaults={
                "title": row.get("title") or "",
                "summary": row.get("summary") or "",
                "country": row["country"].upper(),
                "target_profile": target_profile,
                "source_type": source_type,
                "status": status,
                "created_by": ingestion_user,
                "updated_by": ingestion_user,
            },
        )
        if not created:
            offer.title = row.get("title") or offer.title
            offer.summary = row.get("summary") or offer.summary
            offer.country = row["country"].upper()
            offer.target_profile = target_profile
            offer.source_type = source_type
            offer.status = status
            offer.updated_by = ingestion_user
            offer.save(update_fields=[
                "title", "summary", "country", "target_profile",
                "source_type", "status", "updated_by", "updated_at",
            ])

        domain_names = _extract_domains(row)
        if domain_names:
            offer.domains.set(Domain.objects.filter(name__in=domain_names))

        return offer

    def _enqueue_url(self, offer: Offer, url: str) -> None:
        source_key = f"import__{offer.organization_id}"
        crawl_url, created = CrawlUrl.objects.get_or_create(
            source_key=source_key,
            url=url,
            defaults={
                "status": CrawlUrl.UrlStatus.PENDING,
                "next_check_at": timezone.now(),
                "offer": offer,
            },
        )
        if not created and crawl_url.offer_id != offer.pk:
            crawl_url.offer = offer
            crawl_url.save(update_fields=["offer", "updated_at"])
