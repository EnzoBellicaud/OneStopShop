# Offer Contacts Analysis

## Current State

`Offer` does not have a singular `contact` field.

The model relationship is many-to-many:

```python
class Offer(models.Model):
    contacts = models.ManyToManyField(Contact, through="OfferContact", related_name="offers")
```

The join model stores offer-specific contact meaning:

```python
class OfferContact(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    role_label = models.CharField(max_length=50, default="primary_contact")
```

`Contact` currently has:

```python
contact_name
email
phone
role
organization
contact_approved
```

It does not currently have a `linkedin` field.

In `backend/content/views/offers.py`, `_offer_to_dict()` currently contains a direct singular access pattern:

```python
"contact": {
    "name": offer.contact.contact_name,
    "email": offer.contact.email,
    "phone": offer.contact.phone,
    "linkedin": offer.contact.linkedin
}
```

That is risky because `offer.contact` is not defined by the model. If this code path is active, it can raise `AttributeError`. Even if a future property is added, it also assumes a contact always exists.

## Requirement

Expose contact information in the offer response.

Desired single-contact shape:

```json
"contact": {
  "name": "Jane Doe",
  "email": "jane@example.edu",
  "phone": "+39...",
  "linkedin": "https://linkedin.com/in/jane"
}
```

But the data model supports multiple contacts per offer through `OfferContact`, with `role_label` values such as `primary_contact`, `secondary_contact`, or other labels. So the response design needs to account for zero, one, or many contacts.

## Option 1: Return One Primary Contact as `contact`

Implementation idea:

```python
def _contact_to_dict(contact):
    if contact is None:
        return None
    return {
        "name": contact.contact_name,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin": getattr(contact, "linkedin", None),
    }


def _primary_contact_for_offer(offer):
    links = list(getattr(offer, "prefetched_offer_contacts", []))
    primary = next((link for link in links if link.role_label == "primary_contact"), None)
    selected = primary or (links[0] if links else None)
    return selected.contact if selected else None
```

The API response keeps:

```json
"contact": { ... }
```

or:

```json
"contact": null
```

Query optimization:

```python
from django.db.models import Prefetch
from content.models import OfferContact

Offer.objects.select_related(
    "offer_type",
    "organization",
    "source_type",
    "target_profile",
).prefetch_related(
    "domains",
    Prefetch(
        "offercontact_set",
        queryset=OfferContact.objects.select_related("contact").order_by("role_label", "contact__contact_name"),
        to_attr="prefetched_offer_contacts",
    ),
)
```

Pros:

- Smallest frontend change.
- Keeps the requested `contact` property.
- Good fit if the UI only needs one visible contact.
- Backward-compatible if consumers expect one object.

Cons:

- Loses information when an offer has multiple contacts.
- Requires a rule for choosing the contact. Recommended rule: prefer `role_label == "primary_contact"`, otherwise first linked contact.
- If two contacts are marked primary, the API silently chooses one unless validation is added.

Implications:

- No database migration is required unless `linkedin` must be stored.
- Add null checks so offers without contacts return `"contact": null`.
- Consider a uniqueness rule later if only one primary contact should be allowed per offer.

## Option 2: Return All Contacts as `contacts`

Implementation idea:

```python
def _offer_contact_to_dict(link):
    contact = link.contact
    if contact is None:
        return None
    return {
        "role_label": link.role_label,
        "name": contact.contact_name,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin": getattr(contact, "linkedin", None),
    }
```

The API response becomes:

```json
"contacts": [
  {
    "role_label": "primary_contact",
    "name": "Jane Doe",
    "email": "jane@example.edu",
    "phone": "+39...",
    "linkedin": null
  },
  {
    "role_label": "technical_contact",
    "name": "Marco Rossi",
    "email": "marco@example.edu",
    "phone": null,
    "linkedin": null
  }
]
```

Pros:

- Matches the actual database model.
- Preserves `role_label`.
- Handles one-to-many cleanly.
- Better for admin/detail pages where all contact choices matter.

Cons:

- Requires frontend updates wherever offer details assume a singular contact.
- Slightly larger response payload.
- Existing consumers that expect `contact` would not automatically see the data unless both fields are returned.

Implications:

- Best long-term API shape.
- Use `Prefetch(... OfferContact.objects.select_related("contact") ...)` to avoid N+1 queries.
- Return an empty list when no contacts exist.

## Option 3: Return Both `contact` and `contacts`

Implementation idea:

```json
"contact": {
  "name": "Jane Doe",
  "email": "jane@example.edu",
  "phone": "+39...",
  "linkedin": null
},
"contacts": [
  {
    "role_label": "primary_contact",
    "name": "Jane Doe",
    "email": "jane@example.edu",
    "phone": "+39...",
    "linkedin": null
  }
]
```

