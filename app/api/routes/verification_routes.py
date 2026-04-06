"""
Deposit verification API routes.

Endpoints:
  GET /api/verification/configs
      List all configured merchant→bank verification pairs.

  GET /api/verification/{location_id}/available-months
      List year/month combinations where both merchant and bank data exist.

  GET /api/verification/{location_id}/{year}/{month}
      Run deposit verification for a specific location and month.
      Returns a summary + per-day detail + unmatched items.
"""
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings
from app.config.verification_config import get_verification_config, list_verification_configs
from app.services.verification_service import verification_service
from app.utils.logging import processing_logger

router = APIRouter(prefix="/api/verification", tags=["verification"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/configs")
@limiter.limit(settings.rate_limit_api)
async def get_verification_configs(request: Request):
    """Return all configured merchant→bank verification pairs."""
    configs = list_verification_configs()
    return {
        "configs": [
            {
                "location_id": c["location_id"],
                "display_name": c["display_name"],
                "merchant_source": c["merchant_source"],
                "bank_source": c["bank_source"],
            }
            for c in configs
        ]
    }


@router.get("/{location_id}/available-months")
@limiter.limit(settings.rate_limit_api)
async def get_available_months(location_id: str, request: Request):
    """Return year/month pairs that have data for both merchant and bank sources."""
    cfg = get_verification_config(location_id)
    if cfg is None:
        return {"error": f"Unknown location: {location_id}", "months": []}

    months = verification_service.available_months(location_id)
    return {
        "location_id": location_id,
        "display_name": cfg["display_name"],
        "months": months,
    }


@router.get("/{location_id}/{year}/{month}")
@limiter.limit(settings.rate_limit_api)
async def run_verification(
    location_id: str,
    year: int,
    month: int,
    request: Request,
):
    """
    Run deposit verification for a location and month.

    Returns:
      - summary: aggregate match statistics
      - day_summaries: per-sale-date breakdown
      - unmatched_batches: merchant batches with no matching bank deposit
      - unmatched_deposits: bank deposits not matched to any merchant batch
      - matched_pairs: all successfully matched batch↔deposit pairs
    """
    cfg = get_verification_config(location_id)
    if cfg is None:
        return {"error": f"Unknown location: {location_id}", "success": False}

    if not (1 <= month <= 12):
        return {"error": "month must be 1–12", "success": False}

    processing_logger.log_system_event(
        f"Running deposit verification for {location_id} {year}-{month:02d}"
    )

    try:
        result = verification_service.verify(location_id, year, month)
    except Exception as e:
        processing_logger.log_system_event(
            f"Verification failed for {location_id} {year}-{month:02d}: {e}",
            level="error",
        )
        return {"error": str(e), "success": False}

    # Serialise dataclasses to plain dicts
    day_summaries = [
        {
            "sale_date": s.sale_date.isoformat(),
            "merchant_batches": s.merchant_batches,
            "merchant_total": s.merchant_total,
            "deposit_date": s.deposit_date.isoformat() if s.deposit_date else None,
            "bank_deposits": s.bank_deposits,
            "bank_total": s.bank_total,
            "matched_count": s.matched_count,
            "status": s.status,
        }
        for s in result.day_summaries
    ]

    unmatched_batches = [
        {
            "sale_date": b.sale_date.isoformat(),
            "ref": b.ref,
            "amount": b.amount,
        }
        for b in result.unmatched_batches
    ]

    unmatched_deposits = [
        {
            "deposit_date": d.deposit_date.isoformat(),
            "amount": d.amount,
            "description": d.description[:120],
            "sale_date": d.sale_date.isoformat() if d.sale_date else None,
        }
        for d in result.unmatched_deposits
    ]

    discrepancies = [
        {
            "date": item.date,
            "amount": item.amount,
            "ref": item.ref,
            "discrepancy_type": item.discrepancy_type,
            "reason": item.reason,
            "action": item.action,
            "severity": item.severity,
            "detail": item.detail,
        }
        for item in result.discrepancies
    ]

    return {
        "success": True,
        "location_id": result.location_id,
        "display_name": result.display_name,
        "year": result.year,
        "month": result.month,
        "summary": {
            "total_merchant_batches": result.total_merchant_batches,
            "total_adjustments": result.total_adjustments,
            "total_bank_deposits": result.total_bank_deposits,
            "matched_count": result.matched_count,
            "unmatched_merchant_count": result.unmatched_merchant_count,
            "unmatched_bank_count": result.unmatched_bank_count,
            "total_merchant_amount": result.total_merchant_amount,
            "total_bank_amount": result.total_bank_amount,
            "matched_amount": result.matched_amount,
            "unmatched_merchant_amount": result.unmatched_merchant_amount,
            "unmatched_bank_amount": result.unmatched_bank_amount,
            "match_rate": result.match_rate,
            "variance": result.variance,
            "discrepancy_count": len(result.discrepancies),
            "discrepancy_amount": round(sum(i.amount for i in result.discrepancies), 2),
            "high_severity_count": sum(1 for i in result.discrepancies if i.severity == "high"),
        },
        "day_summaries": day_summaries,
        "unmatched_batches": unmatched_batches,
        "unmatched_deposits": unmatched_deposits,
        "discrepancies": discrepancies,
        "matched_pairs": result.matched_pairs,
    }
