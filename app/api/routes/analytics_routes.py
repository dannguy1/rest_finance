"""
Analytics routes for Financial Data Processor.
Provides analytical views and data analysis endpoints.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from slowapi import Limiter
from slowapi.util import get_remote_address
import pandas as pd
import numpy as np
from pathlib import Path

from app.config import settings
from app.utils.logging import processing_logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Source configurations
SOURCE_CONFIGS = {
    "bankofamerica": {
        "name": "BankOfAmerica",
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
        "name": "RestaurantDepot",
        "icon": "shop",
        "description": "Restaurant Depot supplier receipt processing and management"
    }
}


def get_source_config(source_slug: str) -> dict:
    """Get source configuration by slug."""
    if source_slug not in SOURCE_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Source '{source_slug}' not found")
    return SOURCE_CONFIGS[source_slug]


@router.get("/{source}/group-by-description")
@limiter.limit(settings.rate_limit_api)
async def analytics_group_by_description(
    source: str,
    request: Request,
    fileType: str = Query(..., description="Type of file (processed or uploaded)"),
    filePath: str = Query(..., description="Path to the file")
):
    """Group data by description and provide summary statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Group by description
        description_groups = df.groupby('Description').agg({
            'Amount': ['count', 'sum', 'mean', 'min', 'max']
        }).round(2)
        
        # Flatten column names
        description_groups.columns = ['count', 'total_amount', 'average_amount', 'min_amount', 'max_amount']
        description_groups = description_groups.reset_index()
        
        # Convert to list of dictionaries
        groups = []
        for _, row in description_groups.iterrows():
            groups.append({
                'description': row['Description'],
                'count': int(row['count']),
                'total_amount': float(row['total_amount']),
                'average_amount': float(row['average_amount']),
                'min_amount': float(row['min_amount']),
                'max_amount': float(row['max_amount'])
            })
        
        # Sort by total amount descending
        groups.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "groups": groups,
            "total_groups": len(groups)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in group by description analytics for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}/monthly-summary")
