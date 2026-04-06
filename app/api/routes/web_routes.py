from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api.templates_config import templates
from app.config.location_config import LOCATIONS, get_location

router = APIRouter()

# Source configurations (display metadata — does not drive processing)
SOURCE_CONFIGS = {
    "bankofamerica": {
        "name": "Bank of America",
        "icon": "bank",
        "description": "Bank statement processing and management"
    },
    "chase": {
        "name": "Chase",
        "icon": "credit-card",
        "description": "Chase bank statement processing and management"
    },
    "sysco": {
        "name": "Sysco",
        "icon": "truck",
        "description": "Sysco supplier receipt processing and management"
    },
    "restaurantdepot": {
        "name": "Restaurant Depot",
        "icon": "shop",
        "description": "Restaurant Depot supplier receipt processing and management"
    },
    "gg": {
        "name": "GG",
        "icon": "credit-card",
        "description": "GG merchant statement processing and management"
    },
    "ar": {
        "name": "AR",
        "icon": "credit-card",
        "description": "AR merchant statement processing and management"
    }
}


def _location_context(location_id: str) -> dict:
    """Return template context variables for a given location."""
    loc = get_location(location_id)
    return {
        "location_id": location_id,
        "location_name": loc["display_name"] if loc else location_id.upper(),
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "page_title": "Dashboard",
        "page_description": "Overview of your financial data processing system"
    })


# ── Location-centric routes ────────────────────────────────────────────────

@router.get("/location/{location_id}/bank", response_class=HTMLResponse)
async def location_bank(request: Request, location_id: str):
    """Bank statement page for a specific location."""
    loc = get_location(location_id)
    if not loc:
        return RedirectResponse(url="/")
    source = loc["bank_source"]
    cfg = SOURCE_CONFIGS.get(source, {})
    return templates.TemplateResponse("source.html", {
        "request": request,
        "page_title": f"{loc['display_name']} — Bank Statement",
        "page_description": cfg.get("description", ""),
        "source": source,
        "source_name": cfg.get("name", source),
        "source_icon": cfg.get("icon", "bank"),
        "source_description": cfg.get("description", ""),
        **_location_context(location_id),
    })


@router.get("/location/{location_id}/merchant", response_class=HTMLResponse)
async def location_merchant(request: Request, location_id: str):
    """Merchant statement page for a specific location."""
    loc = get_location(location_id)
    if not loc:
        return RedirectResponse(url="/")
    source = loc["merchant_source"]
    cfg = SOURCE_CONFIGS.get(source, {})
    return templates.TemplateResponse("source.html", {
        "request": request,
        "page_title": f"{loc['display_name']} — Merchant Statement",
        "page_description": cfg.get("description", ""),
        "source": source,
        "source_name": cfg.get("name", source),
        "source_icon": cfg.get("icon", "credit-card"),
        "source_description": cfg.get("description", ""),
        **_location_context(location_id),
    })


@router.get("/location/{location_id}/verify", response_class=HTMLResponse)
async def location_verify(request: Request, location_id: str):
    """Deposit verification page pre-selected for a specific location."""
    loc = get_location(location_id)
    if not loc:
        return RedirectResponse(url="/verification")
    return templates.TemplateResponse("verification.html", {
        "request": request,
        "page_title": f"{loc['display_name']} — Deposit Verification",
        "page_description": "Verify merchant batch deposits against bank statement records",
        **_location_context(location_id),
    })


# ── Legacy / generic source routes (kept for backward compatibility) ───────

@router.get("/source/{source}", response_class=HTMLResponse)
async def source_page(request: Request, source: str):
    if source not in SOURCE_CONFIGS:
        return RedirectResponse(url="/")
    config = SOURCE_CONFIGS[source]
    return templates.TemplateResponse("source.html", {
        "request": request,
        "page_title": config["name"],
        "page_description": config["description"],
        "source": source,
        "source_name": config["name"],
        "source_icon": config["icon"],
        "source_description": config["description"]
    })

@router.get("/source/{source}/analytics", response_class=HTMLResponse)
async def source_analytics_page(request: Request, source: str):
    if source not in SOURCE_CONFIGS:
        return RedirectResponse(url="/")
    config = SOURCE_CONFIGS[source]
    return templates.TemplateResponse("source_analytics.html", {
        "request": request,
        "page_title": f"{config['name']} Analytics",
        "page_description": f"Analyze {config['name']} data with interactive charts and reports",
        "source": source,
        "source_name": config["name"],
        "source_icon": config["icon"],
        "source_description": config["description"]
    })

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("pages/upload.html", {
        "request": request,
        "page_title": "File Upload",
        "page_description": "Upload financial data files for processing"
    })

@router.get("/process", response_class=HTMLResponse)
async def process_page(request: Request):
    return templates.TemplateResponse("pages/process.html", {
        "request": request,
        "page_title": "Data Processing",
        "page_description": "Process uploaded files and generate organized reports"
    })

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse("pages/analytics.html", {
        "request": request,
        "page_title": "Analytics",
        "page_description": "Analyze your financial data with interactive charts and reports"
    })

@router.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    return templates.TemplateResponse("pages/download.html", {
        "request": request,
        "page_title": "Download",
        "page_description": "Download processed files and reports"
    })

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("pages/settings.html", {
        "request": request,
        "page_title": "Settings",
        "page_description": "Configure your application preferences"
    })

@router.get("/mapping", response_class=HTMLResponse)
async def mapping_page(request: Request):
    return templates.TemplateResponse("mapping.html", {
        "request": request,
        "page_title": "Source Mapping Configuration",
        "page_description": "Configure how source-specific columns map to normalized processed data"
    })

@router.get("/verification", response_class=HTMLResponse)
async def verification_page(request: Request):
    return templates.TemplateResponse("verification.html", {
        "request": request,
        "page_title": "Deposit Verification",
        "page_description": "Verify merchant batch deposits against bank statement records"
    })

@router.get("/api/pages/{page}")
async def get_page_content(page: str):
    return {
        "page": page,
        "content": f"<div class='dynamic-content'><h2>{page.title()} Content</h2><p>Dynamic content for {page} page.</p></div>"
    }

@router.get("/api/dashboard")
async def get_dashboard_data():
    return {
        "totalFiles": 42,
        "processingJobs": 3,
        "processedRecords": 15420,
        "outputFiles": 28
    }

