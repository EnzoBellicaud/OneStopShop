"""
Unit tests for the matching service.
Tests the hybrid matching logic: fast filters and scoring.
Also includes integration tests for the full matching service and the matching refresh triggers.
"""

from decimal import Decimal
from django.test import TestCase

from content.models import (
    Domain,
    MatchingHit,
    Offer,
    OfferDomain,
    OfferType,
    Organization,
    SourceType,
    TargetProfile,
    User,
    UserNeed,
    UserNeedDomain,
)
from content.matching_service import (
    _keyword_overlap,
    _keyword_score,
    _passes_fast_filter,
    _tokenize,
    run_matching_for_offers,
)
from content.matching_triggers import refresh_matches_for_need, refresh_matches_for_offers


class TokenizationTests(TestCase):
    """Test keyword tokenization."""

    def test_tokenize_basic(self):
        """Extract keywords from text."""
        result = _tokenize("Python programming course")
        self.assertIn("python", result)
        self.assertIn("programming", result)
        self.assertIn("course", result)

    def test_tokenize_removes_stopwords(self):
        """Stopwords are filtered out."""
        result = _tokenize("the quick brown fox and the lazy dog")
        self.assertNotIn("the", result)
        self.assertNotIn("and", result)
        self.assertIn("quick", result)
        self.assertIn("brown", result)

    def test_tokenize_short_words(self):
        """Words shorter than 3 characters are excluded."""
        result = _tokenize("a AI in machine learning")
        self.assertNotIn("a", result)
        self.assertNotIn("in", result)
        self.assertIn("machine", result)

    def test_tokenize_empty_string(self):
        """Empty string returns empty set."""
        result = _tokenize("")
        self.assertEqual(result, set())

    def test_tokenize_case_insensitive(self):
        """Tokenization is case-insensitive."""
        result1 = _tokenize("Python")
        result2 = _tokenize("python")
        self.assertEqual(result1, result2)


class KeywordOverlapTests(TestCase):
    """Test keyword overlap calculation."""

    @classmethod
    def setUpTestData(cls):
        cls.target_profile = TargetProfile.objects.create(name="student")
        cls.source_type = SourceType.objects.create(name="manual")
        cls.offer_type = OfferType.objects.create(name="course")
        cls.organization = Organization.objects.create(
            name="Test University",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://test.edu",
        )
        cls.user = User.objects.create(
            username="test_user",
            email="test@example.com",
            password_hash="hash",
        )

    def test_keyword_overlap_matching(self):
        """Keywords in common are counted."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Python Machine Learning",
            description="Looking for AI and data science",
            target_profile=self.target_profile,
        )
        offer = Offer.objects.create(
            title="Advanced Machine Learning with Python",
            summary="Data science and AI techniques",
            link="https://test.edu/course",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.target_profile,
            created_by=self.user,
            updated_by=self.user,
        )
        overlap = _keyword_overlap(need, offer)
        # Should find: machine, learning, python, data, science
        self.assertGreaterEqual(overlap, 3)

    def test_keyword_overlap_no_match(self):
        """No keywords in common results in 0 overlap."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Art History",
            description="Renaissance painting",
            target_profile=self.target_profile,
        )
        offer = Offer.objects.create(
            title="Computer Science 101",
            summary="Programming and algorithms",
            link="https://test.edu/cs",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.target_profile,
            created_by=self.user,
            updated_by=self.user,
        )
        overlap = _keyword_overlap(need, offer)
        self.assertEqual(overlap, 0)


