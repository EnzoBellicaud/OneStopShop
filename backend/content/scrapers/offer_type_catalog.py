import logging
from django.core.cache import cache

LOGGER = logging.getLogger(__name__)
_CACHE_KEY = "offer_type_catalog"
_CACHE_TTL = 300  # 5 minutes


def get_offer_type_catalog() -> list[dict]:
    """Returns [{key, name, description}] for all OfferType rows, cached for 5 min."""
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached
    from content.models import OfferType  # local import avoids circular dep
    catalog = list(OfferType.objects.values("id", "name", "description"))
    # key == name (OfferType uses name as the logical key used by the LLM)
    for entry in catalog:
        entry["key"] = entry["name"]
    cache.set(_CACHE_KEY, catalog, _CACHE_TTL)
    LOGGER.debug("Loaded %d offer types from DB into cache", len(catalog))
    return catalog


def invalidate_catalog() -> None:
    cache.delete(_CACHE_KEY)
