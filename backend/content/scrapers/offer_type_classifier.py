import logging
import os

LOGGER = logging.getLogger(__name__)
_THRESHOLD = float(os.environ.get("SCRAPER_CLASSIFIER_THRESHOLD", "0.30"))
_GATE_THRESHOLD = float(os.environ.get("SCRAPER_GATE_THRESHOLD", "0.05"))


class OfferTypeClassifier:
    """
    TF-IDF cosine-similarity classifier against all OfferType descriptions.
    Used as a deterministic fallback when LLM is disabled or returns no offer_type.
    """

    def classify(self, text: str) -> tuple[str | None, float]:
        """
        Returns (offer_type_name, confidence).
        Returns (None, 0.0) if below threshold or catalog is empty.
        """
        if not text or not text.strip():
            return None, 0.0

        from content.scrapers.offer_type_catalog import get_offer_type_catalog
        catalog = get_offer_type_catalog()
        if not catalog:
            return None, 0.0

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            LOGGER.warning("scikit-learn not installed — offer_type_classifier unavailable")
            return None, 0.0

        docs = [
            f"{t['name']} {t['description'] or ''} {(t.get('keywords') or '').replace(',', ' ')}"
            for t in catalog
        ]
        names = [t["name"] for t in catalog]

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
            query_vec = vectorizer.transform([text])
        except ValueError:
            return None, 0.0

        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])

        if best_score < _THRESHOLD:
            LOGGER.debug(
                "Classifier best match '%s' score %.3f below threshold %.2f — discarding",
                names[best_idx], best_score, _THRESHOLD,
            )
            return None, best_score

        LOGGER.debug("Classifier → '%s' (score=%.3f)", names[best_idx], best_score)
        return names[best_idx], best_score

    def classify_with_terms(self, text: str, top_n: int = 5) -> tuple[str | None, float, list[str]]:
        """Like classify() but also returns the top TF-IDF terms from the input for logging."""
        if not text or not text.strip():
            return None, 0.0, []

        from content.scrapers.offer_type_catalog import get_offer_type_catalog
        catalog = get_offer_type_catalog()
        if not catalog:
            return None, 0.0, []

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
        except ImportError:
            return None, 0.0, []

        docs = [
            f"{t['name']} {t['description'] or ''} {(t.get('keywords') or '').replace(',', ' ')}"
            for t in catalog
        ]
        names = [t["name"] for t in catalog]

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(docs)
            query_vec = vectorizer.transform([text])
        except ValueError:
            return None, 0.0, []

        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])

        feature_names = vectorizer.get_feature_names_out()
        query_weights = query_vec.toarray().flatten()
        top_indices = np.argsort(query_weights)[-top_n:][::-1]
        top_terms = [feature_names[i] for i in top_indices if query_weights[i] > 0]

        if best_score < _THRESHOLD:
            return None, best_score, top_terms

        return names[best_idx], best_score, top_terms
