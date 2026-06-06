"""Tests for mock website views and admin CRUD API."""
import json
import uuid

from django.test import Client, TestCase, override_settings

from content.auth import hash_password
from content.models import MockOpportunity, User


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


def _make_opportunity(**kwargs):
    defaults = {
        "title": "Python Internship at Demo University",
        "description": "A great internship opportunity for CS students.",
        "offer_type": "internship",
        "target_profile": "student",
    }
    defaults.update(kwargs)
    return MockOpportunity.objects.create(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# Public mock website HTML views
# ─────────────────────────────────────────────────────────────────────────────

class MockWebsiteListViewTestCase(TestCase):
    """Tests for GET /mock/ — public HTML list page."""

    def setUp(self):
        self.client = Client()

    def test_list_returns_200(self):
        resp = self.client.get("/mock/")
        self.assertEqual(resp.status_code, 200)

    def test_list_empty_shows_no_opportunities_message(self):
        resp = self.client.get("/mock/")
        self.assertContains(resp, "No opportunities are currently listed.")

    def test_list_shows_opportunity_link(self):
        opp = _make_opportunity()
        resp = self.client.get("/mock/")
        self.assertContains(resp, opp.title)
        self.assertContains(resp, f"/mock/offers/{opp.id}/")

    def test_list_shows_multiple_opportunities(self):
        opp1 = _make_opportunity(title="Internship A")
        opp2 = _make_opportunity(title="Thesis B", offer_type="thesis")
        resp = self.client.get("/mock/")
        self.assertContains(resp, opp1.title)
        self.assertContains(resp, opp2.title)

    def test_list_no_auth_required(self):
        # Must be publicly accessible for the scraper (no auth header)
        resp = self.client.get("/mock/")
        self.assertNotEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 403)


class MockWebsiteDetailViewTestCase(TestCase):
    """Tests for GET /mock/offers/<uuid>/ — public HTML detail page."""

    def setUp(self):
        self.client = Client()

    def test_detail_returns_200_for_existing(self):
        opp = _make_opportunity()
        resp = self.client.get(f"/mock/offers/{opp.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_detail_shows_title_in_h1(self):
        opp = _make_opportunity(title="ML Research Thesis")
        resp = self.client.get(f"/mock/offers/{opp.id}/")
        self.assertContains(resp, "<h1>")
        self.assertContains(resp, opp.title)

    def test_detail_shows_offer_type_in_body(self):
        opp = _make_opportunity(offer_type="internship")
        resp = self.client.get(f"/mock/offers/{opp.id}/")
        self.assertContains(resp, "internship")

    def test_detail_shows_description(self):
        opp = _make_opportunity(description="Unique description XYZ123")
        resp = self.client.get(f"/mock/offers/{opp.id}/")
        self.assertContains(resp, "Unique description XYZ123")

    def test_detail_returns_404_for_missing(self):
        missing_id = uuid.uuid4()
        resp = self.client.get(f"/mock/offers/{missing_id}/")
        self.assertEqual(resp.status_code, 404)

    def test_detail_returns_404_after_deletion(self):
        opp = _make_opportunity()
        opp_id = opp.id
        opp.delete()
        resp = self.client.get(f"/mock/offers/{opp_id}/")
        self.assertEqual(resp.status_code, 404)

    def test_detail_no_auth_required(self):
        opp = _make_opportunity()
        resp = self.client.get(f"/mock/offers/{opp.id}/")
        self.assertNotEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 403)


# ─────────────────────────────────────────────────────────────────────────────
# Admin CRUD API — list / create
# ─────────────────────────────────────────────────────────────────────────────

