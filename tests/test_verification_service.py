"""Tests for VerificationService matching logic."""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.services.verification_service import (
    VerificationService,
    MerchantBatch,
    BankDeposit,
    _add_business_days,
    _business_days_between,
    _is_business_day,
)
from app.config.verification_config import get_verification_config


# ---------------------------------------------------------------------------
# Business day helpers
# ---------------------------------------------------------------------------

class TestBusinessDayHelpers:
    def test_weekday_is_business_day(self):
        assert _is_business_day(date(2025, 1, 6))   # Monday

    def test_saturday_not_business_day(self):
        assert not _is_business_day(date(2025, 1, 4))  # Saturday

    def test_sunday_not_business_day(self):
        assert not _is_business_day(date(2025, 1, 5))  # Sunday

    def test_holiday_not_business_day(self):
        assert not _is_business_day(date(2025, 1, 1))  # New Year's

    def test_add_one_business_day_weekday(self):
        # Monday Jan 6 + 1 = Tuesday Jan 7
        assert _add_business_days(date(2025, 1, 6), 1) == date(2025, 1, 7)

    def test_add_one_business_day_friday(self):
        # Friday Jan 3 + 1 = Monday Jan 6
        assert _add_business_days(date(2025, 1, 3), 1) == date(2025, 1, 6)

    def test_add_one_business_day_saturday(self):
        # Saturday Jan 4 + 1 = Monday Jan 6
        assert _add_business_days(date(2025, 1, 4), 1) == date(2025, 1, 6)

    def test_add_one_business_day_sunday(self):
        # Sunday Jan 5 + 1 = Monday Jan 6
        assert _add_business_days(date(2025, 1, 5), 1) == date(2025, 1, 6)

    def test_business_days_between(self):
        # Mon to Wed = 2 business days
        assert _business_days_between(date(2025, 1, 6), date(2025, 1, 8)) == 2

    def test_business_days_between_across_weekend(self):
        # Friday to Monday = 1 business day
        assert _business_days_between(date(2025, 1, 3), date(2025, 1, 6)) == 1


# ---------------------------------------------------------------------------
# Verification config
# ---------------------------------------------------------------------------

class TestVerificationConfig:
    def test_gg_config_exists(self):
        cfg = get_verification_config("gg")
        assert cfg is not None
        assert cfg["merchant_source"] == "gg"
        assert cfg["bank_source"] == "bankofamerica"

    def test_ar_config_exists(self):
        cfg = get_verification_config("ar")
        assert cfg is not None
        assert cfg["merchant_source"] == "ar"
        assert cfg["bank_source"] == "chase"
        assert cfg["bank_sale_date_regex"] is not None

    def test_unknown_returns_none(self):
        assert get_verification_config("nonexistent") is None


# ---------------------------------------------------------------------------
# Matching logic (unit tests with synthetic data)
# ---------------------------------------------------------------------------

def _make_service():
    svc = VerificationService.__new__(VerificationService)
    svc.data_dir = Path("/fake")
    return svc