Rules:

- `contacts` always contains all linked contacts.
- `contact` is the preferred primary contact.
- If there are no contacts, return:

```json
"contact": null,
"contacts": []
```

Pros:

- Safest transition path.
- Supports the simple frontend use case and the correct many-contact model.
- Avoids breaking older or simpler consumers.

Cons:

- Duplicates the primary contact data in the response.
- The API has to document clearly that `contact` is a convenience field.

Implications:

- This is probably the best implementation if the UI currently wants a single `contact`, but the backend wants to remain faithful to `OfferContact`.
- It allows future frontend screens to move to `contacts` without another backend change.

## LinkedIn Field

The desired response includes:

```json
"linkedin": "..."
```

But `Contact` does not currently define `linkedin`.

Possible approaches:

1. Return `"linkedin": null` for now using `getattr(contact, "linkedin", None)`.
2. Add `linkedin = models.URLField(max_length=500, blank=True, null=True)` to `Contact`.
3. Store external links in `Contact.details` if a JSON field is added later.

Recommendation:

- If LinkedIn is part of the real product requirement, add a nullable `linkedin` field with a migration.
- If it is only a placeholder in the response contract, return `null` for now and avoid a schema change.

## Recommended Implementation

Use Option 3: return both `contact` and `contacts`.

Reasoning:

- It fixes the immediate bug caused by direct `offer.contact` access.
- It gives the frontend the requested simple `contact` object.
- It does not ignore the existing many-to-many model.
- It lets us preserve `role_label` for primary vs secondary contacts.

Recommended response shape:

```json
{
  "id": "...",
  "title": "...",
  "contact": {
    "name": "Jane Doe",
    "email": "jane@example.edu",
    "phone": "+39...",
    "linkedin": null
  },
  "contacts": [
    {
      "role_label": "primary_contact",
      "name": "Jane Doe",
      "email": "jane@example.edu",
      "phone": "+39...",
      "linkedin": null
    }
  ]
}
```

If no contacts are linked:

```json
{
  "contact": null,
  "contacts": []
}
```

## Implementation Notes

1. Import `Prefetch` and `OfferContact` in `backend/content/views/offers.py`.
2. Add helper serializers for `Contact` and `OfferContact`.
3. Update all offer querysets used before `_offer_to_dict()`:
   - list endpoint
   - detail endpoint
   - create response reload
   - update response reload
4. Use `Prefetch` with `to_attr` so `_offer_to_dict()` can serialize contacts without extra queries.
5. Add tests for:
   - offer with no contacts
   - offer with one primary contact
   - offer with multiple contacts
   - response includes `contact` and `contacts`
6. Decide whether to add a nullable `Contact.linkedin` migration.

## Potential Follow-Up

If the domain requires exactly one primary contact per offer, add validation around `OfferContact.role_label == "primary_contact"`. A database-level partial unique constraint would be ideal on PostgreSQL:

```python
models.UniqueConstraint(
    fields=["offer"],
    condition=models.Q(role_label="primary_contact"),
    name="uniq_primary_contact_per_offer",
)
```

That would prevent multiple primary contacts while still allowing secondary contacts.

---

# Many-to-Many Design Analysis: Offer ↔ OfferContact ↔ Contact

## Data Model Overview

The relationship is implemented as a traditional Django many-to-many through a join table:

```
Offer (1) ──→ (many) OfferContact (many) ←─ (1) Contact
```

### Why Through Table?

The `OfferContact` join model serves two purposes:
1. **Relationship metadata**: `role_label` differentiates between primary, secondary, and other contact roles.
2. **Offer-specific context**: Each offer can have its own contact set with contextual roles.

### Current State

- **Offer deletion**: Cascades to `OfferContact` records (via `on_delete=CASCADE`).
- **Contact deletion**: Cascades to `OfferContact` records (via `on_delete=CASCADE`).
- **Orphan problem**: If an `OfferContact` is deleted directly (via admin or API), the `Contact` record remains. This can accumulate unused `Contact` records that are never referenced by any offer.

## Orphan Cleanup Strategy

### Problem Statement

When an offer is deleted or an OfferContact link is removed, associated `Contact` records may become orphaned if they are no longer linked to any other offer. Without cleanup, the database accumulates orphan `Contact` entries that consume storage and complicate data integrity.

### Proposed Solution: Cascade + Cleanup Signal

Implement a Django signal handler that automatically deletes orphaned `Contact` records when their last `OfferContact` link is removed:

