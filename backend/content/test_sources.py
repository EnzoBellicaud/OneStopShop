"""Tests for admin scraping-source CRUD endpoints."""
import json
import uuid
from django.test import TestCase, Client
from content.models import Organization, ScrapingSource, User, UserOrganization, UserRole
from content.auth import hash_password

_TEST_ORG_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))


def _make_org():
    org, _ = Organization.objects.get_or_create(
        id=_TEST_ORG_ID,
        defaults={
            "name": "Test Org",
            "type": Organization.OrganizationType.UNIVERSITY,
            "country": "IT",
            "website": "https://test.example.com",
        },
    )
    return org


def _make_admin(username="admin", password="Admin1234!"):
    user = User.objects.create(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        profile=User.ProfileType.ADMIN,
        email_verified=True,
        approval_status="approved",
        is_active=True,
    )
    return user, password


def _make_student(username="student", password="Student123!"):
    user = User.objects.create(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        profile="Student",
        email_verified=True,
        approval_status="approved",
        is_active=True,
    )
    return user, password


def _token(client, username, password):
    resp = client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return json.loads(resp.content)["tokens"]["access_token"]


def _source_payload(**overrides):
    base = {
        "key": "test_source",
        "name": "Test Source",
        "url": "https://example.com",
        "organization_id": _TEST_ORG_ID,
        "target_profile": "student",
        "country": "IT",
        "domain_names": ["AI"],
        "interval_minutes": 120,
        "llm_fallback_enabled": True,
        "enabled": True,
        "quality": "real",
        "crawl_depth": 1,
        "crawl_max_pages": 25,
        "crawl_match_patterns": [],
        "crawl_exclude_patterns": [],
        "auto_publish_enabled": False,
    }
    base.update(overrides)
    return base


