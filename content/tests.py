import uuid

from django.test import TestCase

from content.models import (
	Domain,
	Offer,
	OfferDomain,
	OfferType,
	Organization,
	ScrapingRun,
	SourceType,
	TargetProfile,
	User,
)


class ReadApiTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.offer_type = OfferType.objects.create(name="training", description="")
		cls.domain = Domain.objects.create(name="AI")
		cls.target_profile = TargetProfile.objects.create(name="student", description="")
		cls.source_type = SourceType.objects.create(name="manual", description="")
		cls.organization = Organization.objects.create(
			name="Test University",
			type=Organization.OrganizationType.UNIVERSITY,
			country="IT",
			website="https://example.edu",
		)
		cls.user = User.objects.create(
			username="tester",
			email="tester@example.com",
			password_hash="not-used",
		)
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

	def test_health_endpoint(self):
		response = self.client.get("/api/health")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["status"], "ok")

	def test_docs_endpoint(self):
		response = self.client.get("/api/docs")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "SwaggerUIBundle")

	def test_openapi_schema_endpoint(self):
		response = self.client.get("/api/openapi.json")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["openapi"], "3.0.3")
		self.assertIn("/api/offers", payload["paths"])

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

	def test_offers_list_endpoint(self):
		response = self.client.get("/api/offers")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)
		self.assertEqual(payload["results"][0]["title"], "AI Master Programme")

	def test_offers_filter_by_status(self):
		response = self.client.get("/api/offers", {"status": Offer.OfferStatus.PUBLISHED})
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 1)

	def test_scraping_runs_endpoint(self):
		response = self.client.get("/api/scraping/runs")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["count"], 0)

	def test_scraping_run_detail_endpoint(self):
		run = ScrapingRun.objects.create(source_key="test-source", status=ScrapingRun.RunStatus.SUCCESS)
		response = self.client.get(f"/api/scraping/runs/{run.id}")
		payload = response.json()
		self.assertEqual(response.status_code, 200)
		self.assertEqual(payload["id"], str(run.id))

	def test_scraping_run_detail_not_found(self):
		response = self.client.get(f"/api/scraping/runs/{uuid.uuid4()}")
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
