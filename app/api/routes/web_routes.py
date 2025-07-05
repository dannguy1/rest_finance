from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.api.templates_config import templates

router = APIRouter()

# Source configurations
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
    }
}

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "page_title": "Dashboard",
        "page_description": "Overview of your financial data processing system"
    })

@router.get("/source/{source}", response_class=HTMLResponse)
async def source_page(request: Request, source: str):
    """Source-specific application page"""
    if source not in SOURCE_CONFIGS:
        # Redirect to dashboard if source not found
        from fastapi.responses import RedirectResponse
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

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """File upload page"""
    return templates.TemplateResponse("pages/upload.html", {
        "request": request,
        "page_title": "File Upload",
        "page_description": "Upload financial data files for processing"
    })

@router.get("/process", response_class=HTMLResponse)
async def process_page(request: Request):
    """Data processing page"""
    return templates.TemplateResponse("pages/process.html", {
        "request": request,
        "page_title": "Data Processing",
        "page_description": "Process uploaded files and generate organized reports"
    })

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics page"""
    return templates.TemplateResponse("pages/analytics.html", {
        "request": request,
        "page_title": "Analytics",
        "page_description": "Analyze your financial data with interactive charts and reports"
    })

@router.get("/download", response_class=HTMLResponse)
async def download_page(request: Request):
    """Download page"""
    return templates.TemplateResponse("pages/download.html", {
        "request": request,
        "page_title": "Download",
        "page_description": "Download processed files and reports"
    })

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("pages/settings.html", {
        "request": request,
        "page_title": "Settings",
        "page_description": "Configure your application preferences"
    })

@router.get("/mapping", response_class=HTMLResponse)
async def mapping_page(request: Request):
    """Source mapping configuration page"""
    return templates.TemplateResponse("mapping.html", {
        "request": request,
        "page_title": "Source Mapping Configuration",
        "page_description": "Configure how source-specific columns map to normalized processed data"
    })

# API endpoints for dynamic content
@router.get("/api/pages/{page}")
async def get_page_content(page: str):
    """Get dynamic page content"""
    # This would typically load content from a database or file system
    # For now, return a simple response
    return {
        "page": page,
        "content": f"<div class='dynamic-content'><h2>{page.title()} Content</h2><p>Dynamic content for {page} page.</p></div>"
    }

@router.get("/api/dashboard")
async def get_dashboard_data():
    """Get dashboard statistics"""
    # This would typically load real data from the database
    return {
        "totalFiles": 42,
        "processingJobs": 3,
        "processedRecords": 15420,
        "outputFiles": 28
    } 