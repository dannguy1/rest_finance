"""
Data processing routes for Financial Data Processor.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.utils.logging import processing_logger
from app.services.processing_service import DataProcessor
from app.services.file_service import FileService
from app.models.file_models import (
    SourceType, 
    ProcessingOptions, 
    ProcessingResult,
    ProcessingStatus,
    ProcessingProgress
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize services
processor = DataProcessor()
file_service = FileService()

# Source configuration with format details
SOURCE_CONFIGS = {
    "bankofamerica": {
        "name": "BankOfAmerica",
        "display_name": "Bank of America",
        "description": "Bank statement processing",
        "required_columns": ["Status", "Date", "Original Description", "Amount"],
        "date_column": "Date",
        "description_column": "Original Description",
        "amount_column": "Amount",
        "date_format": "MM/DD/YYYY"
    },
    "chase": {
        "name": "Chase",
        "display_name": "Chase",
        "description": "Chase bank statement processing",
        "required_columns": ["Posting Date", "Description", "Amount"],
        "optional_columns": ["Details", "Type", "Balance", "Check or Slip #"],
        "date_column": "Posting Date",
        "description_column": "Description",
        "amount_column": "Amount",
        "date_format": "MM/DD/YYYY"
    },
    "restaurantdepot": {
        "name": "RestaurantDepot",
        "display_name": "Restaurant Depot",
        "description": "Restaurant Depot invoice processing",
        "required_columns": ["Date", "Description", "Total"],
        "date_column": "Date",
        "description_column": "Description",
        "amount_column": "Total",
        "date_format": "MM/DD/YYYY"
    },
    "sysco": {
        "name": "Sysco",
        "display_name": "Sysco",
        "description": "Sysco invoice processing",
        "required_columns": ["Date", "Description", "Total"],
        "date_column": "Date",
        "description_column": "Description",
        "amount_column": "Total",
        "date_format": "MM/DD/YYYY"
    }
}

def get_source_config(source_slug: str) -> dict:
    """Get source configuration by slug."""
    config = SOURCE_CONFIGS.get(source_slug.lower())
    if not config:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid source '{source_slug}'. Supported sources: {', '.join(SOURCE_CONFIGS.keys())}"
        )
    return config

@router.post("/process/{source}")
@limiter.limit(settings.rate_limit_process)
async def process_data(
    source: str,
    request: Request,
    options: Optional[ProcessingOptions] = None
):
    """Process data for a specific source, automatically generating files for all years found in the data."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        processing_logger.log_processing_job(
            "api", source_enum, "started", 0.0, f"Processing started for {source_config['display_name']}"
        )
        
        # Process the data
        result = await processor.process_source(source_enum, options)
        
        if result.success:
            processing_logger.log_processing_job(
                "api", source_enum, "completed", 100.0, f"Processing completed for {source_config['display_name']}"
            )
        else:
            processing_logger.log_processing_job(
                "api", source_enum, "error", 0.0, f"Processing failed for {source_config['display_name']}: {result.error_message}"
            )
        
        return {
            **result.dict(),
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "expected_format": {
                "required_columns": source_config["required_columns"],
                "date_format": source_config["date_format"],
                "optional_columns": source_config.get("optional_columns", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_processing_job(
            "api", source, "error", 0.0, f"Processing error for {source}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{source}")
@limiter.limit(settings.rate_limit_api)
async def get_processing_status(source: str, request: Request):
    """Get processing status for a source across all years."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Get all available years
        years = await file_service.get_available_years(source_enum)
        
        # Get total summary across all years
        total_files = 0
        total_records = 0
        total_amount = 0.0
        
        for year in years:
            summary = await processor.get_processing_summary(source_enum, year)
            total_files += summary["total_files"]
            total_records += summary["total_records"]
            total_amount += summary["total_amount"]
        
        status = ProcessingStatus(
            job_id=f"{source_enum}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source=source_enum,
            status="completed" if total_files > 0 else "pending",
            progress=100.0 if total_files > 0 else 0.0,
            message=f"Processed {total_files} files with {total_records} records across {len(years)} years for {source_config['display_name']}",
            processed_files=total_files,
            total_files=total_files,
            created_at=datetime.now(),
            completed_at=datetime.now() if total_files > 0 else None
        )
        
        return {
            **status.dict(),
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "years_processed": years
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting processing status for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{source}/{year}")
@limiter.limit(settings.rate_limit_api)
async def get_processing_summary(source: str, year: int, request: Request):
    """Get processing summary for a source and year."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        summary = await processor.get_processing_summary(source_enum, year)
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "year": year,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting processing summary for {source} {year}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{source}/{year}/{month}")
@limiter.limit(settings.rate_limit_download)
async def download_processed_file(source: str, year: int, month: int, request: Request):
    """Download a processed file."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        
        file_path = settings.data_path / source_enum / "output" / str(year) / f"{month:02d}_{year}.csv"
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Processed file not found for {source_config['display_name']} {year}/{month:02d}"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=f"{source_config['display_name']}_{year}_{month:02d}.csv",
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error downloading processed file for {source} {year}/{month}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources")
@limiter.limit(settings.rate_limit_api)
async def get_available_sources(request: Request):
    """Get list of available data sources with format information."""
    try:
        sources = []
        for slug, config in SOURCE_CONFIGS.items():
            sources.append({
                "slug": slug,
                "name": config["name"],
                "display_name": config["display_name"],
                "description": config["description"],
                "format": {
                    "required_columns": config["required_columns"],
                    "date_format": config["date_format"],
                    "optional_columns": config.get("optional_columns", [])
                }
            })
        
        return {
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting available sources: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/years/{source}")
@limiter.limit(settings.rate_limit_api)
async def get_available_years(source: str, request: Request):
    """Get list of available years for a source."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        
        output_dir = settings.data_path / source_enum / "output"
        if not output_dir.exists():
            return {
                "source": source_enum,
                "source_display": source_config["display_name"],
                "years": [],
                "count": 0
            }
        
        years = []
        for year_dir in output_dir.iterdir():
            if year_dir.is_dir() and year_dir.name.isdigit():
                years.append(int(year_dir.name))
        
        years.sort()
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "years": years,
            "count": len(years)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting available years for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/months/{source}/{year}")
@limiter.limit(settings.rate_limit_api)
async def get_available_months(source: str, year: int, request: Request):
    """Get list of available months for a source and year."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        from pathlib import Path
        
        year_dir = settings.data_path / source_enum / "output" / str(year)
        if not year_dir.exists():
            return {
                "source": source_enum,
                "source_display": source_config["display_name"],
                "year": year,
                "months": [],
                "count": 0
            }
        
        months = []
        for csv_file in year_dir.glob("*.csv"):
            # Extract month from filename (e.g., "01_2023.csv" -> 1)
            try:
                month_str = csv_file.stem.split("_")[0]
                month = int(month_str)
                if 1 <= month <= 12:
                    months.append(month)
            except (ValueError, IndexError):
                continue
        
        months.sort()
        
        return {
            "source": source_enum,
            "source_display": source_config["display_name"],
            "description": source_config["description"],
            "year": year,
            "months": months,
            "count": len(months)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error getting available months for {source} {year}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time processing updates
@router.websocket("/ws/{source}/{year}")
async def processing_websocket(websocket: WebSocket, source: str, year: int):
    """WebSocket endpoint for real-time processing updates."""
    await websocket.accept()
    
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        processing_logger.log_system_event(
            f"WebSocket connection established for {source_config['display_name']} {year}"
        )
        
        # Send initial status
        summary = await processor.get_processing_summary(source_enum, year)
        progress = ProcessingProgress(
            job_id=f"{source_enum}_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source=source_enum,
            progress=100.0 if summary["total_files"] > 0 else 0.0,
            status="completed" if summary["total_files"] > 0 else "pending",
            message=f"Current status for {source_config['display_name']}: {summary['total_files']} files processed",
            processed_files=summary["total_files"],
            total_files=summary["total_files"]
        )
        
        await websocket.send_text(progress.json())
        
        # Keep connection alive and send periodic updates
        while True:
            await websocket.receive_text()  # Wait for client ping
            
            # Send updated status
            summary = await processor.get_processing_summary(source_enum, year)
            progress = ProcessingProgress(
                job_id=f"{source_enum}_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                source=source_enum,
                progress=100.0 if summary["total_files"] > 0 else 0.0,
                status="completed" if summary["total_files"] > 0 else "pending",
                message=f"Current status for {source_config['display_name']}: {summary['total_files']} files processed",
                processed_files=summary["total_files"],
                total_files=summary["total_files"]
            )
            
            await websocket.send_text(progress.json())
            
    except WebSocketDisconnect:
        processing_logger.log_system_event(
            f"WebSocket connection closed for {source} {year}"
        )
    except Exception as e:
        processing_logger.log_system_event(
            f"WebSocket error for {source} {year}: {str(e)}", level="error"
        )
        try:
            await websocket.close()
        except:
            pass 