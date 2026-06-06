"""Unit tests for the TF-IDF offer type classifier."""
from unittest.mock import patch
from django.test import TestCase

from content.scrapers.offer_type_classifier import OfferTypeClassifier

_CATALOG = [
    {"name": "thesis", "description": "Academic thesis or dissertation project at a university"},
    {"name": "internship", "description": "Internship or work placement for students"},
    {"name": "job", "description": "Full-time or part-time employment position"},
    {"name": "scholarship", "description": "Scholarship, grant, or funding opportunity"},
    {"name": "course", "description": "Training course, workshop, or online learning program"},
]

_CATALOG_MODULE = "content.scrapers.offer_type_catalog.get_offer_type_catalog"


class OfferTypeClassifierTest(TestCase):

    @patch(_CATALOG_MODULE)
    def test_classifies_thesis_text(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("PhD thesis research project university academic dissertation supervisor")
        self.assertEqual(key, "thesis")
        self.assertGreater(score, 0.30)

    @patch(_CATALOG_MODULE)
    def test_classifies_internship_text(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("internship placement students company work experience")
        self.assertEqual(key, "internship")
        self.assertGreater(score, 0.30)

    @patch(_CATALOG_MODULE)
    def test_classifies_scholarship_text(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("scholarship grant funding opportunity students financial aid")
        self.assertEqual(key, "scholarship")
        self.assertGreater(score, 0.30)

    @patch(_CATALOG_MODULE)
    def test_returns_none_below_threshold(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("xyz abc 123 qwerty asdfgh jkl zxcvbn")
        self.assertIsNone(key)

    @patch(_CATALOG_MODULE)
    def test_returns_none_for_empty_text(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("")
        self.assertIsNone(key)
        self.assertEqual(score, 0.0)

    @patch(_CATALOG_MODULE)
    def test_returns_none_for_whitespace_text(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("   ")
        self.assertIsNone(key)
        self.assertEqual(score, 0.0)

    @patch(_CATALOG_MODULE)
    def test_returns_none_when_catalog_empty(self, mock_catalog):
        mock_catalog.return_value = []
        clf = OfferTypeClassifier()
        key, score = clf.classify("thesis research academic")
        self.assertIsNone(key)
        self.assertEqual(score, 0.0)

    @patch(_CATALOG_MODULE)
    def test_score_is_between_zero_and_one(self, mock_catalog):
        mock_catalog.return_value = _CATALOG
        clf = OfferTypeClassifier()
        key, score = clf.classify("thesis university research academic")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