class TestMatching:
    """Unit-test the internal _match method with synthetic batches/deposits."""

    def _cfg(self, with_sale_date_regex=False):
        return {
            "deposit_lag_days": [1, 2, 3],
            "bank_sale_date_regex": r"DESC DATE:(\d{6})" if with_sale_date_regex else None,
        }

    def test_exact_match_one_business_day(self):
        svc = _make_service()
        cfg = self._cfg()
        batches = [MerchantBatch(sale_date=date(2025, 1, 6), amount=1000.0, ref="REF1")]
        deposits = [BankDeposit(deposit_date=date(2025, 1, 7), amount=1000.0, description="BANKCARD DEP")]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 1
        assert pairs[0]["merchant_ref"] == "REF1"
        assert pairs[0]["lag_days"] == 1

    def test_exact_match_weekend_delay(self):
        svc = _make_service()
        cfg = self._cfg()
        # Friday sale → Monday deposit (1 business day)
        batches = [MerchantBatch(sale_date=date(2025, 1, 3), amount=500.0, ref="REF_FRI")]
        deposits = [BankDeposit(deposit_date=date(2025, 1, 6), amount=500.0, description="BANKCARD DEP")]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 1
        assert pairs[0]["lag_days"] == 1  # 1 business day

    def test_no_match_wrong_amount(self):
        svc = _make_service()
        cfg = self._cfg()
        batches = [MerchantBatch(sale_date=date(2025, 1, 6), amount=1000.0, ref="REF1")]
        deposits = [BankDeposit(deposit_date=date(2025, 1, 7), amount=999.0, description="BANKCARD DEP")]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 0
        assert not batches[0].matched
        assert not deposits[0].matched

    def test_no_match_wrong_date(self):
        svc = _make_service()
        cfg = self._cfg()
        batches = [MerchantBatch(sale_date=date(2025, 1, 6), amount=1000.0, ref="REF1")]
        # Deposit 5 calendar days later (> 3 business day window)
        deposits = [BankDeposit(deposit_date=date(2025, 1, 13), amount=1000.0, description="BANKCARD DEP")]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 0

    def test_adjustments_excluded(self):
        svc = _make_service()
        cfg = self._cfg()
        batches = [
            MerchantBatch(sale_date=date(2025, 1, 6), amount=1000.0, ref="REF1"),
            MerchantBatch(sale_date=date(2025, 1, 6), amount=-50.0, ref="MOADJ", is_adjustment=True),
        ]
        deposits = [BankDeposit(deposit_date=date(2025, 1, 7), amount=1000.0, description="BANKCARD DEP")]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 1  # only real batch matched; adjustment ignored

    def test_multiple_batches_same_day(self):
        svc = _make_service()
        cfg = self._cfg()
        batches = [
            MerchantBatch(sale_date=date(2025, 1, 6), amount=100.0, ref="A"),
            MerchantBatch(sale_date=date(2025, 1, 6), amount=200.0, ref="B"),
        ]
        deposits = [
            BankDeposit(deposit_date=date(2025, 1, 7), amount=100.0, description="BANKCARD DEP"),
            BankDeposit(deposit_date=date(2025, 1, 7), amount=200.0, description="BANKCARD DEP"),
        ]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 2
        assert all(b.matched for b in batches)
        assert all(d.matched for d in deposits)

    def test_one_deposit_not_reused(self):
        """A deposit must not match two batches with the same amount."""
        svc = _make_service()
        cfg = self._cfg()
        batches = [
            MerchantBatch(sale_date=date(2025, 1, 6), amount=500.0, ref="A"),
            MerchantBatch(sale_date=date(2025, 1, 6), amount=500.0, ref="B"),
        ]
        deposits = [
            BankDeposit(deposit_date=date(2025, 1, 7), amount=500.0, description="BANKCARD DEP"),
        ]
        pairs = svc._match(batches, deposits, cfg)
        # Only one match possible since there is only one deposit
        assert len(pairs) == 1

    def test_chase_sale_date_from_description(self):
        """Chase deposits carry the sale date in DESC DATE:YYMMDD."""
        svc = _make_service()
        cfg = self._cfg(with_sale_date_regex=True)
        batches = [
            MerchantBatch(sale_date=date(2025, 2, 2), amount=826.22, ref="BATCH1"),
        ]
        desc = "BANKCARD 8076 DESC DATE:250202 BTOT DEP"
        deposits = [
            BankDeposit(
                deposit_date=date(2025, 2, 3),
                amount=826.22,
                description=desc,
                sale_date=date(2025, 2, 2),  # pre-extracted (as done in _load_bank_deposits)
            )
        ]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 1
        assert batches[0].matched

    def test_chase_sale_date_mismatch_no_match(self):
        """If Chase DESC DATE doesn't match batch sale date, skip it."""
        svc = _make_service()
        cfg = self._cfg(with_sale_date_regex=True)
        batches = [MerchantBatch(sale_date=date(2025, 2, 3), amount=826.22, ref="BATCH1")]
        deposits = [
            BankDeposit(
                deposit_date=date(2025, 2, 4),
                amount=826.22,
                description="BANKCARD 8076 DESC DATE:250202 BTOT DEP",
                sale_date=date(2025, 2, 2),  # different sale date
            )
        ]
        pairs = svc._match(batches, deposits, cfg)
        assert len(pairs) == 0


# ---------------------------------------------------------------------------
# Day summaries
# ---------------------------------------------------------------------------

class TestDaySummaries:
    def test_fully_matched_day(self):
        svc = _make_service()
        batch = MerchantBatch(
            sale_date=date(2025, 1, 6), amount=1000.0, ref="R",
            matched=True, matched_deposit_date=date(2025, 1, 7), matched_deposit_amount=1000.0
        )
        summaries = svc._build_day_summaries([batch], [])
        assert len(summaries) == 1
        assert summaries[0].status == "matched"
        assert summaries[0].merchant_total == 1000.0

    def test_unmatched_day(self):
        svc = _make_service()
        batch = MerchantBatch(sale_date=date(2025, 1, 6), amount=1000.0, ref="R", matched=False)
        summaries = svc._build_day_summaries([batch], [])
        assert summaries[0].status == "missing"

    def test_adjustment_only_day(self):
        svc = _make_service()
        adj = MerchantBatch(
            sale_date=date(2025, 1, 6), amount=-50.0, ref="MOADJ", is_adjustment=True
        )
        summaries = svc._build_day_summaries([adj], [])
        assert summaries[0].status == "adjustment"

    def test_partial_day(self):
        svc = _make_service()
        batches = [
            MerchantBatch(sale_date=date(2025, 1, 6), amount=100.0, ref="A",
                          matched=True, matched_deposit_date=date(2025, 1, 7), matched_deposit_amount=100.0),
            MerchantBatch(sale_date=date(2025, 1, 6), amount=200.0, ref="B", matched=False),
        ]
        summaries = svc._build_day_summaries(batches, [])
        assert summaries[0].status == "partial"