class FastFilterTests(TestCase):
    """Test the fast filter logic."""

    @classmethod
    def setUpTestData(cls):
        cls.domain_ai = Domain.objects.create(name="AI")
        cls.domain_web = Domain.objects.create(name="Web Development")
        cls.profile_student = TargetProfile.objects.create(name="student")
        cls.profile_researcher = TargetProfile.objects.create(name="researcher")
        cls.source_type = SourceType.objects.create(name="manual")
        cls.offer_type = OfferType.objects.create(name="course")
        cls.organization = Organization.objects.create(
            name="Test Org",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://test.edu",
        )
        cls.user = User.objects.create(
            username="test",
            email="test@example.com",
            password_hash="hash",
        )

    def test_passes_fast_filter_target_profile_mismatch(self):
        """Mismatched target profiles fail filter."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Student Research",
            description="Research opportunity",
            target_profile=self.profile_student,
        )
        offer = Offer.objects.create(
            title="Researcher Internship",
            summary="For researchers",
            link="https://test.edu/research",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.profile_researcher,
            created_by=self.user,
            updated_by=self.user,
        )
        result = _passes_fast_filter(need, offer, set(), set())
        self.assertFalse(result)

    def test_passes_fast_filter_country_mismatch(self):
        """Mismatched countries fail filter."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Study in Italy",
            description="Looking for Italian program",
            target_profile=self.profile_student,
            countries=["IT"],
        )
        offer = Offer.objects.create(
            title="Course in Sweden",
            summary="Swedish program",
            link="https://test.se/course",
            country="SE",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.profile_student,
            created_by=self.user,
            updated_by=self.user,
        )
        result = _passes_fast_filter(
            need, offer, set(), set()
        )
        self.assertFalse(result)

    def test_passes_fast_filter_domain_mismatch(self):
        """Missing domain fails filter."""
        need = UserNeed.objects.create(
            user=self.user,
            title="AI Training",
            description="AI focused",
            target_profile=self.profile_student,
        )
        UserNeedDomain.objects.create(user_need=need, domain=self.domain_ai)
        
        offer = Offer.objects.create(
            title="Web Development Course",
            summary="Web development",
            link="https://test.edu/web",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.profile_student,
            created_by=self.user,
            updated_by=self.user,
        )
        OfferDomain.objects.create(offer=offer, domain=self.domain_web)
        
        result = _passes_fast_filter(
            need, offer, {self.domain_ai.id}, {self.domain_web.id}
        )
        self.assertFalse(result)

    def test_passes_fast_filter_success(self):
        """Matching criteria pass filter."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Machine Learning opportunity",
            description="Seeking ML program",
            target_profile=self.profile_student,
            countries=["IT"],
        )
        UserNeedDomain.objects.create(user_need=need, domain=self.domain_ai)
        
        offer = Offer.objects.create(
            title="AI and Machine Learning Master",
            summary="Advanced AI techniques",
            link="https://test.edu/ai",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.profile_student,
            created_by=self.user,
            updated_by=self.user,
        )
        OfferDomain.objects.create(offer=offer, domain=self.domain_ai)
        
        result = _passes_fast_filter(
            need, offer, {self.domain_ai.id}, {self.domain_ai.id}
        )
        self.assertTrue(result)


class KeywordScoringTests(TestCase):
    """Test keyword-based scoring."""

    @classmethod
    def setUpTestData(cls):
        cls.target_profile = TargetProfile.objects.create(name="student")
        cls.source_type = SourceType.objects.create(name="manual")
        cls.offer_type = OfferType.objects.create(name="course")
        cls.organization = Organization.objects.create(
            name="Test Org",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://test.edu",
        )
        cls.user = User.objects.create(
            username="test",
            email="test@example.com",
            password_hash="hash",
        )

    def test_keyword_score_high_overlap(self):
        """High keyword overlap produces higher score."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Python Data Science Machine Learning",
            description="Want to learn data science and machine learning with Python",
            target_profile=self.target_profile,
        )
        offer = Offer.objects.create(
            title="Python Machine Learning and Data Science",
            summary="Master data science and machine learning using Python",
            link="https://test.edu/course",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.target_profile,
            created_by=self.user,
            updated_by=self.user,
        )
        score, reason = _keyword_score(need, offer)
        # High overlap should produce higher score
        self.assertGreater(score, Decimal("0.5"))
        self.assertLessEqual(score, Decimal("0.9"))

    def test_keyword_score_low_overlap(self):
        """Low keyword overlap produces lower score."""
        need = UserNeed.objects.create(
            user=self.user,
            title="Art",
            description="Art history study",
            target_profile=self.target_profile,
        )
        offer = Offer.objects.create(
            title="Computer Science",
            summary="Programming basics",
            link="https://test.edu/cs",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.target_profile,
            created_by=self.user,
            updated_by=self.user,
        )
        score, reason = _keyword_score(need, offer)
        # Minimal overlap should produce minimal score
        self.assertEqual(score, Decimal("0.4"))