```python
from django.db.models.signals import post_delete
from django.dispatch import receiver
from content.models import Contact, OfferContact

@receiver(post_delete, sender=OfferContact)
def cleanup_orphaned_contacts(sender, instance, **kwargs):
    """
    After an OfferContact is deleted, check if the Contact has no other offers.
    If so, delete the Contact record (unless it is protected by business logic).
    """
    contact = instance.contact
    
    # Check if this contact has any remaining OfferContact links
    remaining_links = OfferContact.objects.filter(contact=contact).exists()
    
    if not remaining_links:
        # Additional safety: ensure contact is not referenced elsewhere
        # (e.g., not marked as contact_approved, or not in any admin-approved list)
        if not contact.contact_approved:  # Only delete if not approved/verified
            contact.delete()
            logger.info(f"Cleaned up orphaned Contact {contact.id}")
```

### Database Constraints

To prevent unexpected orphan creation, enforce via database constraint:

```python
class Meta:
    db_table = "offer_contact"
    constraints = [
        models.UniqueConstraint(
            fields=["offer", "contact"],
            name="uniq_offer_contact",
        ),
        models.CheckConstraint(
            check=models.Q(role_label__in=["primary_contact", "secondary_contact", "technical_contact", "procurement_contact"]),
            name="valid_role_labels",
        ),
    ]
```

### Implications and Trade-offs

**Pros:**
- Automatic cleanup keeps the database clean.
- No manual intervention needed.
- Prevents data bloat over time.

**Cons:**
- Deletes `Contact` records automatically, which can surprise users if they expect to re-use a contact later.
- If a contact is `contact_approved=True`, permanent deletion might violate audit/compliance rules.
- Signal handlers can have hidden side effects; hard to debug.

**Alternative: Soft Delete**

Instead of deleting, mark contacts as "archived" or "inactive":

```python
class Contact(TimeStampedModel):
    ...
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        indexes = [models.Index(fields=["is_archived"]),]
```

Then filter queries to exclude archived contacts, and manually review orphans for re-use.

---

## Component-Level Implications

### 1. API Layer (`backend/content/views/offers.py`)

**Current State:**
- Uses `_offer_to_dict()` to serialize offer details.
- Implements Option 1 (single primary contact).
- Prefetches `OfferContact` with `Prefetch()` and `to_attr="prefetched_offer_contacts"`.

**Required Changes for Contact[] Operations:**

1. **Add endpoint for managing offer contacts:**
   ```python
   # GET /api/offers/{offer_id}/contacts/ → list all contacts
   # POST /api/offers/{offer_id}/contacts/ → add a contact to offer
   # DELETE /api/offers/{offer_id}/contacts/{contact_id}/ → remove contact link
   # PATCH /api/offers/{offer_id}/contacts/{contact_id}/ → update role_label
   ```

2. **Update offer serialization to include both `contact` and `contacts`:**
   ```python
   def _offer_to_dict(offer: Offer) -> dict:
       # ... existing fields ...
       "contact": _primary_contact_for_offer(offer),
       "contacts": [_offer_contact_to_dict(link) for link in offer.prefetched_offer_contacts],
   ```

3. **Add request validation for contact operations:**
   - Validate `role_label` values against enum.
   - Prevent multiple primary contacts (optional constraint).
   - Ensure contact exists before linking.

4. **Transactional safety:**
   - Wrap offer+contact changes in `transaction.atomic()`.
   - Handle signal-based cleanup gracefully.

### 2. Scraper & Ingestion Services (`backend/content/scrapers/`, `backend/content/matching_service.py`)

**Current Usage:**
- `UrlScraperService` and `CrawlerService` create offers during scraping.
- May extract contact info from HTML pages.

**Required Changes:**

1. **Contact extraction from scraped pages:**
   ```python
   # In extractors.py or scraper service:
   def extract_contacts_from_page(html, page_source):
       """Extract name, email, phone from contact forms or footer."""
       return {
           "primary_contact": {"name": "...", "email": "...", ...},
           "secondary_contact": {"name": "...", "email": "...", ...},
       }
   ```

2. **Upsert contact logic in `_upsert_offer()`:**
   ```python
   # After creating/updating the offer, link contacts:
   for role_label, contact_data in extracted_contacts.items():
       contact, _ = Contact.objects.get_or_create(
           email=contact_data["email"],
           defaults={
               "contact_name": contact_data["name"],
               "phone": contact_data.get("phone"),
               "role_id": ...,
               "organization": offer.organization,
           }
       )
       OfferContact.objects.get_or_create(
           offer=offer,
           contact=contact,
           defaults={"role_label": role_label},
       )
   ```

