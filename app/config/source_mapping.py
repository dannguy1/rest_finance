"""
Source mapping configuration for flexible column mapping.
Allows users to configure how source-specific columns map to normalized processed data.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.config.settings import settings


class MappingType(str, Enum):
    """Types of column mappings."""
    DATE = "date"
    DESCRIPTION = "description"
    AMOUNT = "amount"
    OPTIONAL = "optional"


class ColumnMapping(BaseModel):
    """Configuration for mapping a source column to processed data."""
    source_column: str = Field(..., description="Column name in source file")
    target_field: str = Field(..., description="Target field in processed data")
    mapping_type: MappingType = Field(..., description="Type of mapping")
    required: bool = Field(default=True, description="Whether this column is required")
    date_format: Optional[str] = Field(default=None, description="Date format if mapping type is date")
    amount_format: Optional[str] = Field(default=None, description="Amount format if mapping type is amount")
    description: Optional[str] = Field(default=None, description="Human-readable description of this column")


class SourceMappingConfig(BaseModel):
    """Complete mapping configuration for a data source."""
    source_id: str = Field(..., description="Unique identifier for the source")
    display_name: str = Field(..., description="Human-readable name for the source")
    description: str = Field(..., description="Description of the source")
    icon: str = Field(default="file", description="Icon for the source")
    
    # Column mappings
    date_mapping: ColumnMapping = Field(..., description="Mapping for date column")
    description_mapping: ColumnMapping = Field(..., description="Mapping for description column")
    amount_mapping: ColumnMapping = Field(..., description="Mapping for amount column")
    optional_mappings: List[ColumnMapping] = Field(default=[], description="Optional column mappings")
    
    # Validation settings
    expected_columns: List[str] = Field(..., description="All expected columns in source files")
    required_columns: List[str] = Field(..., description="Required columns for validation")
    
    # Processing settings
    default_date_format: str = Field(default="MM/DD/YYYY", description="Default date format")
    default_amount_format: str = Field(default="USD", description="Default amount format")
    
    # Example data for UI
    example_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="Example data rows")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Default source configurations with flexible mapping
DEFAULT_SOURCE_MAPPINGS = {
    "bankofamerica": SourceMappingConfig(
        source_id="bankofamerica",
        display_name="Bank of America",
        description="Bank statement processing and management",
        icon="bank",
        date_mapping=ColumnMapping(
            source_column="Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Transaction date"
        ),
        description_mapping=ColumnMapping(
            source_column="Original Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Transaction description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Amount",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Transaction amount"
        ),
        optional_mappings=[
            ColumnMapping(
                source_column="Status",
                target_field="status",
                mapping_type=MappingType.OPTIONAL,
                required=False,
                description="Transaction status"
            )
        ],
        expected_columns=["Status", "Date", "Original Description", "Amount"],
        required_columns=["Date", "Original Description", "Amount"],
        example_data=[
            {"Status": "Posted", "Date": "01/15/2024", "Original Description": "VERIZON WIRELESS", "Amount": "-421.50"},
            {"Status": "Posted", "Date": "01/20/2024", "Original Description": "GROCERY STORE", "Amount": "-45.67"}
        ]
    ),
    
    "chase": SourceMappingConfig(
        source_id="chase",
        display_name="Chase",
        description="Chase bank statement processing and management",
        icon="credit-card",
        date_mapping=ColumnMapping(
            source_column="Posting Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Transaction posting date"
        ),
        description_mapping=ColumnMapping(
            source_column="Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Transaction description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Amount",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Transaction amount"
        ),
        optional_mappings=[
            ColumnMapping(
                source_column="Details",
                target_field="details",
                mapping_type=MappingType.OPTIONAL,
                required=False,
                description="Additional transaction details"
            ),
            ColumnMapping(
                source_column="Type",
                target_field="type",
                mapping_type=MappingType.OPTIONAL,
                required=False,
                description="Transaction type"
            ),
            ColumnMapping(
                source_column="Balance",
                target_field="balance",
                mapping_type=MappingType.OPTIONAL,
                required=False,
                description="Account balance"
            ),
            ColumnMapping(
                source_column="Check or Slip #",
                target_field="check_number",
                mapping_type=MappingType.OPTIONAL,
                required=False,
                description="Check or slip number"
            )
        ],
        expected_columns=["Posting Date", "Description", "Amount", "Details", "Type", "Balance", "Check or Slip #"],
        required_columns=["Posting Date", "Description", "Amount"],
        example_data=[
            {"Posting Date": "01/15/2024", "Description": "VERIZON WIRELESS", "Amount": "-421.50", "Type": "DEBIT"},
            {"Posting Date": "01/20/2024", "Description": "GROCERY STORE", "Amount": "-45.67", "Type": "DEBIT"}
        ]
    ),
    
    "restaurantdepot": SourceMappingConfig(
        source_id="restaurantdepot",
        display_name="Restaurant Depot",
        description="Restaurant Depot supplier receipt processing and management",
        icon="shop",
        date_mapping=ColumnMapping(
            source_column="Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Invoice date"
        ),
        description_mapping=ColumnMapping(
            source_column="Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Item description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Total",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Item total"
        ),
        optional_mappings=[],
        expected_columns=["Date", "Description", "Total"],
        required_columns=["Date", "Description", "Total"],
        example_data=[
            {"Date": "01/15/2024", "Description": "CHICKEN BREAST", "Total": "125.50"},
            {"Date": "01/20/2024", "Description": "VEGETABLES", "Total": "45.67"}
        ]
    ),
    
    "sysco": SourceMappingConfig(
        source_id="sysco",
        display_name="Sysco",
        description="Sysco supplier receipt processing and management",
        icon="truck",
        date_mapping=ColumnMapping(
            source_column="Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Invoice date"
        ),
        description_mapping=ColumnMapping(
            source_column="Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Item description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Total",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Item total"
        ),
        optional_mappings=[],
        expected_columns=["Date", "Description", "Total"],
        required_columns=["Date", "Description", "Total"],
        example_data=[
            {"Date": "01/15/2024", "Description": "MEAT PRODUCTS", "Total": "225.50"},
            {"Date": "01/20/2024", "Description": "DAIRY PRODUCTS", "Total": "85.67"}
        ]
    ),
    
    "gg": SourceMappingConfig(
        source_id="gg",
        display_name="GG",
        description="GG merchant statement processing and management",
        icon="credit-card",
        date_mapping=ColumnMapping(
            source_column="Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Transaction date"
        ),
        description_mapping=ColumnMapping(
            source_column="Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Transaction description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Amount",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Transaction amount"
        ),
        optional_mappings=[],
        expected_columns=["Date", "Description", "Amount"],
        required_columns=["Date", "Description", "Amount"],
        example_data=[
            {"Date": "01/15/2024", "Description": "MERCHANT TRANSACTION", "Amount": "125.50"},
            {"Date": "01/20/2024", "Description": "PAYMENT PROCESSING", "Amount": "45.67"}
        ]
    ),
    
    "ar": SourceMappingConfig(
        source_id="ar",
        display_name="AR",
        description="AR merchant statement processing and management",
        icon="credit-card",
        date_mapping=ColumnMapping(
            source_column="Date",
            target_field="date",
            mapping_type=MappingType.DATE,
            required=True,
            date_format="MM/DD/YYYY",
            description="Transaction date"
        ),
        description_mapping=ColumnMapping(
            source_column="Description",
            target_field="description",
            mapping_type=MappingType.DESCRIPTION,
            required=True,
            description="Transaction description"
        ),
        amount_mapping=ColumnMapping(
            source_column="Amount",
            target_field="amount",
            mapping_type=MappingType.AMOUNT,
            required=True,
            amount_format="USD",
            description="Transaction amount"
        ),
        optional_mappings=[],
        expected_columns=["Date", "Description", "Amount"],
        required_columns=["Date", "Description", "Amount"],
        example_data=[
            {"Date": "01/15/2024", "Description": "MERCHANT TRANSACTION", "Amount": "125.50"},
            {"Date": "01/20/2024", "Description": "PAYMENT PROCESSING", "Amount": "45.67"}
        ]
    )
}


class SourceMappingManager:
    """Manager for source mapping configurations."""
    
    def __init__(self):
        # Use settings to get the config directory path
        self.config_dir = settings.config_path
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, SourceMappingConfig]:
        """Load mappings from JSON files in config directory."""
        mappings = DEFAULT_SOURCE_MAPPINGS.copy()
        
        if not self.config_dir.exists():
            print(f"Warning: Config directory {self.config_dir} does not exist")
            return mappings
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                source_id = config_file.stem
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    mapping = SourceMappingConfig(**data)
                    mappings[source_id.lower()] = mapping
                    print(f"Loaded mapping for {source_id} from {config_file}")
            except Exception as e:
                print(f"Warning: Failed to load mapping from {config_file}: {e}")
        
        return mappings
    
    def _save_mapping(self, mapping: SourceMappingConfig) -> None:
        """Save a mapping to its JSON file."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = self.config_dir / f"{mapping.source_id}.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(mapping.dict(), f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save mapping to {config_file}: {e}")
    
    def _delete_mapping_file(self, source_id: str) -> None:
        """Delete a mapping JSON file."""
        config_file = self.config_dir / f"{source_id}.json"
        if config_file.exists():
            try:
                config_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete mapping file {config_file}: {e}")
    
    def get_mapping(self, source_id: str) -> Optional[SourceMappingConfig]:
        """Get mapping configuration for a source."""
        return self.mappings.get(source_id.lower())
    
    def get_all_mappings(self) -> Dict[str, SourceMappingConfig]:
        """Get all mapping configurations."""
        return self.mappings.copy()
    
    def add_mapping(self, mapping: SourceMappingConfig) -> None:
        """Add or update a mapping configuration."""
        self.mappings[mapping.source_id.lower()] = mapping
        self._save_mapping(mapping)
    
    def remove_mapping(self, source_id: str) -> bool:
        """Remove a mapping configuration."""
        source_id_lower = source_id.lower()
        if source_id_lower in self.mappings:
            del self.mappings[source_id_lower]
            self._delete_mapping_file(source_id)
            return True
        return False
    
    def validate_mapping(self, mapping: SourceMappingConfig) -> List[str]:
        """Validate a mapping configuration and return list of errors."""
        errors = []
        
        # Check required mappings
        if not mapping.date_mapping:
            errors.append("Date mapping is required")
        if not mapping.description_mapping:
            errors.append("Description mapping is required")
        if not mapping.amount_mapping:
            errors.append("Amount mapping is required")
        
        # Check for duplicate source columns
        source_columns = [mapping.date_mapping.source_column, 
                         mapping.description_mapping.source_column,
                         mapping.amount_mapping.source_column]
        source_columns.extend([opt.source_column for opt in mapping.optional_mappings])
        
        if len(source_columns) != len(set(source_columns)):
            errors.append("Duplicate source columns found")
        
        # Check that expected columns include all mapped columns
        mapped_columns = set(source_columns)
        expected_columns = set(mapping.expected_columns)
        
        if not mapped_columns.issubset(expected_columns):
            missing = mapped_columns - expected_columns
            errors.append(f"Expected columns missing mapped columns: {missing}")
        
        return errors
    
    def get_mapping_summary(self, source_id: str) -> Dict[str, Any]:
        """Get a summary of mapping configuration for API responses."""
        mapping = self.get_mapping(source_id)
        if not mapping:
            return None
        
        return {
            "source_id": mapping.source_id,
            "display_name": mapping.display_name,
            "description": mapping.description,
            "icon": mapping.icon,
            "required_columns": mapping.required_columns,
            "optional_columns": [opt.source_column for opt in mapping.optional_mappings],
            "date_format": mapping.default_date_format,
            "amount_format": mapping.default_amount_format,
            "example_data": mapping.example_data
        }


# Global mapping manager instance
mapping_manager = SourceMappingManager() 