class MatchingServiceIntegrationTests(TestCase):
    """Integration tests for the full matching service."""

    @classmethod
    def setUpTestData(cls):
        cls.domain = Domain.objects.create(name="Data Science")
        cls.target_profile = TargetProfile.objects.create(name="student")
        cls.source_type = SourceType.objects.create(name="manual")
        cls.offer_type = OfferType.objects.create(name="course")
        cls.organization = Organization.objects.create(
            name="Tech University",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://tech.edu",
        )

        # Create users
        cls.user1 = User.objects.create(
            username="user1",
            email="user1@example.com",
            password_hash="hash",
        )
        cls.user2 = User.objects.create(
            username="user2",
            email="user2@example.com",
            password_hash="hash",
        )

        # Create needs
        cls.need1 = UserNeed.objects.create(
            user=cls.user1,
            title="Data Science training",
            description="Looking for data science course",
            target_profile=cls.target_profile,
            status=UserNeed.NeedStatus.ACTIVE,
        )
        UserNeedDomain.objects.create(user_need=cls.need1, domain=cls.domain)

        cls.need2 = UserNeed.objects.create(
            user=cls.user2,
            title="Web Development",
            description="Web development course",
            target_profile=cls.target_profile,
            status=UserNeed.NeedStatus.ACTIVE,
        )

        # Create published offer
        cls.offer1 = Offer.objects.create(
            title="Data Science and Machine Learning",
            summary="Comprehensive data science training",
            link="https://tech.edu/ds",
            country="IT",
            offer_type=cls.offer_type,
            organization=cls.organization,
            source_type=cls.source_type,
            target_profile=cls.target_profile,
            status=Offer.OfferStatus.PUBLISHED,
            created_by=cls.user1,
            updated_by=cls.user1,
        )
        OfferDomain.objects.create(offer=cls.offer1, domain=cls.domain)

        # Create draft offer (should not be matched)
        cls.offer2 = Offer.objects.create(
            title="AI Bootcamp",
            summary="Artificial Intelligence intensive",
            link="https://tech.edu/ai",
            country="IT",
            offer_type=cls.offer_type,
            organization=cls.organization,
            source_type=cls.source_type,
            target_profile=cls.target_profile,
            status=Offer.OfferStatus.DRAFT,
            created_by=cls.user1,
            updated_by=cls.user1,
        )

    def test_run_matching_creates_hits(self):
        """Running matching creates appropriate MatchingHit records."""
        self.assertEqual(MatchingHit.objects.count(), 0)
        
        stats = run_matching_for_offers([self.offer1.id])
        
        self.assertEqual(stats["offers"], 1)
        self.assertGreaterEqual(stats["candidates"], 1)
        self.assertGreater(stats["created"], 0)
        self.assertGreater(MatchingHit.objects.count(), 0)

    def test_run_matching_skips_draft_offers(self):
        """Draft offers are not matched."""
        stats = run_matching_for_offers([self.offer2.id])
        
        self.assertEqual(stats["offers"], 0)
        self.assertEqual(stats["candidates"], 0)
        self.assertEqual(stats["created"], 0)

    def test_run_matching_skips_inactive_needs(self):
        """Inactive needs are not matched."""
        # Archive the need
        self.need1.status = UserNeed.NeedStatus.FULFILLED
        self.need1.save()
        
        stats = run_matching_for_offers([self.offer1.id])
        
        self.assertEqual(stats["candidates"], 0)
        self.assertEqual(stats["created"], 0)

    def test_run_matching_skips_duplicates(self):
        """Duplicate matches are skipped on second run."""
        # First run
        stats1 = run_matching_for_offers([self.offer1.id])
        created_count_1 = stats1["created"]
        self.assertGreater(created_count_1, 0)
        
        # Second run should skip duplicates
        stats2 = run_matching_for_offers([self.offer1.id])
        self.assertEqual(stats2["skipped"], created_count_1)
        self.assertEqual(stats2["created"], 0)

    def test_run_matching_empty_list(self):
        """Empty offer list returns empty stats."""
        stats = run_matching_for_offers([])
        
        self.assertEqual(stats["offers"], 0)
        self.assertEqual(stats["candidates"], 0)
        self.assertEqual(stats["created"], 0)

    def test_matching_hit_structure(self):
        """Created MatchingHit has correct structure."""
        run_matching_for_offers([self.offer1.id])
        
        hit = MatchingHit.objects.first()
        self.assertIsNotNone(hit)
        self.assertEqual(hit.offer_id, self.offer1.id)
        self.assertIn(hit.need_id, [self.need1.id, self.need2.id])
        self.assertGreaterEqual(hit.match_score, Decimal("0"))
        self.assertLessEqual(hit.match_score, Decimal("1"))
        self.assertNotEqual(hit.match_reason, "")


