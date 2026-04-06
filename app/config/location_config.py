"""
Location configuration.

A "location" represents a physical restaurant site.  Each location owns:
  - a bank data source  (e.g. bankofamerica, chase)
  - a merchant data source  (e.g. gg, ar) for card-processing batches
  - one or more vendor data sources  (e.g. restaurantdepot, sysco)

Features (verification, analytics, …) receive plain source IDs from the
location config and do not need to reason about location themselves.
"""
from typing import Dict, Any, List, Optional


LOCATIONS: Dict[str, Dict[str, Any]] = {
    "gg": {
        "location_id": "gg",
        "display_name": "GG (Garlic & Chives 2)",
        "bank_source": "bankofamerica",
        "merchant_source": "gg",
        "vendor_sources": ["restaurantdepot", "sysco"],
    },
    "ar": {
        "location_id": "ar",
        "display_name": "AR (Garlic & Chives)",
        "bank_source": "chase",
        "merchant_source": "ar",
        "vendor_sources": ["restaurantdepot", "sysco"],
    },
}


def get_location(location_id: str) -> Optional[Dict[str, Any]]:
    """Return location config dict, or None if not found."""
    return LOCATIONS.get(location_id.lower())


def list_locations() -> List[Dict[str, Any]]:
    """Return all location configs as a list."""
    return list(LOCATIONS.values())


def get_bank_source(location_id: str) -> Optional[str]:
    loc = get_location(location_id)
    return loc["bank_source"] if loc else None


def get_merchant_source(location_id: str) -> Optional[str]:
    loc = get_location(location_id)
    return loc["merchant_source"] if loc else None


def get_vendor_sources(location_id: str) -> List[str]:
    loc = get_location(location_id)
    return loc["vendor_sources"] if loc else []
