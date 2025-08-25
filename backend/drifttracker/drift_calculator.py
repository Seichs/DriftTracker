"""
Drift calculation module for ocean drift prediction
"""
import numpy as np
import xarray as xr
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
import logging
import math

from .config import EARTH_RADIUS_KM, METERS_PER_DEGREE_LAT, METERS_PER_DEGREE_LON_AT_EQUATOR
from .common_utils import calculate_distance, get_currents_at_position

# Configure logging
logger = logging.getLogger(__name__)

class DriftCalculator:
    """Calculate drift trajectories for objects in ocean currents"""
    
    def __init__(self):
        self.earth_radius_km = EARTH_RADIUS_KM
        self.meters_per_degree_lat = METERS_PER_DEGREE_LAT
        self.meters_per_degree_lon_at_equator = METERS_PER_DEGREE_LON_AT_EQUATOR
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair
            
        Returns:
            Distance in kilometers
        """
        return calculate_distance(lat1, lon1, lat2, lon2)
    
    def get_object_properties(self, object_type: str) -> Dict[str, float]:
        """
        Get drift properties for different object types
        
        Args:
            object_type: Type of drifting object
            
        Returns:
            Dictionary with drift properties
        """
        from .config import get_object_properties as get_props
        return get_props(object_type)
    
    def get_currents_at_position(self, ds: xr.Dataset, lat: float, lon: float, 
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
        return get_currents_at_position(ds, lat, lon, time)
    
    def calculate_drift_trajectory(self, initial_lat: float, initial_lon: float,
                                 drift_hours: float, object_type: str,
                                 ocean_data: xr.Dataset,
                                 start_time: Optional[datetime] = None,
                                 time_step_minutes: int = 15) -> List[Dict[str, float]]:
        """
        Calculate drift trajectory with intermediate points
        
        Args:
            initial_lat: Starting latitude
            initial_lon: Starting longitude
            drift_hours: Total hours to drift
            object_type: Type of drifting object
            ocean_data: xarray Dataset with ocean current data
            start_time: Start time for drift calculation
            time_step_minutes: Time step in minutes for calculation
            
        Returns:
            List of position dictionaries with lat, lon, hours_elapsed, timestamp
        """
        try:
            # Initialize position and trajectory
            current_lat = initial_lat
            current_lon = initial_lon
            trajectory = []
            
            # Get object properties
            props = self.get_object_properties(object_type)
            
            # Add initial position
            if start_time:
                timestamp = start_time.isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()
            
            trajectory.append({
                "lat": round(current_lat, 6),
                "lon": round(current_lon, 6),
                "hours_elapsed": 0.0,
                "timestamp": timestamp
            })
            
            # Calculate number of time steps
            time_step_hours = time_step_minutes / 60.0
            num_steps = int(drift_hours / time_step_hours)
            
            for step in range(1, num_steps + 1):
                # Calculate current time for this step
                hours_elapsed = step * time_step_hours
                if start_time:
                    current_time = start_time + timedelta(hours=hours_elapsed)
                else:
                    current_time = None
                
                # Get ocean currents at current position and time
                u_current, v_current = self.get_currents_at_position(
                    ocean_data, current_lat, current_lon, current_time
                )
                
                # Apply object-specific modifications
                u_effective = u_current * props["current_factor"] * props["drag_factor"]
                v_effective = v_current * props["current_factor"] * props["drag_factor"]
                
                # Calculate movement for this time step
                dt_seconds = time_step_minutes * 60
                dx_meters = u_effective * dt_seconds
                dy_meters = v_effective * dt_seconds
                
                # Convert to degrees
                lat_change = dy_meters / self.meters_per_degree_lat
                lon_change = dx_meters / (self.meters_per_degree_lon_at_equator * 
                                        math.cos(math.radians(current_lat)))
                
                # Update position
                current_lat += lat_change
                current_lon += lon_change
                
                # Add position to trajectory (store every hour or every few steps)
                if step % max(1, int(60 / time_step_minutes)) == 0 or step == num_steps:
                    if current_time:
                        timestamp = current_time.isoformat()
                    else:
                        timestamp = datetime.now(timezone.utc).isoformat()
                    
                    trajectory.append({
                        "lat": round(current_lat, 6),
                        "lon": round(current_lon, 6),
                        "hours_elapsed": round(hours_elapsed, 2),
                        "timestamp": timestamp
                    })
            
            return trajectory
            
        except Exception as e:
            logger.error(f"Error calculating drift trajectory: {e}")
            # Return fallback trajectory
            return self._fallback_trajectory(initial_lat, initial_lon, drift_hours, object_type)
    
    def _fallback_trajectory(self, lat: float, lon: float, hours: float, 
                           object_type: str) -> List[Dict[str, float]]:
        """
        Simple fallback trajectory calculation if detailed calculation fails
        """
        props = self.get_object_properties(object_type)
        
        # Simple linear drift estimation
        drift_lat_per_hour = 0.01 * props["current_factor"] * props["drag_factor"]
        drift_lon_per_hour = 0.015 * props["current_factor"] * props["drag_factor"]
        
        trajectory = [{"lat": lat, "lon": lon, "hours_elapsed": 0.0, 
                     "timestamp": datetime.now(timezone.utc).isoformat()}]
        
        for h in range(1, int(hours) + 1):
            new_lat = lat + (drift_lat_per_hour * h)
            new_lon = lon + (drift_lon_per_hour * h)
            trajectory.append({
                "lat": round(new_lat, 6),
                "lon": round(new_lon, 6),
                "hours_elapsed": float(h),
                "timestamp": (datetime.now(timezone.utc) + timedelta(hours=h)).isoformat()
            })
        
        return trajectory
    
    def recommend_search_pattern(self, drift_hours: float, drift_distance_km: float,
                               object_type: str) -> Tuple[str, str]:
        """
        Recommend search pattern based on drift conditions
        
        Args:
            drift_hours: Hours since incident
            drift_distance_km: Total drift distance
            object_type: Type of object
            
        Returns:
            Tuple of (pattern_name, pattern_description)
        """
        if drift_hours < 1 and drift_distance_km < 2:
            return "Sector Search", "Use when position is recent and precise."
        elif drift_hours < 3 and drift_distance_km < 8:
            return "Expanding Square", "Covers moderate uncertainty zones."
        elif "Life" in object_type and drift_hours < 24:
            return "Parallel Track", "Person with life jacket - expanded search area."
        elif drift_hours >= 10 or drift_distance_km >= 20:
            return "Parallel Sweep", "Large area coverage for extended time/distance."
        else:
            return "Parallel Sweep", "Large area coverage for extended time/distance."
