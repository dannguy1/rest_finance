"""
Deposit verification configuration.

Each entry pairs a merchant source with its corresponding bank source and
defines how to identify merchant deposits within the bank statement data.
"""
from typing import Dict, Any, Optional


# Supported deposit lag values in business days.
# Most batches settle in 1 business day; allow up to 3 to handle holiday weeks.
DEFAULT_LAG_DAYS = [1, 2, 3]


VERIFICATION_PAIRS: Dict[str, Dict[str, Any]] = {
    "gg": {
        "location_id": "gg",
        "display_name": "GG (Garlic & Chives 2)",
        # Data sources
        "merchant_source": "gg",
        "bank_source": "bankofamerica",
        # How to identify merchant deposits inside the bank statement
        "bank_filter_pattern": "BANKCARD 8076",
        "bank_filter_type": "contains",       # contains | prefix | regex
        "bank_deposit_subtype": "BTOT DEP",   # only credits, not MTOT DISC fees
        # Date formats used in the output CSVs
        "bank_date_format": "%m/%d/%Y",
        "merchant_date_format": "%Y-%m-%d",
        # Chase embeds the original sale date in the description as DESC DATE:YYMMDD.
        # BofA does not; we derive the sale date from deposit_date - lag instead.
        "bank_sale_date_regex": None,
        # Permissible deposit lag window (business days)
        "deposit_lag_days": DEFAULT_LAG_DAYS,
        # Rows with negative amounts or description matching this pattern are
        # considered adjustments; they never produce a bank deposit.
        "adjustment_pattern": "ADJ",
    },
    "ar": {
        "location_id": "ar",
        "display_name": "AR (Garlic & Chives)",
        "merchant_source": "ar",
        "bank_source": "chase",
        "bank_filter_pattern": "BANKCARD 8076",
        "bank_filter_type": "contains",
        "bank_deposit_subtype": "BTOT DEP",
        "bank_date_format": "%m/%d/%Y",
        "merchant_date_format": "%Y-%m-%d",
        # Chase description contains "DESC DATE:YYMMDD" — extract authoritative sale date.
        "bank_sale_date_regex": r"DESC DATE:(\d{6})",
        "deposit_lag_days": DEFAULT_LAG_DAYS,
        "adjustment_pattern": "ADJ",
    },
}


def get_verification_config(location_id: str) -> Optional[Dict[str, Any]]:
    """Return verification pair config for a location, or None if not found."""
    return VERIFICATION_PAIRS.get(location_id.lower())


def list_verification_configs() -> list:
    """Return all verification pair configs as a list."""
    return list(VERIFICATION_PAIRS.values())