3. **Bulk import (CSV/JSON) in `backend/content/ingestion/importer.py`:**
   - Parse contact columns: `primary_contact_email`, `primary_contact_name`, etc.
   - Create or link contacts based on email (idempotent).

4. **Matching service impact:**
   - `matching_service.py` may use contact info to identify target profiles.
   - Update queries to select correct contact from `OfferContact` set.

5. **Garbage collection in scraper:**
   - If scraper encounters contact info conflicts (e.g., two emails for one role), log warning and take first.
   - After offer deletion, rely on signal to clean orphaned contacts.

### 3. LLM Integration (`backend/content/scrapers/ollama_client.py`)

**Current Usage:**
- LLM extracts offer metadata (title, summary, domain, type) from scraped pages.

**Required Changes:**

1. **Contact extraction in LLM prompt:**
   ```python
   def assess_and_extract(self, html, page_source, extracted):
       # Existing extraction...
       llm_prompt = f"""
       ...
       Extract the primary contact:
       - Name (e.g., "Jane Doe"): 
       - Email (e.g., "jane@example.edu"): 
       - Phone (e.g., "+39..."): 
       - Role (e.g., "primary_contact" or "technical_contact"):
       ...
       """
   ```

2. **Parse LLM response to include contacts:**
   ```python
   llm_payload = LLMPayload(
       title=...,
       summary=...,
       contacts={
           "primary_contact": {"name": "...", "email": "..."},
       }
   )
   ```

3. **Validate extracted emails:**
   - Check email format.
   - Deduplicate if LLM returns same email multiple times.
   - Store low-confidence extractions in `details["llm_contacts_raw"]` for manual review.

4. **Confidence scoring:**
   - Include separate confidence for contacts vs. title/summary.
   - If contact confidence < threshold, skip contact creation.

### 4. Unit Tests (`backend/content/tests.py`)

**Current Tests:**
- `test_offers_list_endpoint`, `test_offer_detail_endpoint`: basic offer serialization.
- No tests for contact operations yet.

**Required New Tests:**

1. **API endpoint tests:**
   ```python
   def test_offer_detail_includes_primary_and_all_contacts(self):
       """Verify offer detail returns both contact and contacts."""
       offer = Offer.objects.create(...)
       contact1 = Contact.objects.create(...)
       OfferContact.objects.create(offer=offer, contact=contact1, role_label="primary_contact")
       
       response = self.client.get(f"/api/offers/{offer.id}/")
       self.assertEqual(response.status_code, 200)
       data = response.json()
       self.assertIsNotNone(data["contact"])
       self.assertIsNotNone(data["contacts"])
       self.assertEqual(len(data["contacts"]), 1)
       self.assertEqual(data["contacts"][0]["role_label"], "primary_contact")

   def test_offer_detail_no_contacts_returns_empty(self):
       """Verify offer with no contacts returns null/empty."""
       offer = Offer.objects.create(...)
       response = self.client.get(f"/api/offers/{offer.id}/")
       self.assertIsNone(response.json()["contact"])
       self.assertEqual(response.json()["contacts"], [])

   def test_post_add_contact_to_offer(self):
       """Test adding a contact to an offer via API."""
       offer = Offer.objects.create(...)
       contact = Contact.objects.create(...)
       response = self.client.post(
           f"/api/offers/{offer.id}/contacts/",
           {"contact_id": str(contact.id), "role_label": "secondary_contact"}
       )
       self.assertEqual(response.status_code, 201)
       self.assertTrue(OfferContact.objects.filter(offer=offer, contact=contact).exists())

   def test_delete_contact_from_offer_cleans_orphan(self):
       """Test that deleting last OfferContact link cleans orphaned Contact."""
       offer = Offer.objects.create(...)
       contact = Contact.objects.create(contact_approved=False)
       link = OfferContact.objects.create(offer=offer, contact=contact)
       
       # Delete the link
       link.delete()
       
       # Contact should be cleaned up (if signal is enabled)
       self.assertFalse(Contact.objects.filter(id=contact.id).exists())

   def test_delete_contact_keeps_approved_contact(self):
       """Test that approved contacts are not auto-deleted."""
       offer = Offer.objects.create(...)
       contact = Contact.objects.create(contact_approved=True)
       link = OfferContact.objects.create(offer=offer, contact=contact)
       
       # Delete the link
       link.delete()
       
       # Contact should remain (approved contacts are protected)
       self.assertTrue(Contact.objects.filter(id=contact.id).exists())

   def test_offer_delete_cascades_to_offer_contacts(self):
       """Test that deleting an offer cascades to OfferContact."""
       offer = Offer.objects.create(...)
       contact = Contact.objects.create(contact_approved=False)
       link = OfferContact.objects.create(offer=offer, contact=contact)
       
       offer.delete()
       
       # OfferContact should be deleted
       self.assertFalse(OfferContact.objects.filter(id=link.id).exists())
       # Orphaned contact should be cleaned
       self.assertFalse(Contact.objects.filter(id=contact.id).exists())
   ```

