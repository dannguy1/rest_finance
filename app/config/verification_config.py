"""
Deposit verification configuration.

Bank-matching rules are keyed by *bank_source* (not location) so the same
bank config can be reused across locations.  Location→source resolution is
done via location_config.LOCATIONS; features receive plain source IDs and
do not need to know about locations at all.
"""
from typing import Dict, Any, Optional, List
from app.config.location_config import LOCATIONS, get_location


# Permissible deposit lag window (business days).
# Most batches settle in 1 business day; allow up to 3 for holiday weeks.
DEFAULT_LAG_DAYS = [1, 2, 3]


# Bank-specific matching rules.
# Keys are bank_source slugs (same as data directory names).
BANK_MATCHING_RULES: Dict[str, Dict[str, Any]] = {
    "bankofamerica": {
        # How to identify merchant card deposits inside the bank statement
        "bank_filter_pattern": "BANKCARD 8076",
        "bank_filter_type": "contains",      # contains | prefix | regex
        "bank_deposit_subtype": "BTOT DEP",  # only credits, not MTOT DISC fees
        "bank_date_format": "%m/%d/%Y",
        "merchant_date_format": "%Y-%m-%d",
        # BofA does not encode the original sale date; derive from deposit_date − lag.
        "bank_sale_date_regex": None,
        "deposit_lag_days": DEFAULT_LAG_DAYS,
        # Rows matching this pattern are adjustments — no corresponding deposit.
        "adjustment_pattern": "ADJ",
    },
    "chase": {
        "bank_filter_pattern": "BANKCARD 8076",
        "bank_filter_type": "contains",
        "bank_deposit_subtype": "BTOT DEP",
        "bank_date_format": "%m/%d/%Y",
        "merchant_date_format": "%Y-%m-%d",
        # Chase embeds the original sale date as "DESC DATE:YYMMDD" — use it directly.
        "bank_sale_date_regex": r"DESC DATE:(\d{6})",
        "deposit_lag_days": DEFAULT_LAG_DAYS,
        "adjustment_pattern": "ADJ",
    },
}


def get_verification_config(location_id: str) -> Optional[Dict[str, Any]]:
    """
    Return a complete verification config for a location, merging location
    metadata with bank-specific matching rules.  Returns None if the location
    or its bank source is not configured.
    """
    loc = get_location(location_id)
    if not loc:
        return None
    bank_source = loc["bank_source"]
    rules = BANK_MATCHING_RULES.get(bank_source)
    if not rules:
        return None
    return {
        "location_id": loc["location_id"],
        "display_name": loc["display_name"],
        "merchant_source": loc["merchant_source"],
        "bank_source": bank_source,
        **rules,
    }


def list_verification_configs() -> List[Dict[str, Any]]:
    """Return verification configs for all configured locations."""
    configs = []
    for loc_id in LOCATIONS:
        cfg = get_verification_config(loc_id)
        if cfg:
            configs.append(cfg)
    return configs