class SourcesListCreateTestCase(TestCase):
    """Tests for GET /api/admin/sources and POST /api/admin/sources."""

    def setUp(self):
        self.client = Client()
        ScrapingSource.objects.all().delete()
        _make_org()
        _, pw = _make_admin()
        self.token = _token(self.client, "admin", pw)
        _, spw = _make_student()
        self.student_token = _token(self.client, "student", spw)
        self.url = "/api/admin/sources"

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    # ── Auth guard ──────────────────────────────────────────────────────────

    def test_list_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_list_requires_admin(self):
        resp = self.client.get(self.url, **self._auth(self.student_token))
        self.assertEqual(resp.status_code, 403)

    def test_create_requires_auth(self):
        resp = self.client.post(
            self.url,
            data=json.dumps(_source_payload()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_create_requires_admin(self):
        resp = self.client.post(
            self.url,
            data=json.dumps(_source_payload()),
            content_type="application/json",
            **self._auth(self.student_token),
        )
        self.assertEqual(resp.status_code, 403)

    # ── List ────────────────────────────────────────────────────────────────

    def test_list_empty(self):
        resp = self.client.get(self.url, **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["results"], [])

    def test_list_returns_all_sources(self):
        ScrapingSource.objects.create(
            key="src_a", name="A", url="https://a.com", organization_token="o",
        )
        ScrapingSource.objects.create(
            key="src_b", name="B", url="https://b.com", organization_token="o",
        )
        resp = self.client.get(self.url, **self._auth())
        data = json.loads(resp.content)
        self.assertEqual(data["count"], 2)
        keys = {s["key"] for s in data["results"]}
        self.assertIn("src_a", keys)
        self.assertIn("src_b", keys)

    # ── Create ──────────────────────────────────────────────────────────────

    def test_create_success(self):
        payload = _source_payload()
        resp = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["key"], "test_source")
        self.assertEqual(data["name"], "Test Source")
        self.assertEqual(data["url"], "https://example.com")
        self.assertFalse(data["auto_publish_enabled"])
        self.assertEqual(data["auto_publish_mode"], "llm")
        self.assertTrue(ScrapingSource.objects.filter(key="test_source").exists())

    def test_create_with_auto_publish_enabled(self):
        payload = _source_payload(auto_publish_enabled=True, llm_fallback_enabled=False)
        resp = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertTrue(data["auto_publish_enabled"])
        self.assertEqual(data["auto_publish_mode"], "deterministic")
        source = ScrapingSource.objects.get(key="test_source")
        self.assertTrue(source.auto_publish_enabled)

    def test_create_missing_required_fields(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"key": "only_key"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_auto_generates_key_when_absent(self):
        payload = {
            "name": "Auto Key Source",
            "url": "https://autokey.example.com",
            "organization_id": _TEST_ORG_ID,
        }
        resp = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        key = data["key"]
        self.assertTrue(len(key) > 0)
        import uuid as _uuid
        _uuid.UUID(key)  # raises ValueError if not a valid UUID

    def test_create_invalid_target_profile(self):
        payload = _source_payload(target_profile="invalid_profile", key="bad_tp_src")
        resp = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_duplicate_key(self):
        ScrapingSource.objects.create(
            key="test_source", name="Existing", url="https://x.com", organization_token="o",
        )
        resp = self.client.post(
            self.url,
            data=json.dumps(_source_payload()),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 409)

    def test_create_invalid_json(self):
        resp = self.client.post(
            self.url,
            data="not-json",
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_sets_defaults(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({
                "key": "minimal_src",
                "name": "Minimal",
                "url": "https://min.com",
                "organization_id": _TEST_ORG_ID,
            }),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["interval_minutes"], 360)
        self.assertTrue(data["llm_fallback_enabled"])
        self.assertTrue(data["enabled"])
        self.assertFalse(data["auto_publish_enabled"])
        self.assertEqual(data["auto_publish_mode"], "llm")
        self.assertNotIn("crawl_enabled", data)


class SourcesDetailTestCase(TestCase):
    """Tests for GET/PATCH/DELETE /api/admin/sources/<key>."""

    def setUp(self):
        self.client = Client()
        _, pw = _make_admin()
        self.token = _token(self.client, "admin", pw)
        self.source = ScrapingSource.objects.create(
            key="existing_src",
            name="Existing Source",
            url="https://existing.com",
            organization_token="org",
            target_profile="student",
            country="IT",
            llm_fallback_enabled=True,
            enabled=True,
        )
        self.url = f"/api/admin/sources/{self.source.key}"

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    # ── GET detail ──────────────────────────────────────────────────────────

    def test_get_detail_success(self):
        resp = self.client.get(self.url, **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["key"], "existing_src")
        self.assertEqual(data["name"], "Existing Source")
        self.assertFalse(data["auto_publish_enabled"])
        self.assertEqual(data["auto_publish_mode"], "llm")

    def test_get_detail_not_found(self):
        resp = self.client.get("/api/admin/sources/nonexistent", **self._auth())
        self.assertEqual(resp.status_code, 404)

    def test_get_detail_requires_admin(self):
        _, spw = _make_student()
        stok = _token(self.client, "student", spw)
        resp = self.client.get(self.url, HTTP_AUTHORIZATION=f"Bearer {stok}")
        self.assertEqual(resp.status_code, 403)

    # ── PATCH ───────────────────────────────────────────────────────────────

    def test_patch_name(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"name": "Updated Name"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["name"], "Updated Name")
        self.source.refresh_from_db()
        self.assertEqual(self.source.name, "Updated Name")

    def test_patch_llm_fallback_toggle(self):
        self.source.llm_fallback_enabled = True
        self.source.save()
        resp = self.client.patch(
            self.url,
            data=json.dumps({"llm_fallback_enabled": False}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse(data["llm_fallback_enabled"])
        self.assertEqual(data["auto_publish_mode"], "deterministic")
        self.source.refresh_from_db()
        self.assertFalse(self.source.llm_fallback_enabled)

    def test_patch_enabled_toggle(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"enabled": False}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(json.loads(resp.content)["enabled"])

    def test_patch_auto_publish_toggle(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"auto_publish_enabled": True}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data["auto_publish_enabled"])
        self.source.refresh_from_db()
        self.assertTrue(self.source.auto_publish_enabled)

    def test_patch_interval_minutes(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"interval_minutes": 720}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["interval_minutes"], 720)

    def test_patch_domain_names(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"domain_names": ["AI", "Cybersecurity"]}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["domain_names"], ["AI", "Cybersecurity"])

    def test_patch_unknown_field_ignored(self):
        resp = self.client.patch(
            self.url,
            data=json.dumps({"unknown_field": "should_be_ignored", "name": "Still Updated"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Still Updated")

    def test_patch_invalid_json(self):
        resp = self.client.patch(
            self.url,
            data="bad-json",
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_patch_not_found(self):
        resp = self.client.patch(
            "/api/admin/sources/missing",
            data=json.dumps({"name": "x"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 404)

    # ── DELETE ──────────────────────────────────────────────────────────────

    def test_delete_success(self):
        resp = self.client.delete(self.url, **self._auth())
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(ScrapingSource.objects.filter(key="existing_src").exists())

    def test_delete_not_found(self):
        resp = self.client.delete("/api/admin/sources/ghost", **self._auth())
        self.assertEqual(resp.status_code, 404)

    def test_delete_requires_admin(self):
        _, spw = _make_student(username="student2")
        stok = _token(self.client, "student2", spw)
        resp = self.client.delete(self.url, HTTP_AUTHORIZATION=f"Bearer {stok}")
        self.assertEqual(resp.status_code, 403)


class GetSourcesFromDBTestCase(TestCase):
    """Tests for get_sources() DB-backed implementation."""

    def setUp(self):
        ScrapingSource.objects.all().delete()

    def test_get_sources_returns_enabled_only_by_default(self):
        from content.scrapers.source_registry import get_sources
        ScrapingSource.objects.create(
            key="enabled_src", name="Enabled", url="https://e.com",
            organization_token="o", enabled=True,
        )
        ScrapingSource.objects.create(
            key="disabled_src", name="Disabled", url="https://d.com",
            organization_token="o", enabled=False,
        )
        results = get_sources()
        keys = {s.key for s in results}
        self.assertIn("enabled_src", keys)
        self.assertNotIn("disabled_src", keys)

    def test_get_sources_with_key_filter_returns_all_matching(self):
        from content.scrapers.source_registry import get_sources
        ScrapingSource.objects.create(
            key="src_a", name="A", url="https://a.com",
            organization_token="o", enabled=False,
        )
        ScrapingSource.objects.create(
            key="src_b", name="B", url="https://b.com",
            organization_token="o", enabled=True,
        )
        results = get_sources(source_keys=["src_a", "src_b"])
        keys = {s.key for s in results}
        self.assertEqual(keys, {"src_a", "src_b"})

    def test_get_sources_returns_source_definition_objects(self):
        from content.scrapers.source_registry import get_sources
        from content.scrapers.types import SourceDefinition
        ScrapingSource.objects.create(
            key="typed_src", name="Typed", url="https://t.com",
            organization_token="org_x",
            target_profile="researcher", country="DE",
        )
        results = get_sources(source_keys=["typed_src"])
        self.assertEqual(len(results), 1)
        src = results[0]
        self.assertIsInstance(src, SourceDefinition)
        self.assertEqual(src.key, "typed_src")
        self.assertEqual(src.country, "DE")
        self.assertFalse(src.auto_publish_enabled)

    def test_get_sources_maps_auto_publish_enabled(self):
        from content.scrapers.source_registry import get_sources
        ScrapingSource.objects.create(
            key="auto_src", name="Auto", url="https://auto.com",
            organization_token="org_x", auto_publish_enabled=True,
        )
        results = get_sources(source_keys=["auto_src"])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].auto_publish_enabled)

    def test_get_sources_empty_db(self):
        from content.scrapers.source_registry import get_sources
        results = get_sources()
        self.assertEqual(results, [])


_OTHER_ORG_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))


def _make_teacher(username="teacher_test", password="Teacher123!"):
    user = User.objects.create(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        profile=User.ProfileType.TEACHER,
        email_verified=True,
        approval_status="approved",
        is_active=True,
    )
    return user, password


def _make_company(username="company_test", password="Company123!"):
    user = User.objects.create(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password(password),
        profile=User.ProfileType.COMPANY,
        email_verified=True,
        approval_status="approved",
        is_active=True,
    )
    return user, password


def _make_other_org():
    org, _ = Organization.objects.get_or_create(
        id=_OTHER_ORG_ID,
        defaults={
            "name": "Other Org",
            "type": Organization.OrganizationType.UNIVERSITY,
            "country": "SE",
            "website": "https://other.example.com",
        },
    )
    return org


class SourcesOrgScopeTestCase(TestCase):
    """Teachers can only access sources belonging to their own organization."""

    def setUp(self):
        self.client = Client()
        ScrapingSource.objects.all().delete()
        self.own_org = _make_org()
        self.other_org = _make_other_org()
        self.role, _ = UserRole.objects.get_or_create(
            name="researcher", defaults={"description": "Researcher role"}
        )
        self.teacher, self.teacher_pw = _make_teacher()
        UserOrganization.objects.create(
            user=self.teacher, organization=self.own_org, role=self.role
        )
        self.teacher_token = _token(self.client, self.teacher.username, self.teacher_pw)
        self.own_source = ScrapingSource.objects.create(
            key="own_src",
            name="Own Source",
            url="https://own.example.com",
            organization=self.own_org,
            organization_token=str(self.own_org.id),
            llm_fallback_enabled=True,
            enabled=True,
        )
        self.other_source = ScrapingSource.objects.create(
            key="other_src",
            name="Other Source",
            url="https://other.example.com",
            organization=self.other_org,
            organization_token=str(self.other_org.id),
            llm_fallback_enabled=True,
            enabled=True,
        )

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.teacher_token}"}

    def test_teacher_can_list_own_org_sources(self):
        resp = self.client.get("/api/admin/sources", **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        keys = {s["key"] for s in data["results"]}
        self.assertIn("own_src", keys)

    def test_teacher_cannot_see_other_org_sources(self):
        resp = self.client.get("/api/admin/sources", **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        keys = {s["key"] for s in data["results"]}
        self.assertNotIn("other_src", keys)
        self.assertEqual(data["count"], 1)

    def test_teacher_can_create_source_org_auto_assigned(self):
        payload = {
            "name": "New Teacher Source",
            "url": "https://new.example.com",
        }
        resp = self.client.post(
            "/api/admin/sources",
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["organization_id"], str(self.own_org.id))
        import uuid as _uuid
        _uuid.UUID(data["key"])  # auto-generated key must be a valid UUID
        src = ScrapingSource.objects.get(key=data["key"])
        self.assertEqual(str(src.organization_id), str(self.own_org.id))

    def test_teacher_can_toggle_llm_fallback_own_source(self):
        resp = self.client.patch(
            f"/api/admin/sources/{self.own_source.key}",
            data=json.dumps({"llm_fallback_enabled": False}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse(data["llm_fallback_enabled"])
        self.own_source.refresh_from_db()
        self.assertFalse(self.own_source.llm_fallback_enabled)

    def test_teacher_cannot_change_source_organization(self):
        resp = self.client.patch(
            f"/api/admin/sources/{self.own_source.key}",
            data=json.dumps({"organization_id": str(self.other_org.id)}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 200)
        self.own_source.refresh_from_db()
        self.assertEqual(str(self.own_source.organization_id), str(self.own_org.id))

    def test_teacher_cannot_access_other_org_source_detail(self):
        resp = self.client.get(
            f"/api/admin/sources/{self.other_source.key}", **self._auth()
        )
        self.assertEqual(resp.status_code, 404)

    def test_teacher_cannot_patch_other_org_source(self):
        resp = self.client.patch(
            f"/api/admin/sources/{self.other_source.key}",
            data=json.dumps({"name": "Hacked"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 404)

    def test_teacher_cannot_delete_other_org_source(self):
        resp = self.client.delete(
            f"/api/admin/sources/{self.other_source.key}", **self._auth()
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(ScrapingSource.objects.filter(key="other_src").exists())

    def test_teacher_can_delete_own_org_source(self):
        resp = self.client.delete(
            f"/api/admin/sources/{self.own_source.key}", **self._auth()
        )
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(ScrapingSource.objects.filter(key="own_src").exists())

    def test_teacher_with_no_org_cannot_create_source(self):
        teacher_no_org, pw = _make_teacher(username="teacher_no_org", password="Teacher123!")
        token = _token(self.client, "teacher_no_org", pw)
        resp = self.client.post(
            "/api/admin/sources",
            data=json.dumps({"name": "New Source", "url": "https://new.example.com"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(resp.status_code, 403)
        data = json.loads(resp.content)
        self.assertIn("No organization linked", data["detail"])

    def test_patch_invalid_target_profile_returns_400(self):
        resp = self.client.patch(
            f"/api/admin/sources/{self.own_source.key}",
            data=json.dumps({"target_profile": "invalid_profile"}),
            content_type="application/json",
            **self._auth(),
        )
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertIn("target_profile", data["detail"])

    def test_company_cannot_access_sources(self):
        company, company_pw = _make_company()
        company_token = _token(self.client, company.username, company_pw)
        resp = self.client.get("/api/admin/sources", HTTP_AUTHORIZATION=f"Bearer {company_token}")
        self.assertEqual(resp.status_code, 403)
