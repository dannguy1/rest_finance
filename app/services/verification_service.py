"""
Deposit verification service.

Matches merchant batch records against bank deposit entries to verify that
every batch has a corresponding deposit within the expected settlement window.

Matching rules:
  - Each merchant batch (positive amount) should appear as a separate bank
    deposit line with an exactly matching amount.
  - The deposit arrives 1–3 business days after the sale date.
  - For BofA (GG): the sale date is inferred as deposit_date − lag.
  - For Chase (AR): the sale date is embedded in the description as
    DESC DATE:YYMMDD and is authoritative.
  - Negative-amount rows or rows whose description contains the
    adjustment_pattern are excluded from matching (they are adjustments).
  - Matching is greedy and 1:1 — each deposit line can match at most one batch.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.config.settings import settings
from app.config.verification_config import get_verification_config
from app.utils.logging import processing_logger

# US Federal holidays for 2024-2026 (add years as needed).
# These are treated as non-business days for lag calculation.
_US_HOLIDAYS: set = {
    date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 19), date(2024, 5, 27),
    date(2024, 6, 19), date(2024, 7, 4), date(2024, 9, 2), date(2024, 11, 11),
    date(2024, 11, 28), date(2024, 12, 25),
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17), date(2025, 5, 26),
    date(2025, 6, 19), date(2025, 7, 4), date(2025, 9, 1), date(2025, 11, 11),
    date(2025, 11, 27), date(2025, 12, 25),
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 5, 25),
    date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7), date(2026, 11, 11),
    date(2026, 11, 26), date(2026, 12, 25),
}


def _is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _US_HOLIDAYS


def _add_business_days(d: date, n: int) -> date:
    """Return the date that is n business days after d."""
    current = d
    added = 0
    while added < n:
        current += timedelta(days=1)
        if _is_business_day(current):
            added += 1
    return current


def _business_days_between(start: date, end: date) -> int:
    """Return the number of business days from start (exclusive) to end (inclusive)."""
    if end <= start:
        return 0
    count = 0
    current = start + timedelta(days=1)
    while current <= end:
        if _is_business_day(current):
            count += 1
        current += timedelta(days=1)
    return count


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MerchantBatch:
    sale_date: date
    amount: float
    ref: str
    is_adjustment: bool = False
    matched: bool = False
    matched_deposit_date: Optional[date] = None
    matched_deposit_amount: Optional[float] = None


@dataclass
class BankDeposit:
    deposit_date: date
    amount: float
    description: str
    sale_date: Optional[date] = None   # known for Chase; inferred for BofA
    matched: bool = False
    matched_batch_ref: Optional[str] = None
    matched_sale_date: Optional[date] = None


@dataclass
class DaySummary:
    sale_date: date
    merchant_batches: int
    merchant_total: float
    deposit_date: Optional[date]        # earliest deposit date for this sale day
    bank_deposits: int
    bank_total: float
    matched_count: int
    status: str                         # "matched" | "partial" | "missing" | "adjustment"


@dataclass
class VerificationResult:
    location_id: str
    display_name: str
    year: int
    month: int
    # Aggregate counts
    total_merchant_batches: int
    total_adjustments: int
    total_bank_deposits: int
    matched_count: int
    unmatched_merchant_count: int
    unmatched_bank_count: int
    # Aggregate amounts
    total_merchant_amount: float
    total_bank_amount: float
    matched_amount: float
    unmatched_merchant_amount: float
    unmatched_bank_amount: float
    # Derived
    match_rate: float                   # 0–100 %
    variance: float                     # total_bank - total_merchant (signed)
    # Detail
    day_summaries: List[DaySummary] = field(default_factory=list)
    unmatched_batches: List[MerchantBatch] = field(default_factory=list)
    unmatched_deposits: List[BankDeposit] = field(default_factory=list)
    matched_pairs: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class VerificationService:
    """Verifies merchant batches against bank deposits."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else settings.data_path

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def verify(self, location_id: str, year: int, month: int) -> VerificationResult:
        """Run deposit verification for one location/month."""
        cfg = get_verification_config(location_id)
        if cfg is None:
            raise ValueError(f"Unknown verification location: {location_id}")

        batches = self._load_merchant_batches(cfg, year, month)
        deposits = self._load_bank_deposits(cfg, year, month)

        matched_pairs = self._match(batches, deposits, cfg)
        day_summaries = self._build_day_summaries(batches, deposits)

        adjustments = [b for b in batches if b.is_adjustment]
        real_batches = [b for b in batches if not b.is_adjustment]
        unmatched_batches = [b for b in real_batches if not b.matched]
        unmatched_deposits = [d for d in deposits if not d.matched]

        total_merchant = round(sum(b.amount for b in real_batches), 2)
        total_bank = round(sum(d.amount for d in deposits), 2)
        matched_amount = round(sum(p["amount"] for p in matched_pairs), 2)
        match_rate = (
            round(len(matched_pairs) / len(real_batches) * 100, 1)
            if real_batches else 100.0
        )

        return VerificationResult(
            location_id=location_id,
            display_name=cfg["display_name"],
            year=year,
            month=month,
            total_merchant_batches=len(real_batches),
            total_adjustments=len(adjustments),
            total_bank_deposits=len(deposits),
            matched_count=len(matched_pairs),
            unmatched_merchant_count=len(unmatched_batches),
            unmatched_bank_count=len(unmatched_deposits),
            total_merchant_amount=total_merchant,
            total_bank_amount=total_bank,
            matched_amount=matched_amount,
            unmatched_merchant_amount=round(
                sum(b.amount for b in unmatched_batches), 2),
            unmatched_bank_amount=round(
                sum(d.amount for d in unmatched_deposits), 2),
            match_rate=match_rate,
            variance=round(total_bank - total_merchant, 2),
            day_summaries=day_summaries,
            unmatched_batches=unmatched_batches,
            unmatched_deposits=unmatched_deposits,
            matched_pairs=matched_pairs,
        )

    def available_months(self, location_id: str) -> List[Dict[str, int]]:
        """Return list of {year, month} dicts where both merchant and bank data exist."""
        cfg = get_verification_config(location_id)
        if cfg is None:
            return []

        merchant_dir = self.data_dir / cfg["merchant_source"] / "output"
        bank_dir = self.data_dir / cfg["bank_source"] / "output"

        available = []
        for year_dir in sorted(merchant_dir.glob("*")):
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue
            year = int(year_dir.name)
            bank_year_dir = bank_dir / str(year)
            for csv_file in sorted(year_dir.glob("*.csv")):
                stem = csv_file.stem   # e.g. "01_2025"
                parts = stem.split("_")
                if len(parts) != 2:
                    continue
                month = int(parts[0])
                # Check that bank data also exists for this month
                bank_file = bank_year_dir / csv_file.name
                if bank_file.exists():
                    available.append({"year": year, "month": month})

        return available

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_merchant_batches(
        self, cfg: Dict[str, Any], year: int, month: int
    ) -> List[MerchantBatch]:
        """Load merchant batches for the given month."""
        path = self.data_dir / cfg["merchant_source"] / "output" / str(year) / f"{month:02d}_{year}.csv"
        if not path.exists():
            processing_logger.log_system_event(
                f"Merchant data not found: {path}", level="warning"
            )
            return []

        df = pd.read_csv(path)
        date_fmt = cfg["merchant_date_format"]
        adj_pattern = cfg.get("adjustment_pattern", "ADJ")
        batches: List[MerchantBatch] = []

        for _, row in df.iterrows():
            try:
                sale_date = pd.to_datetime(
                    str(row["Date"]), format=date_fmt
                ).date()
                amount = float(row["Amount"])
                ref = str(row.get("Description", ""))
                is_adj = amount < 0 or bool(re.search(adj_pattern, ref, re.IGNORECASE))
                batches.append(MerchantBatch(
                    sale_date=sale_date,
                    amount=round(abs(amount), 2) if not is_adj else round(amount, 2),
                    ref=ref,
                    is_adjustment=is_adj,
                ))
            except Exception as e:
                processing_logger.log_system_event(
                    f"Skipping merchant row: {e}", level="warning"
                )

        processing_logger.log_system_event(
            f"Loaded {len(batches)} merchant batches from {path.name}"
        )
        return batches

    def _load_bank_deposits(
        self, cfg: Dict[str, Any], year: int, month: int
    ) -> List[BankDeposit]:
        """Load bank deposits for month and adjacent months (for boundary handling)."""
        filter_pattern = cfg["bank_filter_pattern"]
        subtype = cfg.get("bank_deposit_subtype", "")
        date_fmt = cfg["bank_date_format"]
        sale_date_regex = cfg.get("bank_sale_date_regex")
        bank_source = cfg["bank_source"]
        lag_days = cfg["deposit_lag_days"]
        max_lag = max(lag_days)

        # Collect files: previous month (for late Jan deposits on Dec batches)
        # and current + next month (for cross-month deposits).
        file_keys = self._adjacent_month_keys(year, month)
        all_rows: List[BankDeposit] = []

        for (y, m) in file_keys:
            path = self.data_dir / bank_source / "output" / str(y) / f"{m:02d}_{y}.csv"
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except Exception as e:
                processing_logger.log_system_event(
                    f"Could not read bank file {path}: {e}", level="warning"
                )
                continue

            for _, row in df.iterrows():
                try:
                    desc = str(row.get("Description", ""))
                    if filter_pattern.lower() not in desc.lower():
                        continue
                    if subtype and subtype.upper() not in desc.upper():
                        continue
                    amount = float(row["Amount"])
                    if amount <= 0:
                        continue   # skip fees/debits

                    dep_date = pd.to_datetime(str(row["Date"]), format=date_fmt).date()

                    # Determine sale date
                    sale_date: Optional[date] = None
                    if sale_date_regex:
                        m_obj = re.search(sale_date_regex, desc)
                        if m_obj:
                            raw = m_obj.group(1)          # YYMMDD
                            sale_date = date(
                                2000 + int(raw[:2]), int(raw[2:4]), int(raw[4:])
                            )
                    # For BofA (no embedded date) we leave sale_date=None;
                    # it gets filled in lazily during matching.

                    all_rows.append(BankDeposit(
                        deposit_date=dep_date,
                        amount=round(amount, 2),
                        description=desc,
                        sale_date=sale_date,
                    ))
                except Exception as e:
                    processing_logger.log_system_event(
                        f"Skipping bank row: {e}", level="warning"
                    )

        # Keep only deposits that fall within a reasonable window around the target month.
        # We extend ±(max_lag+2) calendar days around the month boundaries.
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        window_start = month_start - timedelta(days=1)
        window_end = month_end + timedelta(days=max_lag + 3)

        filtered = [d for d in all_rows if window_start <= d.deposit_date <= window_end]
        processing_logger.log_system_event(
            f"Loaded {len(filtered)} bank deposits for {year}-{month:02d} window"
        )
        return filtered

    @staticmethod
    def _adjacent_month_keys(year: int, month: int) -> List[Tuple[int, int]]:
        """Return (year, month) for previous, current, and next month."""
        keys = []
        for delta in (-1, 0, 1):
            m = month + delta
            y = year
            if m < 1:
                m = 12; y -= 1
            elif m > 12:
                m = 1; y += 1
            keys.append((y, m))
        return keys

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def _match(
        self,
        batches: List[MerchantBatch],
        deposits: List[BankDeposit],
        cfg: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Greedy 1:1 matching: for each merchant batch find a bank deposit with
        the same amount whose deposit_date falls within the expected lag window.

        Batches are processed in sale_date order (ascending) to prefer
        earlier matches when amounts repeat.
        """
        lag_days = cfg["deposit_lag_days"]
        tolerance = 0.01
        pairs: List[Dict[str, Any]] = []

        # Build a dict: amount → list of unmatched deposits with that amount
        from collections import defaultdict
        deposit_by_amount: Dict[float, List[BankDeposit]] = defaultdict(list)
        for dep in deposits:
            deposit_by_amount[dep.amount].append(dep)

        real_batches = sorted(
            [b for b in batches if not b.is_adjustment],
            key=lambda b: b.sale_date,
        )

        for batch in real_batches:
            # Compute all valid deposit dates for this batch
            valid_dates: set[date] = set()
            for lag in lag_days:
                valid_dates.add(_add_business_days(batch.sale_date, lag))

            # Look for a deposit with matching amount on one of those dates
            best: Optional[BankDeposit] = None
            for dep in deposit_by_amount.get(batch.amount, []):
                if dep.matched:
                    continue
                # For deposits with known sale_date (Chase), verify it matches
                if dep.sale_date is not None:
                    if dep.sale_date != batch.sale_date:
                        continue
                else:
                    # BofA: verify deposit_date is in the valid window
                    if dep.deposit_date not in valid_dates:
                        continue
                best = dep
                break  # take first eligible

            if best is not None:
                best.matched = True
                best.matched_batch_ref = batch.ref
                best.matched_sale_date = batch.sale_date
                batch.matched = True
                batch.matched_deposit_date = best.deposit_date
                batch.matched_deposit_amount = best.amount

                pairs.append({
                    "sale_date": batch.sale_date.isoformat(),
                    "merchant_ref": batch.ref,
                    "amount": batch.amount,
                    "deposit_date": best.deposit_date.isoformat(),
                    "lag_days": _business_days_between(batch.sale_date, best.deposit_date),
                    "bank_description": best.description[:80],
                })

        return pairs

    # ------------------------------------------------------------------
    # Day-level summary
    # ------------------------------------------------------------------

    def _build_day_summaries(
        self,
        batches: List[MerchantBatch],
        deposits: List[BankDeposit],
    ) -> List[DaySummary]:
        """Aggregate matched/unmatched into per-sale-date summaries."""
        from collections import defaultdict

        # Group batches by sale_date
        by_sale: Dict[date, List[MerchantBatch]] = defaultdict(list)
        for b in batches:
            by_sale[b.sale_date].append(b)

        summaries: List[DaySummary] = []

        for sale_day in sorted(by_sale.keys()):
            day_batches = by_sale[sale_day]
            real = [b for b in day_batches if not b.is_adjustment]
            adjs = [b for b in day_batches if b.is_adjustment]

            if not real and adjs:
                summaries.append(DaySummary(
                    sale_date=sale_day,
                    merchant_batches=0,
                    merchant_total=round(sum(b.amount for b in adjs), 2),
                    deposit_date=None,
                    bank_deposits=0,
                    bank_total=0.0,
                    matched_count=0,
                    status="adjustment",
                ))
                continue

            matched = [b for b in real if b.matched]
            unmatched = [b for b in real if not b.matched]
            merchant_total = round(sum(b.amount for b in real), 2)

            # Collect the deposit dates and amounts for matched batches
            deposit_dates = [b.matched_deposit_date for b in matched if b.matched_deposit_date]
            bank_total = round(sum(b.matched_deposit_amount or 0 for b in matched), 2)
            earliest_dep = min(deposit_dates) if deposit_dates else None

            if not real:
                status = "adjustment"
            elif len(matched) == len(real):
                status = "matched"
            elif matched:
                status = "partial"
            else:
                status = "missing"

            summaries.append(DaySummary(
                sale_date=sale_day,
                merchant_batches=len(real),
                merchant_total=merchant_total,
                deposit_date=earliest_dep,
                bank_deposits=len(matched),
                bank_total=bank_total,
                matched_count=len(matched),
                status=status,
            ))

        return summaries


# Module-level singleton
verification_service = VerificationService()
