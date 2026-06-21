from __future__ import annotations

from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Prefetch

from content.models import Contact, ContactRole, Offer, OfferContact

PRIMARY_CONTACT_LABEL = "primary_contact"
DEFAULT_CONTACT_ROLE = "general_contact"
PRIMARY_CONTACT_PREFETCH_ATTR = "prefetched_primary_offer_contacts"
validate_url = URLValidator()


def primary_offer_contact_prefetch() -> Prefetch:
    return Prefetch(
        "offercontact_set",
        queryset=(
            OfferContact.objects.select_related("contact")
            .filter(role_label=PRIMARY_CONTACT_LABEL)
            .order_by("contact__contact_name", "id")
        ),
        to_attr=PRIMARY_CONTACT_PREFETCH_ATTR,
    )


def serialize_offer_contact(link: OfferContact | None) -> dict | None:
    if link is None:
        return None

    contact = link.contact
    return {
        "contact_id": str(contact.id),
        "role_label": link.role_label,
        "name": contact.contact_name,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin": contact.linkedin,
    }


def get_primary_offer_contact_link(offer: Offer) -> OfferContact | None:
    if hasattr(offer, PRIMARY_CONTACT_PREFETCH_ATTR):
        links = getattr(offer, PRIMARY_CONTACT_PREFETCH_ATTR)
        return links[0] if links else None

    if hasattr(offer, "prefetched_offer_contacts"):
        return next(
            (
                link
                for link in getattr(offer, "prefetched_offer_contacts")
                if link.role_label == PRIMARY_CONTACT_LABEL
            ),
            None,
        )

    return (
        OfferContact.objects.select_related("contact")
        .filter(offer=offer, role_label=PRIMARY_CONTACT_LABEL)
        .order_by("contact__contact_name", "id")
        .first()
    )


def serialize_primary_contact(offer: Offer) -> dict | None:
    return serialize_offer_contact(get_primary_offer_contact_link(offer))


def sync_primary_contact(offer: Offer, payload) -> OfferContact | None:
    if payload is None:
        remove_primary_contact(offer)
        return None
    if not isinstance(payload, dict):
        raise ValueError("contact must be an object or null.")

    name = str(payload.get("name") or payload.get("contact_name") or "").strip()
    email = _clean_optional(payload.get("email"))
    phone = _clean_optional(payload.get("phone"))
    linkedin = _clean_linkedin_url(payload.get("linkedin"))

    if not name:
        raise ValueError("contact.name is required.")
    if not email and not phone:
        raise ValueError("contact.email or contact.phone is required.")

    link = get_primary_offer_contact_link(offer)
    if link is None:
        contact = _find_or_create_contact(
            offer=offer,
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            payload=payload,
        )
        return OfferContact.objects.create(
            offer=offer,
            contact=contact,
            role_label=PRIMARY_CONTACT_LABEL,
        )

    contact = link.contact
    contact.contact_name = name
    contact.email = email
    contact.phone = phone
    contact.linkedin = linkedin
    contact.role = _resolve_contact_role(payload)
    contact.organization = offer.organization
    contact.save(
        update_fields=[
            "contact_name",
            "email",
            "phone",
            "linkedin",
            "role",
            "organization",
            "updated_at",
        ]
    )
    return link


def remove_primary_contact(offer: Offer) -> None:
    links = list(
        OfferContact.objects.select_related("contact").filter(
            offer=offer,
            role_label=PRIMARY_CONTACT_LABEL,
        )
    )
    _delete_links_and_orphaned_contacts(links)


def remove_offer_contacts(offer: Offer) -> None:
    links = list(OfferContact.objects.select_related("contact").filter(offer=offer))
    _delete_links_and_orphaned_contacts(links)


def _find_or_create_contact(
    *,
    offer: Offer,
    name: str,
    email: str | None,
    phone: str | None,
    linkedin: str | None,
    payload: dict,
) -> Contact:
    role = _resolve_contact_role(payload)
    if email:
        contact = (
            Contact.objects.filter(email__iexact=email, organization=offer.organization)
            .order_by("contact_name")
            .first()
        )
        if contact:
            contact.contact_name = name
            contact.phone = phone
            contact.linkedin = linkedin
            contact.role = role
            contact.save(
                update_fields=[
                    "contact_name",
                    "phone",
                    "linkedin",
                    "role",
                    "updated_at",
                ]
            )
            return contact

    return Contact.objects.create(
        contact_name=name,
        email=email,
        phone=phone,
        linkedin=linkedin,
        role=role,
        organization=offer.organization,
    )


def _resolve_contact_role(payload: dict) -> ContactRole:
    role_id = payload.get("role_id") or payload.get("contact_role_id")
    if role_id:
        try:
            parsed_role_id = UUID(str(role_id))
        except ValueError as exc:
            raise ValueError("contact.role_id must be a valid UUID.") from exc
        role = ContactRole.objects.filter(id=parsed_role_id).first()
        if not role:
            raise ValueError("contact.role_id was not found.")
        return role

    role_value = str(payload.get("role") or payload.get("contact_role") or "").strip()
    if role_value:
        role = ContactRole.objects.filter(value__iexact=role_value).first()
        if not role:
            raise ValueError("contact.role was not found.")
        return role

    role = ContactRole.objects.filter(value=DEFAULT_CONTACT_ROLE).first()
    if role:
        return role

    role = ContactRole.objects.order_by("value").first()
    if not role:
        raise ValueError("No contact roles are configured.")
    return role


def _delete_links_and_orphaned_contacts(links: list[OfferContact]) -> None:
    contacts = [link.contact for link in links]
    for link in links:
        link.delete()

    for contact in contacts:
        if contact.contact_approved:
            continue
        if not OfferContact.objects.filter(contact=contact).exists():
            contact.delete()


def _clean_optional(value) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _clean_linkedin_url(value) -> str | None:
    cleaned = _clean_optional(value)
    if cleaned is None:
        return None
    try:
        validate_url(cleaned)
    except ValidationError as exc:
        raise ValueError("contact.linkedin must be a valid URL.") from exc
    return cleaned