class MatchingTriggerTests(TestCase):
    """Tests for write-path matching refresh helpers."""

    @classmethod
    def setUpTestData(cls):
        cls.domain = Domain.objects.create(name="Trigger AI")
        cls.target_profile = TargetProfile.objects.create(name="trigger-student")
        cls.source_type = SourceType.objects.create(name="trigger-manual")
        cls.offer_type = OfferType.objects.create(name="trigger-course")
        cls.organization = Organization.objects.create(
            name="Trigger University",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://trigger.edu",
        )
        cls.user = User.objects.create(
            username="trigger-user",
            email="trigger@example.com",
            password_hash="hash",
        )

    def _create_need(self, title="Trigger AI Need"):
        need = UserNeed.objects.create(
            user=self.user,
            title=title,
            description="Looking for trigger AI machine learning courses",
            target_profile=self.target_profile,
            status=UserNeed.NeedStatus.ACTIVE,
            countries=["IT"],
        )
        UserNeedDomain.objects.create(user_need=need, domain=self.domain)
        return need

    def _create_offer(self, status=Offer.OfferStatus.PUBLISHED):
        offer = Offer.objects.create(
            title="Trigger AI Machine Learning Course",
            summary="A trigger AI machine learning course in Italy",
            link=f"https://trigger.edu/{status}",
            country="IT",
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=self.target_profile,
            status=status,
            created_by=self.user,
            updated_by=self.user,
        )
        OfferDomain.objects.create(offer=offer, domain=self.domain)
        return offer

    def test_refresh_matches_for_need_rebuilds_need_hits(self):
        need = self._create_need()
        offer = self._create_offer()
        MatchingHit.objects.create(
            user=self.user,
            need=need,
            offer=offer,
            match_score=Decimal("0.1000"),
            match_reason="stale",
        )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_matches_for_need(need.id)

        hit = MatchingHit.objects.get(need=need, offer=offer)
        self.assertGreater(hit.match_score, Decimal("0.1000"))
        self.assertNotEqual(hit.match_reason, "stale")

    def test_refresh_matches_for_need_does_not_match_other_needs(self):
        need = self._create_need()
        other_need = self._create_need(title="Other Trigger AI Need")
        offer = self._create_offer()
        MatchingHit.objects.create(
            user=self.user,
            need=need,
            offer=offer,
            match_score=Decimal("0.1000"),
            match_reason="stale",
        )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_matches_for_need(need.id)

        self.assertTrue(MatchingHit.objects.filter(need=need, offer=offer).exists())
        self.assertFalse(
            MatchingHit.objects.filter(need=other_need, offer=offer).exists()
        )

    def test_refresh_matches_for_need_only_rebuilds_published_offer_hits(self):
        need = self._create_need()
        published_offer = self._create_offer(status=Offer.OfferStatus.PUBLISHED)
        draft_offer = self._create_offer(status=Offer.OfferStatus.DRAFT)
        archived_offer = self._create_offer(status=Offer.OfferStatus.ARCHIVED)

        for offer in [published_offer, draft_offer, archived_offer]:
            MatchingHit.objects.create(
                user=self.user,
                need=need,
                offer=offer,
                match_score=Decimal("0.1000"),
                match_reason="stale",
            )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_matches_for_need(need.id)

        self.assertTrue(
            MatchingHit.objects.filter(need=need, offer=published_offer).exists()
        )
        self.assertFalse(MatchingHit.objects.filter(need=need, offer=draft_offer).exists())
        self.assertFalse(
            MatchingHit.objects.filter(need=need, offer=archived_offer).exists()
        )

    def test_refresh_matches_for_draft_offer_removes_stale_hits(self):
        need = self._create_need()
        offer = self._create_offer(status=Offer.OfferStatus.DRAFT)
        MatchingHit.objects.create(
            user=self.user,
            need=need,
            offer=offer,
            match_score=Decimal("0.9000"),
            match_reason="stale",
        )

        with self.captureOnCommitCallbacks(execute=True):
            refresh_matches_for_offers([offer.id])

        self.assertFalse(MatchingHit.objects.filter(need=need, offer=offer).exists())


