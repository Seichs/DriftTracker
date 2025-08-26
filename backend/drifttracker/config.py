"""
Configuration module for DriftTracker

Centralized configuration for object profiles, constants, and settings.
Eliminates duplicate definitions across the codebase.
"""
import os
from typing import Dict, Any
from pathlib import Path

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# Find the .env file relative to this config file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    raise FileNotFoundError(f"No .env file found at: {env_path}")

# Object profiles with drag factors and properties
OBJECT_PROFILES = {
    "Person_Adult_LifeJacket": {
        "drag_factor": 0.8,
        "current_factor": 1.0,
        "wind_factor": 0.01,
        "survival_hours": 24
    },
    "Person_Adult_NoLifeJacket": {
        "drag_factor": 1.1,
        "current_factor": 1.0,
        "wind_factor": 0.005,
        "survival_hours": 6
    },
    "Person_Adolescent_LifeJacket": {
        "drag_factor": 0.9,
        "current_factor": 1.0,
        "wind_factor": 0.01,
        "survival_hours": 24
    },
    "Person_Child_LifeJacket": {
        "drag_factor": 1.0,
        "current_factor": 1.0,
        "wind_factor": 0.015,
        "survival_hours": 12
    },
    "Catamaran": {
        "drag_factor": 0.4,
        "current_factor": 1.0,
        "wind_factor": 0.05,
        "survival_hours": 72
    },
    "Hobby_Cat": {
        "drag_factor": 0.5,
        "current_factor": 1.0,
        "wind_factor": 0.05,
        "survival_hours": 72
    },
    "Fishing_Trawler": {
        "drag_factor": 0.2,
        "current_factor": 1.0,
        "wind_factor": 0.03,
        "survival_hours": 120
    },
    "RHIB": {
        "drag_factor": 0.6,
        "current_factor": 1.0,
        "wind_factor": 0.02,
        "survival_hours": 48
    },
    "SUP_Board": {
        "drag_factor": 1.2,
        "current_factor": 1.0,
        "wind_factor": 0.06,
        "survival_hours": 12
    },
    "Windsurfer": {
        "drag_factor": 1.3,
        "current_factor": 1.0,
        "wind_factor": 0.06,
        "survival_hours": 12
    },
    "Kayak": {
        "drag_factor": 1.1,
        "current_factor": 1.0,
        "wind_factor": 0.01,
        "survival_hours": 24
    }
}

# Physical constants
EARTH_RADIUS_KM = 6371.0
LON_KM_PER_DEGREE_AT_EQUATOR = 111.32
LAT_KM_PER_DEGREE = 110.574
METERS_PER_DEGREE_LAT = 111574.0
METERS_PER_DEGREE_LON_AT_EQUATOR = 111320.0

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Copernicus credentials - MUST be set via environment variables
COPERNICUS_USERNAME = os.environ.get("COPERNICUS_USERNAME")
COPERNICUS_PASSWORD = os.environ.get("COPERNICUS_PASSWORD")

# Validate credentials are set
if not COPERNICUS_USERNAME or not COPERNICUS_PASSWORD:
    raise ValueError(
        "Copernicus credentials not set! Please set COPERNICUS_USERNAME and COPERNICUS_PASSWORD "
        "environment variables. Get them from: https://marine.copernicus.eu/user"
    )

# Copernicus API Configuration
COPERNICUS_CONFIG = {
    "dataset_id": "cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",  # Hourly global ocean physics
    "variables": ["uo", "vo"],  # Eastward and Northward velocity
    "spatial_resolution": 0.083,  # degrees
    "temporal_resolution": "1H",  # hourly
    "max_retries": int(os.getenv("COPERNICUS_MAX_RETRIES", "3")),
    "timeout": int(os.getenv("COPERNICUS_TIMEOUT", "300")),  # seconds
    "cache_duration_hours": int(os.getenv("COPERNICUS_CACHE_HOURS", "24"))
}

# Data caching configuration
DATA_CACHE_CONFIG = {
    "cache_dir": os.getenv("DATA_CACHE_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")),
    "max_cache_size_gb": float(os.getenv("MAX_CACHE_SIZE_GB", "10")),
    "cleanup_interval_hours": int(os.getenv("CLEANUP_INTERVAL_HOURS", "6"))
}

def get_object_properties(object_type: str) -> Dict[str, Any]:
    """
    Get drift properties for different object types
    
    Args:
        object_type: Type of drifting object
        
    Returns:
        Dictionary with drift properties including drag_factor, current_factor, 
        wind_factor, and survival_hours
    """
    return OBJECT_PROFILES.get(object_type, {
        "drag_factor": 1.0,
        "current_factor": 1.0,
        "wind_factor": 0.0,
        "survival_hours": 24
    })

def get_drag_factor(object_type: str) -> float:
    """
    Get drag factor for a specific object type
    
    Args:
        object_type: Type of drifting object
        
    Returns:
        Drag factor value
    """
    return OBJECT_PROFILES.get(object_type, {}).get("drag_factor", 1.0)
