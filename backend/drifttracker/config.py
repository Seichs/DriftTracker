"""
Configuration module for DriftTracker

Centralized configuration for object profiles, constants, and settings.
Eliminates duplicate definitions across the codebase.
"""
import os
from typing import Dict, Any

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
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Copernicus credentials (should be moved to environment variables in production)
COPERNICUS_USERNAME = os.getenv("COPERNICUS_USERNAME", "postema45@gmail.com")
COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "IkHebAids1")

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
