"""
Pydantic models for file upload and processing operations.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class SourceType(str, Enum):
    """Supported data source types."""
    BANK_OF_AMERICA = "BankOfAmerica"
    CHASE = "Chase"
    RESTAURANT_DEPOT = "RestaurantDepot"
    SYSO = "Sysco"


class ProcessingOptions(BaseModel):
    """Options for data processing."""
    date_format: Optional[str] = Field(default="MM/DD/YYYY", description="Date format for parsing")
    currency_format: Optional[str] = Field(default="USD", description="Currency format")
    include_source_file: bool = Field(default=True, description="Include source file in output")


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    source: SourceType = Field(..., description="Data source type")
    files: List[str] = Field(..., description="List of file paths")
    processing_options: Optional[ProcessingOptions] = Field(default=None, description="Processing options")


class ProcessingResult(BaseModel):
    """Result of processing operation."""
    success: bool = Field(..., description="Whether processing was successful")
    files_processed: int = Field(..., description="Number of files processed")
    output_files: List[str] = Field(default_factory=list, description="List of output files generated")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")


class ProcessingStatus(BaseModel):
    """Status of a processing job."""
    job_id: str = Field(..., description="Unique job identifier")
    source: str = Field(..., description="Data source")
    status: str = Field(..., description="Job status: pending, processing, completed, error")
    progress: float = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Status message")
    processed_files: int = Field(..., description="Number of files processed")
    total_files: int = Field(..., description="Total number of files")
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion timestamp")


class TransactionRecord(BaseModel):
    """Individual transaction record."""
    date: str = Field(..., description="Transaction date")
    description: str = Field(..., description="Transaction description")
    amount: float = Field(..., description="Transaction amount")
    source_file: str = Field(..., description="Source file name")


class MonthlyData(BaseModel):
    """Monthly aggregated data."""
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
    transactions: List[TransactionRecord] = Field(default_factory=list, description="List of transactions")
    total_amount: float = Field(..., description="Total amount for the month")
    record_count: int = Field(..., description="Number of records")


class ProcessingProgress(BaseModel):
    """WebSocket processing progress update."""
    job_id: str = Field(..., description="Job identifier")
    source: str = Field(..., description="Data source")
    progress: float = Field(..., description="Progress percentage")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    processed_files: int = Field(..., description="Files processed")
    total_files: int = Field(..., description="Total files")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")


class DetailedHealthCheck(BaseModel):
    """Detailed health check response."""
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    system: Dict[str, Any] = Field(..., description="System metrics")
    database: Dict[str, Any] = Field(..., description="Database status")
    services: Dict[str, str] = Field(..., description="Service status") 