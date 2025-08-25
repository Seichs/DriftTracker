"""
Utility functions for the DriftTracker ocean drift prediction system
"""
import os
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Import centralized logging setup
from .common_utils import setup_logging

def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    
    if lat < -90 or lat > 90:
        return False
    
    if lon < -180 or lon > 180:
        return False
    
    return True

def validate_time_range(start_time: datetime, end_time: datetime) -> bool:
    """
    Validate time range for data queries
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        
    Returns:
        True if time range is valid, False otherwise
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        return False
    
    if start_time >= end_time:
        return False
    
    # Don't allow future times
    now = datetime.now(timezone.utc)
    if start_time > now or end_time > now:
        return False
    
    # Don't allow time ranges longer than 30 days
    if (end_time - start_time).days > 30:
        return False
    
    return True

def calculate_haversine_distance(lat1: float, lon1: float, 
                               lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula
    
    Args:
        lat1, lon1: First point coordinates in decimal degrees
        lat2, lon2: Second point coordinates in decimal degrees
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
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
    
    return R * c

def meters_to_degrees(meters: float, latitude: float) -> Tuple[float, float]:
    """
    Convert meters to degrees at a given latitude
    
    Args:
        meters: Distance in meters
        latitude: Latitude in decimal degrees
        
    Returns:
        Tuple of (degrees_latitude, degrees_longitude)
    """
    # Meters per degree of latitude (constant)
    meters_per_degree_lat = 111574.0
    
    # Meters per degree of longitude (varies with latitude)
    meters_per_degree_lon = 111320.0 * math.cos(math.radians(latitude))
    
    degrees_lat = meters / meters_per_degree_lat
    degrees_lon = meters / meters_per_degree_lon
    
    return degrees_lat, degrees_lon

def degrees_to_meters(degrees_lat: float, degrees_lon: float, 
                     latitude: float) -> Tuple[float, float]:
    """
    Convert degrees to meters at a given latitude
    
    Args:
        degrees_lat: Latitude difference in degrees
        degrees_lon: Longitude difference in degrees
        latitude: Reference latitude in decimal degrees
        
    Returns:
        Tuple of (meters_latitude, meters_longitude)
    """
    # Meters per degree of latitude (constant)
    meters_per_degree_lat = 111574.0
    
    # Meters per degree of longitude (varies with latitude)
    meters_per_degree_lon = 111320.0 * math.cos(math.radians(latitude))
    
    meters_lat = degrees_lat * meters_per_degree_lat
    meters_lon = degrees_lon * meters_per_degree_lon
    
    return meters_lat, meters_lon

def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
    """
    Format coordinates as a string
    
    Args:
        lat: Latitude
        lon: Longitude
        precision: Number of decimal places
        
    Returns:
        Formatted coordinate string
    """
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    
    return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing between two points
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalize to 0-360 degrees
    return (bearing_deg + 360) % 360

def create_bounding_box(center_lat: float, center_lon: float, 
                       radius_km: float) -> Dict[str, float]:
    """
    Create a bounding box around a center point
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Radius in kilometers
        
    Returns:
        Dictionary with min/max lat/lon
    """
    # Convert radius to degrees
    radius_deg_lat = radius_km / 111.0  # Approximate km per degree latitude
    radius_deg_lon = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    return {
        'min_lat': center_lat - radius_deg_lat,
        'max_lat': center_lat + radius_deg_lat,
        'min_lon': center_lon - radius_deg_lon,
        'max_lon': center_lon + radius_deg_lon
    }

def parse_datetime_string(dt_string: str) -> Optional[datetime]:
    """
    Parse various datetime string formats
    
    Args:
        dt_string: Datetime string to parse
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_string, fmt)
            # Add UTC timezone if not specified
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    logger.warning(f"Could not parse datetime string: {dt_string}")
    return None

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float with a default fallback
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int with a default fallback
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def ensure_directory_exists(directory_path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Absolute path to directory
    """
    abs_path = os.path.abspath(directory_path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to a human-readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def interpolate_positions(positions: List[Dict], target_hours: float) -> Optional[Dict]:
    """
    Interpolate position at a specific time from a list of positions
    
    Args:
        positions: List of position dictionaries with 'hours_elapsed', 'lat', 'lon'
        target_hours: Target time in hours
        
    Returns:
        Interpolated position dictionary or None
    """
    if not positions or len(positions) < 2:
        return None
    
    # Sort positions by hours_elapsed
    sorted_positions = sorted(positions, key=lambda x: x.get('hours_elapsed', 0))
    
    # Find the two positions to interpolate between
    for i in range(len(sorted_positions) - 1):
        pos1 = sorted_positions[i]
        pos2 = sorted_positions[i + 1]
        
        hours1 = pos1.get('hours_elapsed', 0)
        hours2 = pos2.get('hours_elapsed', 0)
        
        if hours1 <= target_hours <= hours2:
            # Linear interpolation
            if hours2 == hours1:
                return pos1
            
            factor = (target_hours - hours1) / (hours2 - hours1)
            
            interpolated_lat = pos1['lat'] + factor * (pos2['lat'] - pos1['lat'])
            interpolated_lon = pos1['lon'] + factor * (pos2['lon'] - pos1['lon'])
            
            return {
                'lat': round(interpolated_lat, 6),
                'lon': round(interpolated_lon, 6),
                'hours_elapsed': target_hours,
                'interpolated': True
            }
    
    return None

def is_position_on_land(lat: float, lon: float) -> bool:
    """
    Simple land/water check (basic implementation)
    This is a placeholder - in production you'd use a proper coastline dataset
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        True if position might be on land, False otherwise
    """
    # This is a very basic check - in reality you'd use a proper land mask
    # For now, just check if coordinates are within reasonable ocean bounds
    
    # Very basic ocean bounds (this is not accurate for all regions)
    if lat < -70 or lat > 80:  # Polar regions
        return True
    
    # Add more sophisticated land checking here in production
    return False

# Constants for common conversions
KNOTS_TO_MS = 0.514444  # Convert knots to meters per second
MS_TO_KNOTS = 1.944012  # Convert meters per second to knots
NAUTICAL_MILE_TO_KM = 1.852  # Convert nautical miles to kilometers
KM_TO_NAUTICAL_MILE = 0.539957  # Convert kilometers to nautical miles

def knots_to_ms(knots: float) -> float:
    """Convert knots to meters per second"""
    return knots * KNOTS_TO_MS

def ms_to_knots(ms: float) -> float:
    """Convert meters per second to knots"""
    return ms * MS_TO_KNOTS

def nautical_miles_to_km(nm: float) -> float:
    """Convert nautical miles to kilometers"""
    return nm * NAUTICAL_MILE_TO_KM

def km_to_nautical_miles(km: float) -> float:
    """Convert kilometers to nautical miles"""
    return km * KM_TO_NAUTICAL_MILE