class MatchingAccuracyEdgeCaseTests(TestCase):
    """Focused accuracy and edge-case tests for the matching service."""

    @classmethod
    def setUpTestData(cls):
        cls.domain_data = Domain.objects.create(name="Accuracy Data Science")
        cls.domain_robotics = Domain.objects.create(name="Accuracy Robotics")
        cls.profile_student = TargetProfile.objects.create(name="accuracy-student")
        cls.profile_researcher = TargetProfile.objects.create(name="accuracy-researcher")
        cls.source_type = SourceType.objects.create(name="accuracy-manual")
        cls.offer_type = OfferType.objects.create(name="accuracy-course")
        cls.organization = Organization.objects.create(
            name="Accuracy University",
            type=Organization.OrganizationType.UNIVERSITY,
            country="IT",
            website="https://accuracy.example.edu",
        )
        cls.user = User.objects.create(
            username="accuracy_user",
            email="accuracy@example.com",
            password_hash="hash",
        )

    def _need(
        self,
        title,
        description,
        *,
        target_profile=None,
        countries=None,
        domains=None,
        status=UserNeed.NeedStatus.ACTIVE,
    ):
        need = UserNeed.objects.create(
            user=self.user,
            title=title,
            description=description,
            target_profile=target_profile,
            countries=countries or [],
            status=status,
        )
        if domains:
            need.domains.set(domains)
        return need

    def _offer(
        self,
        title,
        summary,
        *,
        target_profile=None,
        country="IT",
        domains=None,
        status=Offer.OfferStatus.PUBLISHED,
        link_suffix="offer",
    ):
        offer = Offer.objects.create(
            title=title,
            summary=summary,
            link=f"https://accuracy.example.edu/{link_suffix}",
            country=country,
            offer_type=self.offer_type,
            organization=self.organization,
            source_type=self.source_type,
            target_profile=target_profile or self.profile_student,
            status=status,
            created_by=self.user,
            updated_by=self.user,
        )
        if domains:
            offer.domains.set(domains)
        return offer

    def test_matching_accuracy_creates_hit_only_for_relevant_need(self):
        """A precise offer should match the relevant need and ignore unrelated active needs."""
        matching_need = self._need(
            "Data science internship",
            "Looking for Python analytics and machine learning practice",
            target_profile=self.profile_student,
            countries=["IT"],
            domains=[self.domain_data],
        )
        unrelated_need = self._need(
            "Robotics hardware lab",
            "Need embedded systems and sensor prototyping",
            target_profile=self.profile_student,
            countries=["IT"],
            domains=[self.domain_robotics],
        )
        profile_mismatch_need = self._need(
            "Data science researcher placement",
            "Python analytics and machine learning",
            target_profile=self.profile_researcher,
            countries=["IT"],
            domains=[self.domain_data],
        )
        offer = self._offer(
            "Python Data Science Internship",
            "Hands-on analytics and machine learning with Python",
            target_profile=self.profile_student,
            domains=[self.domain_data],
            link_suffix="data-science-internship",
        )

        stats = run_matching_for_offers([offer.id])
        hits = list(MatchingHit.objects.filter(offer=offer))

        self.assertEqual(stats["created"], 1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].need_id, matching_need.id)
        self.assertNotEqual(hits[0].need_id, unrelated_need.id)
        self.assertNotEqual(hits[0].need_id, profile_mismatch_need.id)

    def test_fast_filter_treats_missing_need_target_profile_as_wildcard(self):
        """A need without target_profile should still match when other filters pass."""
        need = self._need(
            "Machine learning course",
            "Python analytics practice",
            target_profile=None,
            countries=["IT"],
            domains=[self.domain_data],
        )
        offer = self._offer(
            "Machine Learning Course",
            "Python analytics for students",
            target_profile=self.profile_student,
            domains=[self.domain_data],
            link_suffix="wildcard-profile",
        )

        result = _passes_fast_filter(
            need,
            offer,
            {self.domain_data.id},
            {self.domain_data.id},
        )

        self.assertTrue(result)

    def test_fast_filter_treats_empty_country_and_domain_filters_as_permissive(self):
        """Needs with no country/domain preferences should not reject a keyword match."""
        need = self._need(
            "Analytics scholarship",
            "Seeking data science funding",
            target_profile=self.profile_student,
        )
        offer = self._offer(
            "Data Science Scholarship",
            "Analytics funding for students",
            country="SE",
            target_profile=self.profile_student,
            domains=[],
            link_suffix="permissive-filters",
        )

        result = _passes_fast_filter(need, offer, set(), set())

        self.assertTrue(result)

    def test_matching_rejects_stopword_only_overlap(self):
        """Text with only stopwords should not create a match."""
        need = self._need(
            "The and for",
            "With the and to",
            target_profile=self.profile_student,
        )
        offer = self._offer(
            "The and for",
            "With the and to",
            target_profile=self.profile_student,
            link_suffix="stopwords",
        )

        stats = run_matching_for_offers([offer.id])

        self.assertEqual(stats["candidates"], 0)
        self.assertEqual(stats["created"], 0)
        self.assertFalse(MatchingHit.objects.filter(need=need, offer=offer).exists())

    def test_keyword_score_caps_at_point_nine_for_many_shared_terms(self):
        """Large overlap should increase confidence but never exceed the scoring cap."""
        need = self._need(
            "Python data science machine learning analytics internship",
            "Neural networks statistics visualization research project",
            target_profile=self.profile_student,
        )
        offer = self._offer(
            "Python data science machine learning analytics internship",
            "Neural networks statistics visualization research project",
            target_profile=self.profile_student,
            link_suffix="score-cap",
        )

        score, reason = _keyword_score(need, offer)

        self.assertEqual(score, Decimal("0.9"))
        self.assertIn("shared terms", reason)
