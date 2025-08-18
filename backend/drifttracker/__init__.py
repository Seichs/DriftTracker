"""
DriftTracker package for ocean drift prediction
"""

from .drift_calculator import DriftCalculator
from .data_service import get_ocean_data_file, download_ocean_data
from .utils import (
    validate_coordinates,
    calculate_haversine_distance,
    format_coordinates,
    setup_logging
)

__version__ = "1.0.0"
__all__ = [
    "DriftCalculator",
    "get_ocean_data_file", 
    "download_ocean_data",
    "validate_coordinates",
    "calculate_haversine_distance",
    "format_coordinates",
    "setup_logging"
]