@override_settings(RATELIMIT_ENABLE=False)
class AdminMockListCreateTestCase(TestCase):
    """Tests for GET/POST /api/admin/mock-opportunities."""

    def setUp(self):
        self.client = Client()
        _, pw = _make_admin()
        self.token = _token(self.client, "admin", pw)
        _, spw = _make_student()
        self.student_token = _token(self.client, "student", spw)
        self.url = "/api/admin/mock-opportunities"

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    def _post(self, payload, token=None):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            **self._auth(token),
        )

    # ── Auth guard ────────────────────────────────────────────────────────────

    def test_list_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_list_requires_admin(self):
        resp = self.client.get(self.url, **self._auth(self.student_token))
        self.assertEqual(resp.status_code, 403)

    def test_create_requires_auth(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"title": "Test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_create_requires_admin(self):
        resp = self._post({"title": "Test"}, token=self.student_token)
        self.assertEqual(resp.status_code, 403)

    # ── List ─────────────────────────────────────────────────────────────────

    def test_list_empty(self):
        resp = self.client.get(self.url, **self._auth())
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["results"], [])

    def test_list_returns_all_opportunities(self):
        _make_opportunity(title="Op A")
        _make_opportunity(title="Op B", offer_type="thesis")
        resp = self.client.get(self.url, **self._auth())
        data = json.loads(resp.content)
        self.assertEqual(data["count"], 2)
        titles = {o["title"] for o in data["results"]}
        self.assertIn("Op A", titles)
        self.assertIn("Op B", titles)

    def test_list_result_shape(self):
        _make_opportunity()
        resp = self.client.get(self.url, **self._auth())
        item = json.loads(resp.content)["results"][0]
        for field in ("id", "title", "description", "offer_type", "target_profile", "created_at"):
            self.assertIn(field, item)

    # ── Create ────────────────────────────────────────────────────────────────

    def test_create_success(self):
        payload = {
            "title": "New Internship",
            "description": "A great opportunity.",
            "offer_type": "internship",
            "target_profile": "student",
        }
        resp = self._post(payload)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["title"], "New Internship")
        self.assertEqual(data["offer_type"], "internship")
        self.assertTrue(MockOpportunity.objects.filter(title="New Internship").exists())

    def test_create_defaults_offer_type_and_profile(self):
        resp = self._post({"title": "Minimal"})
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["offer_type"], "internship")
        self.assertEqual(data["target_profile"], "student")

    def test_create_missing_title_returns_400(self):
        resp = self._post({"description": "No title"})
        self.assertEqual(resp.status_code, 400)

    def test_create_blank_title_returns_400(self):
        resp = self._post({"title": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_create_persists_to_db(self):
        self._post({"title": "Persist Check", "description": "desc"})
        self.assertEqual(MockOpportunity.objects.filter(title="Persist Check").count(), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Admin CRUD API — delete
# ─────────────────────────────────────────────────────────────────────────────

@override_settings(RATELIMIT_ENABLE=False)
class AdminMockDeleteTestCase(TestCase):
    """Tests for DELETE /api/admin/mock-opportunities/<uuid>."""

    def setUp(self):
        self.client = Client()
        _, pw = _make_admin()
        self.token = _token(self.client, "admin", pw)
        _, spw = _make_student()
        self.student_token = _token(self.client, "student", spw)
        self.opp = _make_opportunity()
        self.url = f"/api/admin/mock-opportunities/{self.opp.id}"

    def _auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {token or self.token}"}

    def test_delete_success(self):
        resp = self.client.delete(self.url, **self._auth())
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(MockOpportunity.objects.filter(id=self.opp.id).exists())

    def test_delete_not_found(self):
        missing = uuid.uuid4()
        resp = self.client.delete(
            f"/api/admin/mock-opportunities/{missing}", **self._auth()
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_requires_auth(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_delete_requires_admin(self):
        resp = self.client.delete(self.url, **self._auth(self.student_token))
        self.assertEqual(resp.status_code, 403)

    def test_delete_then_detail_page_returns_404(self):
        """Core demo behaviour: deleted opportunity → detail page 404."""
        detail_url = f"/mock/offers/{self.opp.id}/"
        self.assertEqual(self.client.get(detail_url).status_code, 200)

        self.client.delete(self.url, **self._auth())

        self.assertEqual(self.client.get(detail_url).status_code, 404)
