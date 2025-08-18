"""
Drift calculation module for ocean drift prediction
"""
import math
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

class DriftCalculator:
    """Calculate drift trajectories for objects in ocean currents"""
    
    def __init__(self):
        self.earth_radius_km = 6371.0
        self.meters_per_degree_lat = 111574.0  # meters per degree of latitude
        self.meters_per_degree_lon_at_equator = 111320.0  # meters per degree longitude at equator
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
        
        return self.earth_radius_km * c
    
    def get_object_properties(self, object_type: str) -> Dict[str, float]:
        """
        Get drift properties for different object types
        
        Args:
            object_type: Type of drifting object
            
        Returns:
            Dictionary with drift properties
        """
        default_props = {
            "current_factor": 1.0,  # Current influence
            "wind_factor": 0.0,     # Wind influence (windage)
            "drag_factor": 1.0      # Overall drag factor
        }
        
        # Object-specific properties
        if "Person" in object_type:
            if "LifeJacket" in object_type:
                if "Child" in object_type:
                    return {
                        "current_factor": 1.0,
                        "wind_factor": 0.015,
                        "drag_factor": 1.0
                    }
                else:  # Adult or Adolescent
                    return {
                        "current_factor": 1.0,
                        "wind_factor": 0.01,
                        "drag_factor": 0.8 if "Adult" in object_type else 0.9
                    }
            else:  # No life jacket
                return {
                    "current_factor": 1.0,
                    "wind_factor": 0.005,
                    "drag_factor": 1.1
                }
        elif "Catamaran" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.05, "drag_factor": 0.4}
        elif "Hobby_Cat" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.05, "drag_factor": 0.5}
        elif "Fishing_Trawler" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.03, "drag_factor": 0.2}
        elif "RHIB" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.02, "drag_factor": 0.6}
        elif "SUP_Board" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.06, "drag_factor": 1.2}
        elif "Windsurfer" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.06, "drag_factor": 1.3}
        elif "Kayak" in object_type:
            return {"current_factor": 1.0, "wind_factor": 0.01, "drag_factor": 1.1}
        
        return default_props
    
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
        try:
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
                # Use first time step if available
                if 'time' in ds.dims and len(ds.time) > 0:
                    u_current = float(ds.uo.isel(time=0).interp(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values)
                    
                    v_current = float(ds.vo.isel(time=0).interp(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values)
                else:
                    u_current = float(ds.uo.interp(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values)
                    
                    v_current = float(ds.vo.interp(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values)
            
            return u_current, v_current
            
        except Exception as e:
            logger.warning(f"Error getting currents at {lat}, {lon}: {e}")
            # Return reasonable defaults
            return 0.0, 0.0
    
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
                timestamp = datetime.utcnow().isoformat()
            
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
                        timestamp = datetime.utcnow().isoformat()
                    
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
                     "timestamp": datetime.utcnow().isoformat()}]
        
        for h in range(1, int(hours) + 1):
            new_lat = lat + (drift_lat_per_hour * h)
            new_lon = lon + (drift_lon_per_hour * h)
            trajectory.append({
                "lat": round(new_lat, 6),
                "lon": round(new_lon, 6),
                "hours_elapsed": float(h),
                "timestamp": (datetime.utcnow() + timedelta(hours=h)).isoformat()
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
        else:
            return "Parallel Sweep", "Large area coverage for extended time/distance."