@limiter.limit(settings.rate_limit_api)
async def analytics_monthly_summary(
    source: str,
    request: Request,
    fileType: str = Query(..., description="Type of file (processed or uploaded)"),
    filePath: str = Query(..., description="Path to the file")
):
    """Provide monthly summary statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Convert date column to datetime
        date_column = get_date_column(source_enum)
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Group by month
        df['month'] = df[date_column].dt.to_period('M')
        monthly_data = df.groupby('month').agg({
            'Amount': ['sum', 'count']
        }).round(2)
        
        monthly_data.columns = ['amount', 'count']
        monthly_data = monthly_data.reset_index()
        
        # Convert to list of dictionaries with proper type conversion
        monthly_summary = []
        for _, row in monthly_data.iterrows():
            monthly_summary.append({
                'month': str(row['month']),
                'amount': float(row['amount']),
                'count': int(row['count'])
            })
        
        # Calculate summary statistics with proper type conversion
        total_transactions = int(df['Amount'].count())
        total_amount = float(df['Amount'].sum())
        average_per_month = float(total_amount / len(monthly_summary)) if monthly_summary else 0.0
        
        # Find highest and lowest months
        if monthly_summary:
            highest_month = max(monthly_summary, key=lambda x: x['amount'])
            lowest_month = min(monthly_summary, key=lambda x: x['amount'])
        else:
            highest_month = lowest_month = None
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "monthly_data": monthly_summary,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "average_per_month": average_per_month,
            "highest_month": str(highest_month['month']) if highest_month else None,
            "lowest_month": str(lowest_month['month']) if lowest_month else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in monthly summary analytics for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}/amount-analysis")
@limiter.limit(settings.rate_limit_api)
async def analytics_amount_analysis(
    source: str,
    request: Request,
    fileType: str = Query(..., description="Type of file (processed or uploaded)"),
    filePath: str = Query(..., description="Path to the file")
):
    """Provide amount analysis including distribution and statistics."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Calculate basic statistics
        amounts = df['Amount']
        mean = amounts.mean()
        median = amounts.median()
        std_dev = amounts.std()
        min_amount = amounts.min()
        max_amount = amounts.max()
        count = len(amounts)
        
        # Create amount distribution (bins)
        bins = pd.cut(amounts, bins=10)
        distribution = bins.value_counts().sort_index()
        
        distribution_data = []
        for bin_name, count in distribution.items():
            distribution_data.append({
                'range': str(bin_name),
                'count': int(count)
            })
        
        # Create amount ranges for pie chart
        ranges = [
            {'range': 'Very Low (< $10)', 'count': int(len(amounts[amounts < 10]))},
            {'range': 'Low ($10 - $50)', 'count': int(len(amounts[(amounts >= 10) & (amounts < 50)]))},
            {'range': 'Medium ($50 - $200)', 'count': int(len(amounts[(amounts >= 50) & (amounts < 200)]))},
            {'range': 'High ($200 - $1000)', 'count': int(len(amounts[(amounts >= 200) & (amounts < 1000)]))},
            {'range': 'Very High (> $1000)', 'count': int(len(amounts[amounts >= 1000]))}
        ]
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "mean": float(mean),
            "median": float(median),
            "std_dev": float(std_dev),
            "min": float(min_amount),
            "max": float(max_amount),
            "count": count,
            "distribution": distribution_data,
            "ranges": ranges
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in amount analysis for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}/trends")
@limiter.limit(settings.rate_limit_api)
async def analytics_trends(
    source: str,
    request: Request,
    fileType: str = Query(..., description="Type of file (processed or uploaded)"),
    filePath: str = Query(..., description="Path to the file")
):
    """Provide trend analysis over time."""
    try:
        source_config = get_source_config(source)
        source_enum = source_config["name"]
        
        # Load the file data
        df = await load_file_data(source_enum, fileType, filePath)
        
        # Convert date column to datetime
        date_column = get_date_column(source_enum)
        df[date_column] = pd.to_datetime(df[date_column])
        
        # Group by month and calculate trends
        df['month'] = df[date_column].dt.to_period('M')
        monthly_trends = df.groupby('month')['Amount'].sum().reset_index()
        
        # Convert to list of dictionaries with proper type conversion
        trend_data = []
        for _, row in monthly_trends.iterrows():
            trend_data.append({
                'month': str(row['month']),
                'amount': float(row['Amount'])
            })
        
        # Calculate trend direction and growth rate
        if len(trend_data) >= 2:
            first_amount = float(trend_data[0]['amount'])
            last_amount = float(trend_data[-1]['amount'])
            
            if first_amount != 0:
                growth_rate = float(((last_amount - first_amount) / abs(first_amount)) * 100)
            else:
                growth_rate = 0.0
                
            trend_direction = "Increasing" if growth_rate > 0 else "Decreasing" if growth_rate < 0 else "Stable"
        else:
            growth_rate = 0.0
            trend_direction = "Insufficient Data"
        
        # Find peak and lowest months
        if trend_data:
            peak_month = max(trend_data, key=lambda x: x['amount'])
            lowest_month = min(trend_data, key=lambda x: x['amount'])
        else:
            peak_month = lowest_month = None
        
        return {
            "source": source_enum,
            "file_type": fileType,
            "file_path": filePath,
            "trend_data": trend_data,
            "trend_direction": trend_direction,
            "growth_rate": round(growth_rate, 2),
            "peak_month": str(peak_month['month']) if peak_month else None,
            "lowest_month": str(lowest_month['month']) if lowest_month else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_logger.log_system_event(
            f"Error in trends analysis for {source}: {str(e)}", level="error"
        )
        raise HTTPException(status_code=500, detail=str(e))


async def load_file_data(source_enum: str, file_type: str, file_path: str):
    """Load file data for analytics."""
    from pathlib import Path
    import pandas as pd

    # Debug logging
    processing_logger.log_system_event(
        f"load_file_data called with source_enum={source_enum}, file_type={file_type}, file_path={file_path}",
        level="info"
    )

    # Map source enum to directory name
    source_to_dir = {
        "BankOfAmerica": "bankofamerica",
        "Chase": "chase", 
        "RestaurantDepot": "restaurantdepot",
        "Sysco": "sysco"
    }
    
    source_dir = source_to_dir.get(source_enum, source_enum.lower())

    # Normalize file_path: remove redundant prefix if present
    # e.g. file_path = 'bankofamerica/output/2022/01_2022.csv' but we want just '2022/01_2022.csv'
    prefixes = [
        f"{source_dir}/output/",
        f"{source_dir}/input/",
        f"{source_enum}/output/",
        f"{source_enum}/input/"
    ]
    
    original_file_path = file_path
    for prefix in prefixes:
        if file_path.startswith(prefix):
            file_path = file_path[len(prefix):]
            processing_logger.log_system_event(
                f"Stripped prefix '{prefix}' from file_path: '{original_file_path}' -> '{file_path}'",
                level="info"
            )
            break

    if file_type == "uploaded":
        file_path_obj = settings.data_path / source_dir / "input" / file_path
    else:  # processed
        file_path_obj = settings.data_path / source_dir / "output" / file_path

    processing_logger.log_system_event(
        f"Looking for file at: {file_path_obj}",
        level="info"
    )

    if not file_path_obj.exists():
        # Check if the directory exists
        parent_dir = file_path_obj.parent
        if parent_dir.exists():
            processing_logger.log_system_event(
                f"Directory exists but file not found. Available files: {list(parent_dir.glob('*'))}",
                level="info"
            )
        else:
            processing_logger.log_system_event(
                f"Directory does not exist: {parent_dir}",
                level="info"
            )
        raise HTTPException(status_code=404, detail=f"File not found: {file_path_obj}")

    # Load CSV data
    df = pd.read_csv(file_path_obj)

    # Normalize column names for analytics
    df.columns = df.columns.str.strip()

    # Ensure Amount column exists and is numeric
    amount_column = get_amount_column(source_enum)
    if amount_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Amount column '{amount_column}' not found")

    # Convert amount to numeric, handling currency symbols and commas
    df[amount_column] = pd.to_numeric(df[amount_column].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')

    # Remove rows with NaN amounts
    df = df.dropna(subset=[amount_column])

    # Rename columns for consistency
    df = df.rename(columns={
        amount_column: 'Amount',
        get_description_column(source_enum): 'Description'
    })

    return df


def get_date_column(source_enum: str) -> str:
    """Get the date column name for a source."""
    date_columns = {
        "BankOfAmerica": "Date",
        "Chase": "Posting Date",
        "RestaurantDepot": "Date",
        "Sysco": "Date"
    }
    return date_columns.get(source_enum, "Date")


def get_amount_column(source_enum: str) -> str:
    """Get the amount column name for a source."""
    amount_columns = {
        "BankOfAmerica": "Amount",
        "Chase": "Amount",
        "RestaurantDepot": "Total",
        "Sysco": "Total"
    }
    return amount_columns.get(source_enum, "Amount")


def get_description_column(source_enum: str) -> str:
    """Get the description column name for a source."""
    description_columns = {
        "BankOfAmerica": "Original Description",
        "Chase": "Description",
        "RestaurantDepot": "Description",
        "Sysco": "Description"
    }
    return description_columns.get(source_enum, "Description") 