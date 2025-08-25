"""
Common utilities for DriftTracker

Centralized utility functions to eliminate code duplication across modules.
"""
import math
import logging
from typing import Tuple, Optional
import xarray as xr
from datetime import datetime

from .config import EARTH_RADIUS_KM

logger = logging.getLogger(__name__)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: First coordinate pair
        lat2, lon2: Second coordinate pair
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c

def get_currents_at_position(ds: xr.Dataset, lat: float, lon: float, 
                            time: Optional[datetime] = None) -> Tuple[float, float]:
    """
    Extract current velocities at a specific position and time
    
    Args:
        ds: xarray Dataset containing ocean current data
        lat: Latitude
        lon: Longitude
        time: Time (if None, uses first available time)
        
    Returns:
        Tuple of (u_current, v_current) in m/s
    """
    try:
        # Check if coordinates are within reasonable bounds
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            logger.warning(f"Coordinates ({lat}, {lon}) outside valid bounds")
            return 0.0, 0.0
        
        # Check if coordinates are within dataset bounds
        if 'latitude' in ds.dims and 'longitude' in ds.dims:
            lat_bounds = (float(ds.latitude.min()), float(ds.latitude.max()))
            lon_bounds = (float(ds.longitude.min()), float(ds.longitude.max()))
            
            if not (lat_bounds[0] <= lat <= lat_bounds[1]) or not (lon_bounds[0] <= lon <= lon_bounds[1]):
                logger.warning(f"Coordinates ({lat}, {lon}) outside dataset bounds {lat_bounds}, {lon_bounds}")
                return 0.0, 0.0
        
        if time is not None and 'time' in ds.dims:
            # Find nearest time
            u_current = float(ds.uo.sel(
                time=time,
                latitude=lat,
                longitude=lon,
                method="nearest"
            ).values)
            
            v_current = float(ds.vo.sel(
                time=time,
                latitude=lat,
                longitude=lon,
                method="nearest"
            ).values)
        else:
            # Use first available time
            u_current = float(ds.uo.isel(time=0).sel(
                latitude=lat,
                longitude=lon,
                method="nearest"
            ).values)
            
            v_current = float(ds.vo.isel(time=0).sel(
                latitude=lat,
                longitude=lon,
                method="nearest"
            ).values)
        
        return u_current, v_current
        
    except Exception as e:
        logger.warning(f"Error getting currents at position ({lat}, {lon}): {e}")
        # Return reasonable defaults
        return 0.0, 0.0

def setup_logging(level: str = "INFO", log_file: str = "drifttracker.log") -> None:
    """
    Set up logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