2. **Scraper integration tests:**
   ```python
   def test_scraper_creates_and_links_contacts(self):
       """Test that UrlScraperService extracts and links contacts."""
       # Mock HTML with contact info
       # Run scraper
       # Verify OfferContact records created
   ```

3. **Data consistency tests:**
   ```python
   def test_no_orphaned_contacts_after_bulk_delete(self):
       """Scan database for orphaned contacts and fail if found."""
       orphans = Contact.objects.filter(
           contact_approved=False,
           offercontact__isnull=True
       )
       self.assertEqual(orphans.count(), 0, "Found orphaned contacts")
   ```

### 5. Services (`backend/content/matching_service.py`, Domain/Profile matching)

**Current Usage:**
- Matches offers to user needs based on domain, target_profile, etc.
- Does not currently use contact information.

**Required Changes:**

1. **Update matching algorithm if contact role matters:**
   ```python
   def run_matching_for_offers(offer_ids):
       for offer in Offer.objects.filter(id__in=offer_ids):
           # Check if offer has a technical contact (LLM can identify this)
           primary = offer.offercontact_set.filter(role_label="primary_contact").first()
           if primary and primary.contact:
               # Could use contact approval status to boost confidence
               pass
   ```

2. **Contact data in user need notifications:**
   - When an offer matches a user need, include contact info in email/notification.
   - Use primary contact for the message.

3. **Admin/dashboard views:**
   - Show all contacts, not just primary.
   - Allow admin to change role labels or delete links.
   - Trigger cleanup via admin actions.

### 6. Admin Interface

**Required Changes:**

1. **Inline editing for OfferContact:**
   ```python
   class OfferContactInline(admin.TabularInline):
       model = OfferContact
       fields = ("contact", "role_label")
       extra = 1

   class OfferAdmin(admin.ModelAdmin):
       inlines = [OfferContactInline]
   ```

2. **Custom admin action to clean orphans:**
   ```python
   def cleanup_orphaned_contacts(modeladmin, request, queryset):
       # Manually run cleanup for orphaned contacts
       orphans = Contact.objects.filter(
           contact_approved=False,
           offercontact__isnull=True
       )
       deleted_count, _ = orphans.delete()
       modeladmin.message_user(request, f"Deleted {deleted_count} orphaned contacts")
   cleanup_orphaned_contacts.short_description = "Clean up orphaned contacts"

   class ContactAdmin(admin.ModelAdmin):
       actions = [cleanup_orphaned_contacts]
   ```

---

## Migration & Deployment Strategy

### Phase 1: Backend Changes (Current)
1. ✅ Update `offers.py` to return both `contact` and `contacts`.
2. Add signal handler for orphan cleanup.
3. Add tests for contact operations.

### Phase 2: Scraper & Services
4. Extract contact info in `UrlScraperService` and LLM.
5. Create/link contacts during offer upsert.
6. Test scraper with contact extraction.

### Phase 3: API Endpoints
7. Add POST/DELETE endpoints for managing offer→contact links.
8. Add PATCH to update `role_label`.
9. Documentation and API versioning.

### Phase 4: Frontend Integration
10. Update offer detail view to show `contacts[]`.
11. Add UI for managing offer contacts (if required).
12. Update matching/notification emails to include contact info.

### Phase 5: Data Cleanup
13. Run one-time script to identify and merge duplicate contacts (email-based).
14. Audit orphaned contacts before enabling auto-cleanup signal.
15. Consider archiving instead of deleting for first release.

---

## Summary of Changes by File

| File | Changes |
|------|---------|
| `models.py` | Add signal handler for orphan cleanup; possibly add `Contact.is_archived` soft-delete |
| `views/offers.py` | Return both `contact` and `contacts`; add contact management endpoints |
| `scrapers/service.py` | Extract and link contacts during offer upsert |
| `scrapers/queue_service.py` | Handle contact extraction in `_scrape_one()` and `_scrape_import_url()` |
| `scrapers/ollama_client.py` | Parse LLM response to include contact extraction |
| `matching_service.py` | Use contact info in matching algorithm (optional) |
| `tests.py` | Add contact CRUD tests, orphan cleanup tests, scraper integration tests |
| `admin.py` | Add `OfferContactInline`, contact cleanup action |
