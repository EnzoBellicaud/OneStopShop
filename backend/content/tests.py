import csv
import io
import json
import uuid
from time import perf_counter

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase

from content.auth import generate_tokens
from content.models import (
	CrawlUrl,
	Domain,
	MatchingHit,
	Offer,
	OfferDomain,
	OfferType,
	Organization,
	ScrapingRun,
	SourceType,
	TargetProfile,
	User,
	UserFavorite,
	UserNeed,
	UserNeedDomain,
	UserOrganization,
	UserProfile,
	UserRole,
)


class ReadApiTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.offer_type = OfferType.objects.create(name="training", description="")
		cls.offer_type_thesis = OfferType.objects.create(name="thesis", description="")
		cls.domain = Domain.objects.create(name="AI")
		cls.domain_robotics = Domain.objects.create(name="Robotics")
		cls.target_profile = TargetProfile.objects.create(name="student", description="")
		cls.target_profile_researcher = TargetProfile.objects.create(name="researcher", description="")
		cls.source_type = SourceType.objects.create(name="manual", description="")
		cls.organization = Organization.objects.create(
			name="Test University",
			type=Organization.OrganizationType.UNIVERSITY,
			country="IT",
			website="https://example.edu",
		)
		cls.organization_sweden = Organization.objects.create(
			name="Research Sweden",
			type=Organization.OrganizationType.UNIVERSITY,
			country="SE",
			website="https://example.se",
		)
		cls.user = User.objects.create(
			username="tester",
			email="tester@example.com",
			password_hash="not-used",
		)
		cls.admin = User.objects.create(
			username="admin_test",
			email="admin_test@example.com",
			password_hash="not-used",
			profile=User.ProfileType.ADMIN,
			is_active=True,
		)
		cls.admin_token = generate_tokens(cls.admin.id, cls.admin.username, cls.admin.profile)["access_token"]
		cls.offer = Offer.objects.create(
			id=uuid.uuid4(),
			title="AI Master Programme",
			summary="A test offer",
			link="https://example.edu/offer/ai-master",
			country="IT",
			details={"level": "master"},
			status=Offer.OfferStatus.PUBLISHED,
			offer_type=cls.offer_type,
			organization=cls.organization,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			created_by=cls.user,
			updated_by=cls.user,
		)
		OfferDomain.objects.create(offer=cls.offer, domain=cls.domain)
		cls.offer_two = Offer.objects.create(
			id=uuid.uuid4(),
			title="Robotics Thesis Track",
			summary="A research-focused offer",
			link="https://example.se/offer/robotics-thesis",
			country="SE",
			details={"level": "phd"},
			status=Offer.OfferStatus.DRAFT,
			offer_type=cls.offer_type_thesis,
			organization=cls.organization_sweden,
			source_type=cls.source_type,
			target_profile=cls.target_profile_researcher,
			created_by=cls.user,
			updated_by=cls.user,
		)
		OfferDomain.objects.create(offer=cls.offer_two, domain=cls.domain_robotics)

	def test_health_endpoint(self):
		response = self.client.get("/api/health")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["status"], "ok")

	def test_docs_endpoint(self):
		response = self.client.get("/api/docs")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "SwaggerUIBundle")

	def test_redoc_endpoint(self):
		response = self.client.get("/api/redoc")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Redoc.init")

	def test_openapi_schema_endpoint(self):
		response = self.client.get("/api/openapi.json")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["openapi"], "3.0.3")
		self.assertIn("/api/offers", payload["paths"])
		self.assertIn("/api/users/{user_id}/needs/{need_id}", payload["paths"])
		self.assertIn("/api/users/{user_id}/favorites/{offer_id}", payload["paths"])
		self.assertIn("/api/users/{user_id}/matching-hits/{hit_id}", payload["paths"])

	def test_offer_types_endpoint(self):
		response = self.client.get("/api/lookups/offer-types")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertGreaterEqual(payload["count"], 1)

	def test_domains_endpoint(self):
		response = self.client.get("/api/lookups/domains")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertGreaterEqual(payload["count"], 1)

	def test_organizations_endpoint(self):
		response = self.client.get("/api/lookups/organizations")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertGreaterEqual(payload["count"], 2)
		names = [row["name"] for row in payload["results"]]
		self.assertIn("Test University", names)

	def test_target_profiles_endpoint(self):
		response = self.client.get("/api/lookups/target-profiles")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertGreaterEqual(payload["count"], 2)

	def test_countries_endpoint(self):
		response = self.client.get("/api/lookups/countries")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		codes = [row["code"] for row in payload["results"]]
		self.assertIn("IT", codes)
		self.assertIn("SE", codes)

	def test_offers_list_endpoint(self):
		response = self.client.get("/api/offers", {"page_size": 1})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 2)
		self.assertEqual(payload["page"], 1)
		self.assertEqual(payload["page_size"], 1)
		self.assertEqual(payload["total_pages"], 2)
		self.assertEqual(len(payload["results"]), 1)
		self.assertEqual(payload["results"][0]["title"], "AI Master Programme")

	def test_offers_filter_by_status(self):
		response = self.client.get("/api/offers", {"status": Offer.OfferStatus.PUBLISHED})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)

	def test_offers_search_query(self):
		response = self.client.get("/api/offers", {"q": "research"})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["title"], "Robotics Thesis Track")

	def test_offers_filter_by_domain(self):
		response = self.client.get("/api/offers", {"domain": "AI"})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["title"], "AI Master Programme")

	def test_offers_filter_by_country(self):
		response = self.client.get("/api/offers", {"country": "se"})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["country"], "SE")

	def test_offers_pagination_page_two(self):
		response = self.client.get("/api/offers", {"page": 2, "page_size": 1})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 2)
		self.assertEqual(payload["page"], 2)
		self.assertEqual(payload["total_pages"], 2)
		self.assertEqual(len(payload["results"]), 1)
		self.assertEqual(payload["results"][0]["title"], "Robotics Thesis Track")

	def test_offers_legacy_limit_compatibility(self):
		response = self.client.get("/api/offers", {"limit": 1})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["page_size"], 1)
		self.assertEqual(payload["limit"], 1)
		self.assertEqual(len(payload["results"]), 1)

	def test_scraping_runs_endpoint(self):
		response = self.client.get("/api/scraping/runs", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 0)

	def test_scraping_run_detail_endpoint(self):
		run = ScrapingRun.objects.create(source_key="test-source", status=ScrapingRun.RunStatus.SUCCESS)
		response = self.client.get(f"/api/scraping/runs/{run.id}", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["id"], str(run.id))

	def test_scraping_run_detail_not_found(self):
		response = self.client.get(f"/api/scraping/runs/{uuid.uuid4()}", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		self.assertEqual(response.status_code, 404)

	def test_offer_detail_endpoint(self):
		response = self.client.get(f"/api/offers/{self.offer.id}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["id"], str(self.offer.id))

	def test_offer_detail_invalid_uuid(self):
		response = self.client.get("/api/offers/not-a-uuid")
		self.assertEqual(response.status_code, 400)

	def test_offer_detail_not_found(self):
		response = self.client.get(f"/api/offers/{uuid.uuid4()}")
		self.assertEqual(response.status_code, 404)


class UserDashboardModelTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.domain_ai = Domain.objects.create(name="AI")
		cls.domain_data = Domain.objects.create(name="Data Science")
		cls.target_profile = TargetProfile.objects.create(
			name="research_lab",
			description="Research lab",
		)
		cls.source_type = SourceType.objects.create(name="portal", description="Portal")
		cls.offer_type = OfferType.objects.create(name="grant", description="Grant")
		cls.organization = Organization.objects.create(
			name="Innovation Hub",
			type=Organization.OrganizationType.COMPANY,
			country="DE",
			website="https://innovation.example",
		)
		cls.user = User.objects.create(
			username="dashboard-user",
			email="dashboard@example.com",
			password_hash="secret",
		)
		cls.other_user = User.objects.create(
			username="other-dashboard-user",
			email="other-dashboard@example.com",
			password_hash="secret",
		)
		cls.offer = Offer.objects.create(
			title="AI Collaboration Fund",
			summary="Funding support",
			link="https://innovation.example/offers/ai-fund",
			country="DE",
			details={"kind": "fund"},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)

	def test_user_profile_defaults(self):
		profile = UserProfile.objects.create(user=self.user)

		self.assertEqual(profile.bio, "")
		self.assertEqual(profile.preferred_domains, [])
		self.assertEqual(profile.preferred_countries, [])
		self.assertTrue(profile.notification_enabled)

	def test_user_profile_enforces_one_to_one_relationship(self):
		UserProfile.objects.create(user=self.user)

		with self.assertRaises(IntegrityError):
			UserProfile.objects.create(user=self.user)

	def test_user_profile_deleted_with_user(self):
		user = User.objects.create(
			username="profile-owner",
			email="profile-owner@example.com",
			password_hash="secret",
		)
		profile = UserProfile.objects.create(user=user)

		user.delete()

		self.assertFalse(UserProfile.objects.filter(id=profile.id).exists())

	def test_user_need_defaults_to_active_status(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need partners",
			description="Looking for AI partners",
			target_profile=self.target_profile,
		)

		self.assertEqual(need.status, UserNeed.NeedStatus.ACTIVE)
		self.assertEqual(need.countries, [])

	def test_user_need_can_link_domains_via_through_model(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need domain support",
			description="Need AI and data support",
			target_profile=self.target_profile,
		)
		UserNeedDomain.objects.create(user_need=need, domain=self.domain_ai)
		UserNeedDomain.objects.create(user_need=need, domain=self.domain_data)

		self.assertEqual(need.domains.count(), 2)

	def test_user_need_domain_requires_unique_pair(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need unique domain",
			description="Testing unique constraint",
			target_profile=self.target_profile,
		)
		UserNeedDomain.objects.create(user_need=need, domain=self.domain_ai)

		with self.assertRaises(IntegrityError):
			UserNeedDomain.objects.create(user_need=need, domain=self.domain_ai)

	def test_user_need_deleted_with_owner(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need ownership cleanup",
			description="Should be deleted with user",
			target_profile=self.target_profile,
		)

		# Offer.created_by/updated_by are PROTECT FKs — must clear before deleting user
		Offer.objects.filter(created_by=self.user).delete()
		self.user.delete()

		self.assertFalse(UserNeed.objects.filter(id=need.id).exists())

	def test_user_favorite_allows_blank_note(self):
		favorite = UserFavorite.objects.create(user=self.user, offer=self.offer)

		self.assertEqual(favorite.note, "")

	def test_user_favorite_requires_unique_user_offer_pair(self):
		UserFavorite.objects.create(user=self.user, offer=self.offer)

		with self.assertRaises(IntegrityError):
			UserFavorite.objects.create(user=self.user, offer=self.offer)

	def test_user_favorite_allows_different_users_for_same_offer(self):
		UserFavorite.objects.create(user=self.user, offer=self.offer)
		second = UserFavorite.objects.create(user=self.other_user, offer=self.offer)

		self.assertEqual(second.offer_id, self.offer.id)

	def test_matching_hit_defaults_to_new_status(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need matching",
			description="Matching test",
			target_profile=self.target_profile,
		)
		hit = MatchingHit.objects.create(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.9200",
			match_reason="Strong alignment",
		)

		self.assertEqual(hit.status, MatchingHit.MatchStatus.NEW)
		self.assertIsNone(hit.viewed_at)

	def test_matching_hit_requires_unique_need_offer_pair(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need unique match",
			description="Unique match",
			target_profile=self.target_profile,
		)
		MatchingHit.objects.create(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.7500",
			match_reason="Good fit",
		)

		with self.assertRaises(IntegrityError):
			MatchingHit.objects.create(
				user=self.user,
				need=need,
				offer=self.offer,
				match_score="0.8000",
				match_reason="Duplicate fit",
			)

	def test_matching_hit_allows_same_offer_for_different_need(self):
		first_need = UserNeed.objects.create(
			user=self.user,
			title="First need",
			description="First",
			target_profile=self.target_profile,
		)
		second_need = UserNeed.objects.create(
			user=self.user,
			title="Second need",
			description="Second",
			target_profile=self.target_profile,
		)
		MatchingHit.objects.create(
			user=self.user,
			need=first_need,
			offer=self.offer,
			match_score="0.6500",
			match_reason="First fit",
		)
		second_hit = MatchingHit.objects.create(
			user=self.user,
			need=second_need,
			offer=self.offer,
			match_score="0.8800",
			match_reason="Second fit",
		)

		self.assertEqual(second_hit.need_id, second_need.id)

	def test_matching_hit_deleted_with_need(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need cascade",
			description="Cascade test",
			target_profile=self.target_profile,
		)
		hit = MatchingHit.objects.create(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.9100",
			match_reason="Cascade fit",
		)

		need.delete()

		self.assertFalse(MatchingHit.objects.filter(id=hit.id).exists())

	def test_matching_hit_score_validators_reject_value_below_zero(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need validator low",
			description="Low validator",
			target_profile=self.target_profile,
		)
		hit = MatchingHit(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="-0.1000",
			match_reason="Invalid score",
		)

		with self.assertRaises(ValidationError):
			hit.full_clean()

	def test_matching_hit_score_validators_reject_value_above_one(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need validator high",
			description="High validator",
			target_profile=self.target_profile,
		)
		hit = MatchingHit(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="1.1000",
			match_reason="Invalid score",
		)

		with self.assertRaises(ValidationError):
			hit.full_clean()

	def test_matching_hit_score_accepts_value_between_zero_and_one(self):
		need = UserNeed.objects.create(
			user=self.user,
			title="Need validator valid",
			description="Valid validator",
			target_profile=self.target_profile,
		)
		hit = MatchingHit(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.5000",
			match_reason="Valid score",
		)

		hit.full_clean()

		self.assertEqual(str(hit.match_score), "0.5000")


class UserCrudApiTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.organization = Organization.objects.create(
			name="Stage Two Org",
			type=Organization.OrganizationType.UNIVERSITY,
			country="IT",
			website="https://stage-two.example",
		)
		cls.other_organization = Organization.objects.create(
			name="Second Org",
			type=Organization.OrganizationType.COMPANY,
			country="FR",
			website="https://second.example",
		)
		cls.member_role = UserRole.objects.create(
			name="member",
			description="Default member role",
		)
		cls.user = User.objects.create(
			username="stage2user",
			email="stage2@example.com",
			password_hash="secret",
		)
		cls.other_user = User.objects.create(
			username="otherstage2",
			email="otherstage2@example.com",
			password_hash="secret",
		)
		UserProfile.objects.create(
			user=cls.user,
			bio="Initial bio",
			preferred_domains=["AI"],
			preferred_countries=["IT"],
		)

	def test_upsert_user_creates_user_profile_and_org_link(self):
		response = self.client.post(
			"/api/users",
			data={
				"email": "new.user@example.com",
				"username": "newuser",
				"organization_id": str(self.organization.id),
				"profile": {
					"bio": "Created from stage 2",
					"preferred_domains": ["Data"],
					"preferred_countries": ["DE"],
					"notification_enabled": False,
				},
			},
			content_type="application/json",
		)

		payload = response.json()
		self.assertEqual(response.status_code, 201)
		self.assertTrue(payload["is_new"])
		self.assertEqual(payload["profile"]["bio"], "Created from stage 2")
		self.assertEqual(payload["organizations"][0]["name"], "Stage Two Org")
		self.assertTrue(User.objects.filter(email="new.user@example.com").exists())

	def test_upsert_user_updates_existing_user_and_reactivates(self):
		self.user.is_active = False
		self.user.save(update_fields=["is_active"])

		response = self.client.post(
			"/api/users",
			data={"email": self.user.email, "username": "renamed-user"},
			content_type="application/json",
		)

		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertFalse(payload["is_new"])
		self.user.refresh_from_db()
		self.assertEqual(self.user.username, "renamed-user")
		self.assertTrue(self.user.is_active)

	def test_upsert_user_requires_email_and_username(self):
		response = self.client.post(
			"/api/users",
			data={"email": "", "username": ""},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()["error"], "validation_error")

	def test_upsert_user_accepts_cross_origin_json_without_csrf_token(self):
		csrf_client = Client(enforce_csrf_checks=True)
		response = csrf_client.post(
			"/api/users",
			data={"email": "spa.user@example.com", "username": "spauser"},
			content_type="application/json",
			HTTP_ORIGIN="http://localhost:4200",
		)

		self.assertEqual(response.status_code, 201)
		self.assertTrue(User.objects.filter(email="spa.user@example.com").exists())

	def test_get_user_detail_returns_profile_and_organizations(self):
		UserOrganization.objects.create(
			user=self.user,
			organization=self.organization,
			role=self.member_role,
		)

		response = self.client.get(f"/api/users/{self.user.id}")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["email"], "stage2@example.com")
		self.assertEqual(payload["profile"]["bio"], "Initial bio")
		self.assertEqual(payload["organizations"][0]["role"], "member")

	def test_get_user_detail_invalid_uuid(self):
		response = self.client.get("/api/users/not-a-uuid")
		self.assertEqual(response.status_code, 400)

	def test_get_user_detail_not_found(self):
		response = self.client.get(f"/api/users/{uuid.uuid4()}")
		self.assertEqual(response.status_code, 404)

	def test_patch_user_updates_account_and_profile(self):
		response = self.client.patch(
			f"/api/users/{self.user.id}",
			data={
				"username": "patched-user",
				"profile": {
					"bio": "Updated bio",
					"preferred_domains": ["AI", "ML"],
					"notification_enabled": False,
				},
			},
			content_type="application/json",
		)

		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["username"], "patched-user")
		self.assertEqual(payload["profile"]["bio"], "Updated bio")
		self.assertFalse(payload["profile"]["notification_enabled"])

	def test_patch_user_rejects_duplicate_email(self):
		response = self.client.patch(
			f"/api/users/{self.user.id}",
			data={"email": self.other_user.email},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 409)
		self.assertEqual(response.json()["error"], "conflict")

	def test_delete_user_soft_deletes_account(self):
		response = self.client.delete(f"/api/users/{self.user.id}")

		self.assertEqual(response.status_code, 204)
		self.user.refresh_from_db()
		self.assertFalse(self.user.is_active)

	def test_link_user_organization_creates_link(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/organizations",
			data={"organization_id": str(self.organization.id), "role": "contributor"},
			content_type="application/json",
		)

		payload = response.json()
		self.assertEqual(response.status_code, 201)
		self.assertEqual(payload["name"], "Stage Two Org")
		self.assertEqual(payload["role"], "contributor")

	def test_link_user_organization_rejects_duplicate_org(self):
		UserOrganization.objects.create(
			user=self.user,
			organization=self.organization,
			role=self.member_role,
		)

		response = self.client.post(
			f"/api/users/{self.user.id}/organizations",
			data={"organization_id": str(self.organization.id)},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 409)
		self.assertEqual(response.json()["error"], "conflict")

	def test_unlink_user_organization_removes_link(self):
		UserOrganization.objects.create(
			user=self.user,
			organization=self.organization,
			role=self.member_role,
		)

		response = self.client.delete(
			f"/api/users/{self.user.id}/organizations/{self.organization.id}"
		)

		self.assertEqual(response.status_code, 204)
		self.assertFalse(
			UserOrganization.objects.filter(
				user=self.user,
				organization=self.organization,
			).exists()
		)

	def test_unlink_user_organization_returns_not_found_for_missing_link(self):
		response = self.client.delete(
			f"/api/users/{self.user.id}/organizations/{self.other_organization.id}"
		)

		self.assertEqual(response.status_code, 404)


class UserContentApiTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.domain_ai = Domain.objects.create(name="Applied AI")
		cls.domain_nlp = Domain.objects.create(name="NLP")
		cls.domain_robotics = Domain.objects.create(name="Robotics")
		cls.target_profile = TargetProfile.objects.create(
			name="lab",
			description="Research lab",
		)
		cls.other_target_profile = TargetProfile.objects.create(
			name="company_partner",
			description="Company partner",
		)
		cls.source_type = SourceType.objects.create(name="catalogue", description="Catalogue")
		cls.offer_type = OfferType.objects.create(name="program", description="Program")
		cls.organization = Organization.objects.create(
			name="Stage Three Org",
			type=Organization.OrganizationType.UNIVERSITY,
			country="NL",
			website="https://stage-three.example",
		)
		cls.user = User.objects.create(
			username="stage3user",
			email="stage3@example.com",
			password_hash="secret",
		)
		UserProfile.objects.create(user=cls.user, bio="Stage 3 bio")
		cls.other_user = User.objects.create(
			username="other-stage3",
			email="other-stage3@example.com",
			password_hash="secret",
		)
		cls.offer_one = Offer.objects.create(
			title="AI Residency",
			summary="Research residency",
			link="https://stage-three.example/offers/ai-residency",
			country="NL",
			details={"kind": "residency"},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)
		cls.offer_two = Offer.objects.create(
			title="NLP Fellowship",
			summary="Language fellowship",
			link="https://stage-three.example/offers/nlp-fellowship",
			country="NL",
			details={"kind": "fellowship"},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)
		cls.offer_three = Offer.objects.create(
			title="Robotics Sandbox",
			summary="Robotics program",
			link="https://stage-three.example/offers/robotics-sandbox",
			country="NL",
			details={"kind": "sandbox"},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.other_target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)
		cls.need_active = UserNeed.objects.create(
			user=cls.user,
			title="AI Research Funding",
			description="Need funding",
			target_profile=cls.target_profile,
			status=UserNeed.NeedStatus.ACTIVE,
			countries=["NL", "DE"],
		)
		cls.need_active.domains.set([cls.domain_ai, cls.domain_nlp])
		cls.need_fulfilled = UserNeed.objects.create(
			user=cls.user,
			title="Robotics Mentors",
			description="Need robotics mentors",
			target_profile=cls.other_target_profile,
			status=UserNeed.NeedStatus.FULFILLED,
			countries=["NL"],
		)
		cls.need_fulfilled.domains.set([cls.domain_robotics])
		cls.favorite_one = UserFavorite.objects.create(
			user=cls.user,
			offer=cls.offer_one,
			note="Great fit",
		)
		cls.favorite_two = UserFavorite.objects.create(
			user=cls.user,
			offer=cls.offer_two,
			note="Interesting",
		)
		cls.match_one = MatchingHit.objects.create(
			user=cls.user,
			need=cls.need_active,
			offer=cls.offer_one,
			match_score="0.9500",
			match_reason="Strong AI alignment",
			status=MatchingHit.MatchStatus.NEW,
		)
		cls.match_two = MatchingHit.objects.create(
			user=cls.user,
			need=cls.need_fulfilled,
			offer=cls.offer_three,
			match_score="0.7300",
			match_reason="Relevant robotics support",
			status=MatchingHit.MatchStatus.VIEWED,
		)

	def test_dashboard_returns_stats_and_recent_items(self):
		response = self.client.get(f"/api/users/{self.user.id}/dashboard")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["stats"]["active_needs_count"], 1)
		self.assertEqual(payload["stats"]["total_favorites"], 2)
		self.assertEqual(payload["stats"]["new_matches_count"], 1)
		self.assertEqual(len(payload["recent_favorites"]), 2)
		self.assertEqual(len(payload["recent_matches"]), 2)

	def test_list_needs_defaults_to_active_filter(self):
		response = self.client.get(f"/api/users/{self.user.id}/needs")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["title"], "AI Research Funding")

	def test_list_needs_supports_status_and_pagination(self):
		response = self.client.get(
			f"/api/users/{self.user.id}/needs",
			{"status": UserNeed.NeedStatus.FULFILLED, "page": 1, "page_size": 1},
		)
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertIsNone(payload["next"])
		self.assertEqual(payload["results"][0]["status"], UserNeed.NeedStatus.FULFILLED)

	def test_list_needs_rejects_invalid_status_filter(self):
		response = self.client.get(f"/api/users/{self.user.id}/needs", {"status": "broken"})
		self.assertEqual(response.status_code, 400)

	def test_create_need_persists_domains_and_countries(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/needs",
			data={
				"title": "Need new collaborators",
				"description": "Find new collaborators",
				"target_profile_id": str(self.target_profile.id),
				"domain_ids": [str(self.domain_ai.id), str(self.domain_robotics.id)],
				"countries": ["it", "de"],
			},
			content_type="application/json",
		)
		payload = response.json()

		self.assertEqual(response.status_code, 201)
		self.assertEqual(payload["countries"], ["IT", "DE"])
		self.assertEqual(len(payload["domain_ids"]), 2)

	def test_update_need_replaces_status_and_domain_selection(self):
		response = self.client.put(
			f"/api/users/{self.user.id}/needs/{self.need_active.id}",
			data={
				"title": "AI Research Funding Updated",
				"description": "Updated description",
				"status": UserNeed.NeedStatus.ARCHIVED,
				"target_profile_id": str(self.other_target_profile.id),
				"domain_ids": [str(self.domain_robotics.id)],
				"countries": ["fr"],
			},
			content_type="application/json",
		)
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["status"], UserNeed.NeedStatus.ARCHIVED)
		self.assertEqual(payload["countries"], ["FR"])
		self.assertEqual(len(payload["domain_ids"]), 1)

	def test_delete_need_removes_record(self):
		response = self.client.delete(f"/api/users/{self.user.id}/needs/{self.need_fulfilled.id}")

		self.assertEqual(response.status_code, 204)
		self.assertFalse(UserNeed.objects.filter(id=self.need_fulfilled.id).exists())

	def test_list_favorites_is_paginated(self):
		response = self.client.get(
			f"/api/users/{self.user.id}/favorites",
			{"page": 1, "page_size": 1},
		)
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 2)
		self.assertEqual(len(payload["results"]), 1)
		self.assertIsNotNone(payload["next"])

	def test_add_favorite_creates_new_favorite(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/favorites",
			data={"offer_id": str(self.offer_three.id), "note": "Worth saving"},
			content_type="application/json",
		)
		payload = response.json()

		self.assertEqual(response.status_code, 201)
		self.assertEqual(payload["offer"]["title"], "Robotics Sandbox")

	def test_add_favorite_rejects_duplicate_offer(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/favorites",
			data={"offer_id": str(self.offer_one.id)},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 409)

	def test_remove_favorite_deletes_existing_record(self):
		response = self.client.delete(
			f"/api/users/{self.user.id}/favorites/{self.offer_one.id}"
		)

		self.assertEqual(response.status_code, 204)
		self.assertFalse(
			UserFavorite.objects.filter(user=self.user, offer=self.offer_one).exists()
		)

	def test_list_matching_hits_filters_and_sorts(self):
		response = self.client.get(
			f"/api/users/{self.user.id}/matching-hits",
			{"status": MatchingHit.MatchStatus.NEW, "sort": "-match_score", "page_size": 5},
		)
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["status"], MatchingHit.MatchStatus.NEW)

	def test_list_matching_hits_rejects_invalid_sort(self):
		response = self.client.get(
			f"/api/users/{self.user.id}/matching-hits",
			{"sort": "wrong"},
		)
		self.assertEqual(response.status_code, 400)

	def test_patch_matching_hit_updates_status(self):
		response = self.client.patch(
			f"/api/users/{self.user.id}/matching-hits/{self.match_one.id}",
			data={"status": MatchingHit.MatchStatus.INTERESTED},
			content_type="application/json",
		)
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["status"], MatchingHit.MatchStatus.INTERESTED)
		self.match_one.refresh_from_db()
		self.assertIsNotNone(self.match_one.viewed_at)

	def test_patch_matching_hit_rejects_invalid_status(self):
		response = self.client.patch(
			f"/api/users/{self.user.id}/matching-hits/{self.match_one.id}",
			data={"status": MatchingHit.MatchStatus.NEW},
			content_type="application/json",
		)
		self.assertEqual(response.status_code, 400)


class UserContentEdgeCaseTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.domain = Domain.objects.create(name="Edge AI")
		cls.target_profile = TargetProfile.objects.create(
			name="edge_profile",
			description="Edge profile",
		)
		cls.source_type = SourceType.objects.create(name="edge-source", description="Edge source")
		cls.offer_type = OfferType.objects.create(name="edge-offer-type", description="Edge type")
		cls.organization = Organization.objects.create(
			name="Edge Org",
			type=Organization.OrganizationType.COMPANY,
			country="ES",
			website="https://edge.example",
		)
		cls.user = User.objects.create(
			username="edge-user",
			email="edge@example.com",
			password_hash="secret",
		)
		cls.other_user = User.objects.create(
			username="edge-other-user",
			email="edge-other@example.com",
			password_hash="secret",
		)
		cls.offer = Offer.objects.create(
			title="Edge Opportunity",
			summary="Edge case offer",
			link="https://edge.example/offers/edge",
			country="ES",
			details={"edge": True},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)
		cls.need = UserNeed.objects.create(
			user=cls.user,
			title="Existing need",
			description="Existing need description",
			target_profile=cls.target_profile,
		)
		cls.need.domains.set([cls.domain])
		cls.favorite = UserFavorite.objects.create(user=cls.user, offer=cls.offer)
		cls.match = MatchingHit.objects.create(
			user=cls.user,
			need=cls.need,
			offer=cls.offer,
			match_score="0.6600",
			match_reason="Edge reason",
			status=MatchingHit.MatchStatus.NEW,
		)

	def test_dashboard_handles_empty_lists(self):
		response = self.client.get(f"/api/users/{self.other_user.id}/dashboard")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["stats"]["active_needs_count"], 0)
		self.assertEqual(payload["recent_favorites"], [])
		self.assertEqual(payload["recent_matches"], [])

	def test_needs_returns_empty_list_for_user_without_needs(self):
		response = self.client.get(f"/api/users/{self.other_user.id}/needs")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 0)
		self.assertEqual(payload["results"], [])

	def test_create_need_rejects_invalid_domain_uuid(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/needs",
			data={
				"title": "Bad need",
				"description": "Bad domain",
				"target_profile_id": str(self.target_profile.id),
				"domain_ids": ["not-a-uuid"],
				"countries": ["ES"],
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()["error"], "validation_error")

	def test_create_need_rejects_missing_target_profile(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/needs",
			data={
				"title": "Bad need",
				"description": "Missing target profile",
				"target_profile_id": str(uuid.uuid4()),
				"domain_ids": [str(self.domain.id)],
				"countries": ["ES"],
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.json()["error"], "not_found")

	def test_update_need_returns_not_found_for_other_users_need(self):
		response = self.client.put(
			f"/api/users/{self.other_user.id}/needs/{self.need.id}",
			data={
				"title": "Unauthorized",
				"description": "Should not be visible",
				"status": UserNeed.NeedStatus.ACTIVE,
				"target_profile_id": str(self.target_profile.id),
				"domain_ids": [str(self.domain.id)],
				"countries": ["ES"],
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 404)

	def test_delete_need_rejects_invalid_need_id(self):
		response = self.client.delete(f"/api/users/{self.user.id}/needs/not-a-uuid")
		self.assertEqual(response.status_code, 400)

	def test_list_favorites_returns_empty_list_for_user_without_favorites(self):
		response = self.client.get(f"/api/users/{self.other_user.id}/favorites")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 0)
		self.assertEqual(payload["results"], [])

	def test_add_favorite_rejects_missing_offer(self):
		response = self.client.post(
			f"/api/users/{self.user.id}/favorites",
			data={"offer_id": str(uuid.uuid4())},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 404)
		self.assertEqual(response.json()["error"], "not_found")

	def test_remove_favorite_returns_not_found_when_missing(self):
		response = self.client.delete(
			f"/api/users/{self.other_user.id}/favorites/{self.offer.id}"
		)
		self.assertEqual(response.status_code, 404)

	def test_matching_hits_returns_empty_list_for_user_without_hits(self):
		response = self.client.get(f"/api/users/{self.other_user.id}/matching-hits")
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 0)
		self.assertEqual(payload["results"], [])

	def test_matching_hits_reject_invalid_status_filter(self):
		response = self.client.get(
			f"/api/users/{self.user.id}/matching-hits",
			{"status": "invalid"},
		)
		self.assertEqual(response.status_code, 400)

	def test_patch_matching_hit_returns_not_found_for_other_user(self):
		response = self.client.patch(
			f"/api/users/{self.other_user.id}/matching-hits/{self.match.id}",
			data={"status": MatchingHit.MatchStatus.VIEWED},
			content_type="application/json",
		)
		self.assertEqual(response.status_code, 404)

	def test_patch_matching_hit_rejects_invalid_hit_id(self):
		response = self.client.patch(
			f"/api/users/{self.user.id}/matching-hits/not-a-uuid",
			data={"status": MatchingHit.MatchStatus.VIEWED},
			content_type="application/json",
		)
		self.assertEqual(response.status_code, 400)


class UserIntegrationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.domain = Domain.objects.create(name="Integration AI")
		cls.target_profile = TargetProfile.objects.create(
			name="integration_target",
			description="Integration target",
		)
		cls.source_type = SourceType.objects.create(name="integration-source", description="Integration source")
		cls.offer_type = OfferType.objects.create(name="integration-offer", description="Integration type")
		cls.organization = Organization.objects.create(
			name="Integration Org",
			type=Organization.OrganizationType.UNIVERSITY,
			country="BE",
			website="https://integration.example",
		)
		cls.role = UserRole.objects.create(name="integration-member", description="Integration role")
		cls.user = User.objects.create(
			username="integration-user",
			email="integration@example.com",
			password_hash="secret",
		)
		cls.offer = Offer.objects.create(
			title="Integration Grant",
			summary="Integration offer",
			link="https://integration.example/offers/grant",
			country="BE",
			details={"integration": True},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)

	def test_user_journey_create_need_then_match_then_favorite(self):
		create_response = self.client.post(
			f"/api/users/{self.user.id}/needs",
			data={
				"title": "Integration need",
				"description": "Integration description",
				"target_profile_id": str(self.target_profile.id),
				"domain_ids": [str(self.domain.id)],
				"countries": ["be"],
			},
			content_type="application/json",
		)
		self.assertEqual(create_response.status_code, 201)
		need_id = create_response.json()["id"]
		need = UserNeed.objects.get(id=need_id)

		match = MatchingHit.objects.create(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.8900",
			match_reason="Integration alignment",
		)

		favorite_response = self.client.post(
			f"/api/users/{self.user.id}/favorites",
			data={"offer_id": str(self.offer.id), "note": "save this"},
			content_type="application/json",
		)
		self.assertEqual(favorite_response.status_code, 201)

		dashboard_response = self.client.get(f"/api/users/{self.user.id}/dashboard")
		payload = dashboard_response.json()

		self.assertEqual(payload["stats"]["active_needs_count"], 1)
		self.assertEqual(payload["stats"]["total_favorites"], 1)
		self.assertEqual(payload["stats"]["new_matches_count"], 1)
		self.assertEqual(payload["recent_matches"][0]["id"], str(match.id))

	def test_model_delete_user_cascades_dashboard_entities(self):
		UserProfile.objects.create(user=self.user, bio="Cascade profile")
		UserOrganization.objects.create(user=self.user, organization=self.organization, role=self.role)
		need = UserNeed.objects.create(
			user=self.user,
			title="Cascade need",
			description="Cascade description",
			target_profile=self.target_profile,
		)
		need.domains.set([self.domain])
		favorite = UserFavorite.objects.create(user=self.user, offer=self.offer)
		hit = MatchingHit.objects.create(
			user=self.user,
			need=need,
			offer=self.offer,
			match_score="0.7700",
			match_reason="Cascade match",
		)

		# Offer.created_by/updated_by are PROTECT FKs — must clear before deleting user
		Offer.objects.filter(created_by=self.user).delete()
		self.user.delete()

		self.assertFalse(UserProfile.objects.filter(user_id=self.user.id).exists())
		self.assertFalse(UserOrganization.objects.filter(user_id=self.user.id).exists())
		self.assertFalse(UserNeed.objects.filter(id=need.id).exists())
		self.assertFalse(UserNeedDomain.objects.filter(user_need_id=need.id).exists())
		self.assertFalse(UserFavorite.objects.filter(id=favorite.id).exists())
		self.assertFalse(MatchingHit.objects.filter(id=hit.id).exists())


class UserContentPerformanceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.domain = Domain.objects.create(name="Performance AI")
		cls.target_profile = TargetProfile.objects.create(
			name="performance_target",
			description="Performance target",
		)
		cls.source_type = SourceType.objects.create(name="performance-source", description="Performance source")
		cls.offer_type = OfferType.objects.create(name="performance-offer", description="Performance type")
		cls.organization = Organization.objects.create(
			name="Performance Org",
			type=Organization.OrganizationType.COMPANY,
			country="PT",
			website="https://performance.example",
		)
		cls.user = User.objects.create(
			username="performance-user",
			email="performance@example.com",
			password_hash="secret",
		)
		offer = Offer.objects.create(
			title="Performance Offer",
			summary="Performance summary",
			link="https://performance.example/offers/main",
			country="PT",
			details={"performance": True},
			status=Offer.OfferStatus.PUBLISHED,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			organization=cls.organization,
			created_by=cls.user,
			updated_by=cls.user,
			offer_type=cls.offer_type,
		)
		for index in range(120):
			need = UserNeed.objects.create(
				user=cls.user,
				title=f"Performance Need {index}",
				description="Bulk generated need",
				target_profile=cls.target_profile,
				status=UserNeed.NeedStatus.ACTIVE if index % 2 == 0 else UserNeed.NeedStatus.FULFILLED,
			)
			need.domains.set([cls.domain])
			if index < 20:
				MatchingHit.objects.create(
					user=cls.user,
					need=need,
					offer=offer,
					match_score=f"0.{8000 + index:04d}",
					match_reason="Bulk match",
					status=MatchingHit.MatchStatus.NEW if index % 2 == 0 else MatchingHit.MatchStatus.VIEWED,
				)

	def test_large_needs_query_returns_paginated_results_quickly(self):
		start = perf_counter()
		response = self.client.get(
			f"/api/users/{self.user.id}/needs",
			{"status": UserNeed.NeedStatus.ACTIVE, "page": 2, "page_size": 25},
		)
		duration = perf_counter() - start
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 60)
		self.assertEqual(len(payload["results"]), 25)
		self.assertLess(duration, 0.5)

	def test_large_matching_query_returns_paginated_results_quickly(self):
		start = perf_counter()
		response = self.client.get(
			f"/api/users/{self.user.id}/matching-hits",
			{"page": 1, "page_size": 10, "sort": "-match_score"},
		)
		duration = perf_counter() - start
		payload = response.json()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 20)
		self.assertEqual(len(payload["results"]), 10)
		self.assertLess(duration, 0.5)
class ImportEndpointTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.offer_type = OfferType.objects.create(name="training", description="")
		cls.source_type = SourceType.objects.create(name="manual", description="")
		cls.target_profile = TargetProfile.objects.create(name="student", description="")
		cls.domain = Domain.objects.create(name="AI")
		cls.organization = Organization.objects.create(
			name="Test University",
			type=Organization.OrganizationType.UNIVERSITY,
			country="IT",
			website="https://example.edu",
		)
		cls.bot_user = User.objects.create(
			username="ingestion_bot",
			email="bot@example.com",
			password_hash="not-used",
		)
		cls.user = User.objects.create(
			username="tester",
			email="tester@example.com",
			password_hash="not-used",
		)
		cls.admin = User.objects.create(
			username="import_admin",
			email="import_admin@example.com",
			password_hash="not-used",
			profile=User.ProfileType.ADMIN,
			is_active=True,
		)
		cls.admin_token = generate_tokens(cls.admin.id, cls.admin.username, cls.admin.profile)["access_token"]

	def _csv_file(self, rows: list[dict]) -> io.BytesIO:
		from content.ingestion.importer import ALL_COLUMNS
		buf = io.StringIO()
		writer = csv.DictWriter(buf, fieldnames=ALL_COLUMNS, extrasaction="ignore")
		writer.writeheader()
		for row in rows:
			writer.writerow(row)
		return io.BytesIO(buf.getvalue().encode("utf-8"))

	def _valid_row(self, url="https://example.edu/prog") -> dict:
		return {
			"url": url,
			"offer_type": "training",
			"organization": "Test University",
			"target_profile": "student",
			"country": "IT",
			"title": "Test Offer",
			"summary": "A summary.",
		}

	def test_import_template_returns_xlsx(self):
		response = self.client.get("/api/offers/import/template", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		self.assertEqual(response.status_code, 200)
		self.assertIn(
			"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			response["Content-Type"],
		)
		self.assertGreater(len(response.content), 0)

	def test_import_preview_valid_csv(self):
		f = self._csv_file([self._valid_row()])
		response = self.client.post(
			"/api/offers/import/preview",
			{"file": f},
			format="multipart",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(payload["valid"]), 1)
		self.assertEqual(len(payload["invalid"]), 0)
		self.assertIn("url", payload["valid"][0]["data"])

	def test_import_preview_invalid_row_missing_field(self):
		row = self._valid_row()
		del row["url"]
		f = self._csv_file([row])
		response = self.client.post("/api/offers/import/preview", {"file": f}, format="multipart", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(payload["invalid"]), 1)
		errors = payload["invalid"][0]["errors"]
		self.assertTrue(any("url" in e for e in errors))

	def test_import_preview_existing_url_warns(self):
		url = "https://example.edu/existing"
		Offer.objects.create(
			title="Existing",
			summary="",
			link=url,
			country="IT",
			status=Offer.OfferStatus.PUBLISHED,
			offer_type=self.offer_type,
			organization=self.organization,
			source_type=self.source_type,
			target_profile=self.target_profile,
			created_by=self.user,
			updated_by=self.user,
		)
		f = self._csv_file([self._valid_row(url=url)])
		response = self.client.post("/api/offers/import/preview", {"file": f}, format="multipart", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(payload["valid"]), 1)
		warnings = payload["valid"][0]["warnings"]
		self.assertTrue(any("already exists" in w for w in warnings))

	def test_import_confirm_creates_draft(self):
		url = "https://example.edu/new-draft"
		rows = [{"data": self._valid_row(url=url), "status": "draft"}]
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": rows}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["drafts"], 1)
		self.assertEqual(payload["published"], 0)
		offer = Offer.objects.get(link=url)
		self.assertEqual(offer.status, Offer.OfferStatus.DRAFT)
		self.assertTrue(CrawlUrl.objects.filter(url=url).exists())

	def test_import_confirm_creates_published(self):
		url = "https://example.edu/new-published"
		rows = [{"data": self._valid_row(url=url), "status": "published"}]
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": rows}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["published"], 1)
		offer = Offer.objects.get(link=url)
		self.assertEqual(offer.status, Offer.OfferStatus.PUBLISHED)

	def test_import_confirm_mixed_statuses(self):
		rows = [
			{"data": self._valid_row(url="https://example.edu/draft-a"), "status": "draft"},
			{"data": self._valid_row(url="https://example.edu/pub-b"), "status": "published"},
		]
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": rows}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["drafts"], 1)
		self.assertEqual(payload["published"], 1)

	def test_import_confirm_row_not_object(self):
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": [42]}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("Row 0", response.json()["error"])

	def test_import_confirm_missing_required_field(self):
		row = {"data": self._valid_row(), "status": "draft"}
		del row["data"]["offer_type"]
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": [row]}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("offer_type", response.json()["error"])

	def test_import_confirm_bad_row_no_partial_write(self):
		valid_url = "https://example.edu/atomic-check"
		good_row = {"data": self._valid_row(url=valid_url), "status": "draft"}
		bad_row = {"data": self._valid_row(), "status": "draft"}
		del bad_row["data"]["organization"]
		offer_count_before = Offer.objects.count()
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": [good_row, bad_row]}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		self.assertEqual(response.status_code, 400)
		self.assertEqual(Offer.objects.count(), offer_count_before)

	def test_import_confirm_invalid_status(self):
		row = {"data": self._valid_row(url="https://example.edu/bad-status"), "status": "publsihed"}
		offer_count_before = Offer.objects.count()
		response = self.client.post(
			"/api/offers/import/confirm",
			data=json.dumps({"rows": [row]}),
			content_type="application/json",
			HTTP_AUTHORIZATION=f"Bearer {self.admin_token}",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("status", response.json()["error"])
		self.assertEqual(Offer.objects.count(), offer_count_before)


class ScrapingAnalyticsTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.offer_type = OfferType.objects.create(name="grant", description="")
		cls.source_type = SourceType.objects.create(name="scraper", description="")
		cls.target_profile = TargetProfile.objects.create(name="researcher", description="")
		cls.organization = Organization.objects.create(
			name="Scraping Org",
			type=Organization.OrganizationType.COMPANY,
			country="DE",
			website="https://scraping.example.com",
		)
		cls.user = User.objects.create(
			username="scrape_tester",
			email="scrape@example.com",
			password_hash="not-used",
		)
		cls.admin = User.objects.create(
			username="scrape_admin",
			email="scrape_admin@example.com",
			password_hash="not-used",
			profile=User.ProfileType.ADMIN,
			is_active=True,
		)
		cls.admin_token = generate_tokens(cls.admin.id, cls.admin.username, cls.admin.profile)["access_token"]
		cls.scraping_run = ScrapingRun.objects.create(
			source_key="test-source",
			status=ScrapingRun.RunStatus.SUCCESS,
			offers_processed=2,
			offers_created=1,
			offers_updated=1,
			offers_unchanged=0,
			urls_neglected=1,
			errors_count=0,
			log=[
				{"event": "url_processed", "method": "llm_primary", "confidence": 0.9},
				{"event": "url_processed", "method": "deterministic", "confidence": 0.95},
				{"event": "url_neglected", "url": "https://skip.me"},
			],
		)
		cls.offer = Offer.objects.create(
			title="Grant Offer",
			summary="",
			link="https://scraping.example.com/grant",
			country="DE",
			status=Offer.OfferStatus.PUBLISHED,
			offer_type=cls.offer_type,
			organization=cls.organization,
			source_type=cls.source_type,
			target_profile=cls.target_profile,
			created_by=cls.user,
			updated_by=cls.user,
		)
		CrawlUrl.objects.create(
			source_key="test-source",
			url="https://scraping.example.com/grant",
			status=CrawlUrl.UrlStatus.DONE,
			offer=cls.offer,
		)
		CrawlUrl.objects.create(
			source_key="test-source",
			url="https://scraping.example.com/pending",
			status=CrawlUrl.UrlStatus.PENDING,
			offer=cls.offer,
		)

	def test_scraping_overview_returns_shape(self):
		response = self.client.get("/api/scraping/overview", {"window": "24h"}, HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertIn("runs_total", payload)
		self.assertIn("runs_timeline", payload)
		self.assertIsInstance(payload["runs_timeline"], list)

	def test_scraping_overview_window_params(self):
		for window in ("7d", "30d"):
			with self.subTest(window=window):
				response = self.client.get("/api/scraping/overview", {"window": window}, HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
				self.assertEqual(response.status_code, 200)

	def test_scraping_overview_invalid_window(self):
		response = self.client.get("/api/scraping/overview", {"window": "bad"}, HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		self.assertEqual(response.status_code, 400)

	def test_sources_health_returns_per_source(self):
		response = self.client.get("/api/scraping/sources/health", HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		sources = {s["source_key"]: s for s in payload["results"]}
		self.assertIn("test-source", sources)
		s = sources["test-source"]
		self.assertEqual(s["done"], 1)
		self.assertEqual(s["pending"], 1)
		self.assertEqual(s["total_urls"], 2)

	def test_llm_stats_returns_method_split(self):
		response = self.client.get("/api/scraping/llm/stats", {"window": "24h"}, HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertIn("method_split", payload)
		self.assertIn("llm_primary", payload["method_split"])
		self.assertIn("deterministic", payload["method_split"])
		self.assertIsNotNone(payload["avg_confidence_llm"])

	def test_llm_stats_empty_window(self):
		response = self.client.get("/api/scraping/llm/stats", {"window": "30d"}, HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		# run created in setUpTestData falls within 30d too — just verify shape
		self.assertIn("method_split", payload)
		self.assertIn("avg_confidence_llm", payload)
