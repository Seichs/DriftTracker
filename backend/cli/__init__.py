"""
Standalone Drift Prediction Server

This file contains a complete, self-contained FastAPI application
that implements the entire drift prediction system.
"""
import os
import sys
import math
import uuid
import asyncio
import requests
import numpy as np
import xarray as xr
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import traceback
import json
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
# Jinja2Templates not needed - serving static HTML files
import uvicorn
from fastapi.concurrency import run_in_threadpool
from drifttracker.data_service import get_ocean_data_file
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import copernicusmarine as cm
from fastapi import status
from starlette.middleware.sessions import SessionMiddleware
import secrets

# Create the FastAPI app
app = FastAPI(title="Standalone Drift Predictor")

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Templates not needed - serving static HTML files from frontend directory

# Frontend directory is mounted as /static instead

# Frontend directory will be mounted as /static for CSS, JS, and images

# Mount frontend src directory for static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    # Mount the entire src directory as /static
    src_dir = os.path.join(frontend_dir, "src")
    if os.path.exists(src_dir):
        app.mount("/static", StaticFiles(directory=src_dir), name="static")
        print(f"Frontend src directory mounted at /static: {src_dir}")
    else:
        print(f"WARNING: Frontend src directory not found at: {src_dir}")
else:
    print(f"WARNING: Frontend directory not found at: {frontend_dir}")

# Frontend directory is now mounted as /static, so we don't need the old static directory

# Import centralized configuration
from drifttracker.config import (
    OBJECT_PROFILES, 
    LON_KM_PER_DEGREE_AT_EQUATOR, 
    LAT_KM_PER_DEGREE,
    COPERNICUS_USERNAME,
    COPERNICUS_PASSWORD,
    ADMIN_USERNAME,
    ADMIN_PASSWORD
)


# Import centralized object properties function
from drifttracker.config import get_object_properties


# Import centralized distance calculation function
from drifttracker.common_utils import calculate_distance


# Import centralized current extraction function
from drifttracker.common_utils import get_currents_at_position


def create_synthetic_ocean_data(lat, lon, start_time, end_time):
    """Create synthetic ocean current data for testing or fallback"""
    # Create a time range
    time_delta = end_time - start_time
    hours = int(time_delta.total_seconds() / 3600) + 1
    times = [start_time + timedelta(hours=i) for i in range(hours)]

    # Create lat/lon ranges (±2 degrees)
    lat_range = np.linspace(lat - 2, lat + 2, 20)
    lon_range = np.linspace(lon - 2, lon + 2, 20)

    # Create random currents (reasonable values: -0.5 to 0.5 m/s)
    uo = np.random.normal(0, 0.2, (len(times), len(lat_range), len(lon_range)))
    vo = np.random.normal(0, 0.2, (len(times), len(lat_range), len(lon_range)))

    # Create dataset
    ds = xr.Dataset(
        data_vars={
            "uo": (["time", "latitude", "longitude"], uo),
            "vo": (["time", "latitude", "longitude"], vo),
        },
        coords={
            "time": times,
            "latitude": lat_range,
            "longitude": lon_range,
        },
    )

    return ds


def download_ocean_data(lat, lon, start_time, end_time,
                        username=COPERNICUS_USERNAME,
                        password=COPERNICUS_PASSWORD):
    """Download ocean current data from Copernicus Marine API using copernicusmarine library"""
    # Create the data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_file = os.path.join(DATA_DIR, f"currents_{timestamp}.nc")

    # Calculate area around the point (±2 degrees)
    lat_buffer = 2.0
    lon_buffer = 2.0

    min_lat = lat - lat_buffer
    max_lat = lat + lat_buffer
    min_lon = lon - lon_buffer
    max_lon = lon + lon_buffer

    # Format dates for data request
    start_date = start_time.strftime("%Y-%m-%d")
    end_date = end_time.strftime("%Y-%m-%d")

    print(f"*** DOWNLOADING OCEAN DATA FROM COPERNICUS API ***")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Area: Lat {min_lat:.2f} to {max_lat:.2f}, Lon {min_lon:.2f} to {max_lon:.2f}")

    print(f"Using Copernicus credentials for user: {username}")

    # ── Copernicus-Marine ≥ 2.0 API ─────────────────────────────
    print(f"Copernicus-Marine toolbox version {cm.__version__}")

    # Create (or reuse) ~/.copernicusmarine-credentials
    cm.login(username=username, password=password, force_overwrite=False)

    # Define dataset and variables
    dataset_id = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"  # Global ocean currents
    variables = ["uo", "vo"]  # Ocean current components

    # Beginning data download - this may take some time...
    print("Beginning data download - this may take some time...")

    # V2-style subset call - each selection criterion is a top-level keyword argument
    resp = cm.subset(
        dataset_id=dataset_id,
        variables=variables,
        minimum_longitude=min_lon,
        maximum_longitude=max_lon,
        minimum_latitude=min_lat,
        maximum_latitude=max_lat,
        start_datetime=start_time,  # datetime or "YYYY-MM-DD"
        end_datetime=end_time,
        output_filename=data_file,  # optional - saves to NetCDF
        # output_directory=DATA_DIR,    # default is cwd if you omit this
        force_download=True  # overwrite if file already exists
    )

    # When you pass output_filename, subset() returns a ResponseSubset
    # whose .file_path points to the NetCDF that was written
    data_file = getattr(resp, "file_path", data_file)

    # Check if download was successful
    if os.path.exists(data_file) and os.path.getsize(data_file) > 0:
        print(f"SUCCESS: Data downloaded to {data_file} ({os.path.getsize(data_file)} bytes)")
        return data_file
    else:
        print(f"ERROR: Download appeared to complete but file is empty or missing")
        raise Exception("API download failed: empty or missing file")


def create_fallback_data_file(min_lat, max_lat, min_lon, max_lon, start_time, end_time):
    """Create a fallback data file if download fails"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_file = os.path.join(DATA_DIR, f"fallback_{timestamp}.nc")

    ds = create_synthetic_ocean_data(
        (min_lat + max_lat) / 2,
        (min_lon + max_lon) / 2,
        start_time,
        end_time
    )

    ds.to_netcdf(data_file)
    print(f"Fallback data saved to {data_file}")

    return data_file


def get_ocean_data(lat, lon, start_time, end_time):
    """Get ocean current data for a specific location and time range"""
    try:
        # Calculate buffer around the point (±2 degrees)
        lat_buffer = 2.0
        lon_buffer = 2.0

        min_lat = lat - lat_buffer
        max_lat = lat + lat_buffer
        min_lon = lon - lon_buffer
        max_lon = lon + lon_buffer

        # Download the ocean data - using global constants
        data_file = download_ocean_data(
            lat, lon, start_time, end_time,
            COPERNICUS_USERNAME, COPERNICUS_PASSWORD
        )

        # Load the data with xarray
        ds = xr.open_dataset(data_file)

        return ds
    except Exception as e:
        print(f"Error getting ocean data: {e}")
        # Return synthetic fallback
        print("Creating synthetic ocean data as fallback")
        return create_synthetic_ocean_data(lat, lon, start_time, end_time)


def get_search_pattern(object_type, hours, distance_km):
    """Recommend search pattern based on object and drift conditions"""
    # Simple logic to determine appropriate search pattern
    if hours < 2 and distance_km < 3:
        return "Sector Search", "Location is recent and fairly precise."
    elif hours < 6 and distance_km < 10:
        return "Expanding Square", "Moderate time and drift distance."
    elif "Life" in object_type and hours < 24:
        return "Parallel Track", "Person with life jacket - expanded search area."
    else:
        return "Parallel Sweep", "Large area, long time, or high uncertainty."


def fallback_drift_calculation(lat, lon, hours, object_type):
    """Simple fallback calculation if detailed ocean data fails"""
    # Get object properties
    props = get_object_properties(object_type)

    # Default drift components (very simplified)
    # Objects typically drift 3% of wind speed plus current
    # Here we're using constants as a backup
    drift_lat = 0.01 * hours * props["current_factor"]  # Northward drift
    drift_lon = 0.015 * hours * props["current_factor"]  # Eastward drift

    # Apply the drift
    new_lat = lat + drift_lat
    new_lon = lon + drift_lon

    # Create hourly positions
    interval_positions = [{"lat": lat, "lon": lon, "hours": 0}]
    for h in range(1, int(hours) + 1):
        if h <= hours:
            pos_lat = lat + (drift_lat * h / hours)
            pos_lon = lon + (drift_lon * h / hours)
            interval_positions.append({"lat": pos_lat, "lon": pos_lon, "hours": h})

    return new_lat, new_lon, interval_positions


# Drift calculation function
def calculate_drift(lat, lon, hours, object_type, start_time, end_time, currents_data):
    """Calculate drift for an object using time-specific ocean current data"""
    try:
        # Starting position
        current_lat = lat
        current_lon = lon

        # Create a list to store positions at regular intervals
        interval_positions = []
        interval_positions.append({"lat": current_lat, "lon": current_lon, "hours": 0, "timestamp": start_time.isoformat()})

        # Get object characteristics (e.g., windage) based on type
        object_properties = get_object_properties(object_type)

        # Create a time array from start_time to end_time with appropriate intervals
        time_interval_minutes = 15
        total_minutes = hours * 60
        time_steps = int(total_minutes / time_interval_minutes)

        # Loop through each time step
        for step in range(1, time_steps + 1):
            # Calculate the current timestamp for this step
            current_time = start_time + timedelta(minutes=step * time_interval_minutes)

            # Skip if we've gone past the end time
            if current_time > end_time:
                break

            # Get ocean currents for this position and time from the data
            u_current, v_current = get_currents_at_position_and_time(
                currents_data,
                current_lat,
                current_lon,
                current_time
            )

            # Apply object-specific modifications (like windage)
            u_effective = u_current * object_properties["current_factor"]
            v_effective = v_current * object_properties["current_factor"]

            # Calculate new position based on currents
            # Simple movement calculation - could be replaced with more sophisticated models
            dt_seconds = time_interval_minutes * 60
            dx_meters = u_effective * dt_seconds
            dy_meters = v_effective * dt_seconds

            lat_change_deg = dy_meters / (LAT_KM_PER_DEGREE * 1000)
            lon_change_deg = dx_meters / (LON_KM_PER_DEGREE_AT_EQUATOR * 1000 * math.cos(math.radians(current_lat)))

            # Update position
            current_lon += lon_change_deg
            current_lat += lat_change_deg

            # Store position at hourly intervals for visualization
            elapsed_hours_total = step * time_interval_minutes / 60
            interval_positions.append({
                "lat": round(current_lat, 6),
                "lon": round(current_lon, 6),
                "hours": round(elapsed_hours_total, 2),
                "timestamp": current_time.isoformat()
            })

        # If no hourly positions were recorded, at least add the final position
        if len(interval_positions) == 1:
            interval_positions.append({
                "lat": current_lat,
                "lon": current_lon,
                "hours": hours,
                "timestamp": end_time.isoformat()
            })

        return current_lat, current_lon, interval_positions
    except Exception as e:
        print(f"Error in drift calculation: {e}")
        # Fallback to a simpler calculation if needed
        return fallback_drift_calculation(lat, lon, hours, object_type)


def calculate_drift_path(nc_file: str, lat: float, lon: float,
                         hours: float, drag_factor: float = 1.0) -> List[Dict[str, float]]:
    """Calculate drift path with intermediate points"""
    try:
        # Load data
        ds = xr.open_dataset(nc_file)

        # Set initial position
        current_lat, current_lon = lat, lon
        path = [{"lat": current_lat, "lon": current_lon, "hours_elapsed": 0.0}]

        # Calculate time step size from NetCDF
        step_hours = 1.0
        if 'time' in ds.dims and len(ds.time.values) > 0:
            time_values = ds.time.values
            if len(time_values) >= 2:
                try:
                    time_delta_pd = pd.Timestamp(time_values[1]) - pd.Timestamp(time_values[0])
                    step_hours = time_delta_pd.total_seconds() / 3600.0
                except TypeError:
                    time_delta_np = time_values[1] - time_values[0]
                    step_hours = time_delta_np.astype('timedelta64[s]').item().total_seconds() / 3600.0

            if step_hours <= 0:
                step_hours = 1.0
        
        num_steps = int(hours / step_hours)
        if num_steps == 0 and hours > 0:
            num_steps = 1
            step_hours = hours

        for i in range(num_steps):
            # Determine time index for NetCDF data
            time_index_in_ds = min(i, len(ds.time) - 1) if 'time' in ds.dims and len(ds.time) > 0 else 0
            
            # Get current velocities at position
            try:
                selected_time = ds.time.values[time_index_in_ds] if 'time' in ds.dims and len(ds.time) > 0 else None

                if selected_time is not None:
                    uo = ds["uo"].sel(time=selected_time,
                                      latitude=current_lat,
                                      longitude=current_lon,
                                      method="nearest").values.item()

                    vo = ds["vo"].sel(time=selected_time,
                                      latitude=current_lat,
                                      longitude=current_lon,
                                      method="nearest").values.item()
                else:
                    uo = ds["uo"].isel(latitude=0, longitude=0).interp(latitude=current_lat, longitude=current_lon, method="nearest").values.item()
                    vo = ds["vo"].isel(latitude=0, longitude=0).interp(latitude=current_lat, longitude=current_lon, method="nearest").values.item()

                # Calculate movement in meters for the step_hours
                dx_meters = uo * step_hours * 3600 * drag_factor
                dy_meters = vo * step_hours * 3600 * drag_factor

                # Convert to degrees
                delta_lat = dy_meters / 110574.0
                delta_lon = dx_meters / (111320.0 * math.cos(math.radians(current_lat)))

                # Update position
                current_lat += delta_lat
                current_lon += delta_lon
                
                hours_elapsed = (i + 1) * step_hours
                # Add to path
                path.append({"lat": round(current_lat, 6), "lon": round(current_lon, 6), "hours_elapsed": round(hours_elapsed,2)})

            except Exception as e:
                print(f"Error during step {i} in calculate_drift_path: {e}")
                # If error, continue with a small default drift for this step
                current_lat += 0.001 * drag_factor * step_hours
                current_lon += 0.0015 * drag_factor * step_hours
                hours_elapsed = (i + 1) * step_hours
                path.append({"lat": round(current_lat, 6), "lon": round(current_lon, 6), "hours_elapsed": round(hours_elapsed,2)})

        ds.close()
        return path

    except Exception as e:
        print(f"Error in calculate_drift_path: {e}")
        # Fallback path calculation
        path = [{"lat": lat, "lon": lon, "hours_elapsed": 0.0}]
        step_hours_fallback = 1.0
        num_steps_fallback = int(hours / step_hours_fallback)
        if num_steps_fallback == 0 and hours > 0: num_steps_fallback = 1

        for i in range(num_steps_fallback):
            lat += 0.001 * drag_factor * step_hours_fallback
            lon += 0.0015 * drag_factor * step_hours_fallback
            hours_elapsed = (i + 1) * step_hours_fallback
            path.append({"lat": round(lat, 6), "lon": round(lon, 6), "hours_elapsed": round(hours_elapsed,2)})
        return path


def recommend_search_pattern(hours: float, drift_km: float) -> tuple:
    """Recommend search pattern based on time and drift distance"""
    if hours < 1 and drift_km < 2:
        return "Sector Search", "Use when position is recent and precise."
    elif hours < 3 and drift_km < 8:
        return "Expanding Square", "Covers moderate uncertainty zones."
    else:
        return "Parallel Sweep", "Large coverage when drift is wide or time is long."


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers"""
    R = 6371.0  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Make login page the default landing page at the root URL
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, error: Optional[str] = None):
    """Display the login page at the root URL"""
    # Add more debug to help troubleshoot
    print("Rendering login page")
    
    # Read the frontend login.html file
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    login_file = os.path.join(frontend_dir, "html", "login.html")
    
    if os.path.exists(login_file):
        with open(login_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Login page not found</h1>", status_code=404)


# Process login form submission - fixed to properly handle password
@app.post("/")
async def process_login(request: Request):
    """Process login form submission from root URL"""
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    if not username or not password:
        # If either field is missing
        return RedirectResponse(url="/?error=Username+and+password+are+required", status_code=status.HTTP_303_SEE_OTHER)

    # Check admin credentials first
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print(f"Admin login successful for user: {username}")
        return RedirectResponse(url=f"/app?username={username}", status_code=status.HTTP_303_SEE_OTHER)

    # If not admin, try Copernicus Marine API authentication
    try:
        print(f"Attempting Copernicus login with username: {username} and password: {'*' * len(password)}")
        cm.login(username=username, password=password, force_overwrite=True)
        
        # If successful, redirect to the main application page
        print(f"Copernicus login successful for user: {username}")
        return RedirectResponse(url=f"/app?username={username}", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        # Authentication failed
        error_msg = "Invalid credentials or API connection error"
        print(f"Login error: {str(e)}")

        # Return to login page with error
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)


# Make the main application page at /app
@app.get("/app", response_class=HTMLResponse)
async def app_home(request: Request, username: Optional[str] = None):
    """Render the main application page after login"""
    # If no username, redirect to login
    if not username:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # Display the main application page
    current_timestamp = datetime.now(timezone.utc).isoformat()
    
    # Read the frontend index.html file
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
    index_file = os.path.join(frontend_dir, "html", "index.html")
    
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Main app page not found</h1>", status_code=404)


# Update your predict route to also check for username
@app.post("/predict")
async def predict(request: Request):
    """Calculate drift prediction and render result.html"""
    try:
        form_data = await request.form()
        # Basic security: ensure user is "logged in" (e.g. by checking if username is in form_data or session)
        username = form_data.get("username")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        lat = float(form_data.get("lat"))
        lon = float(form_data.get("lon"))
        hours = int(form_data.get("hours"))
        object_type = form_data.get("object_type")
        
        # Incident date and time
        incident_date_str = form_data.get("date")
        incident_time_str = form_data.get("time")

        if not all([incident_date_str, incident_time_str]):
            incident_dt = datetime.now(timezone.utc) # Default to now if not provided
        else:
            try:
                incident_dt = datetime.strptime(f"{incident_date_str} {incident_time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date/time format.")

        # Ensure incident time is not in the future
        if incident_dt > datetime.now(timezone.utc):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident time cannot be in the future.")

        # Define time range for data download (e.g., 24 hours before to 'hours' after incident)
        start_data_fetch_dt = incident_dt - timedelta(hours=1)
        end_data_fetch_dt = incident_dt + timedelta(hours=hours) + timedelta(hours=1)

        # Get drag factor
        drag_factor = OBJECT_PROFILES.get(object_type, {}).get("drag_factor", 1.0)

        # Download data (blocking, run in threadpool)
        nc_file_path = await run_in_threadpool(
            download_ocean_data,
            lat, lon, 
            start_data_fetch_dt,
            end_data_fetch_dt,
            COPERNICUS_USERNAME, 
            COPERNICUS_PASSWORD
        )

        if not nc_file_path or not os.path.exists(nc_file_path):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve ocean data.")

        # Calculate drift path
        drift_path_points = await run_in_threadpool(
            calculate_drift_path,
            nc_file_path,
            lat,
            lon,
            float(hours),
            drag_factor
        )

        if not drift_path_points:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Drift calculation failed.")

        final_pos = drift_path_points[-1]
        new_lat, new_lon = final_pos["lat"], final_pos["lon"]

        # Calculate total distance drifted
        total_distance_km = 0
        if len(drift_path_points) > 1:
            total_distance_km = haversine(lat, lon, new_lat, new_lon)
        
        # Recommend search pattern
        pattern_name, pattern_desc = recommend_search_pattern(float(hours), total_distance_km)
        
        # Return JSON response instead of template
        return JSONResponse(content={
            "status": "success",
            "orig_lat": lat,
            "orig_lon": lon,
            "new_lat": new_lat,
            "new_lon": new_lon,
            "drift_hours": hours,
            "object_type": object_type,
            "total_distance_km": round(total_distance_km, 2),
            "search_pattern_name": pattern_name,
            "search_pattern_description": pattern_desc,
            "drift_path": drift_path_points,
            "username": username
        })

    except HTTPException:
        raise
    except Exception as e:
        # Handle errors
        print(f"Prediction error: {str(e)}")
        return JSONResponse(content={
            "status": "error",
            "error": True,
            "error_message": f"An error occurred during prediction: {str(e)}",
        })


def calculate_simple_distance(lat1, lon1, lat2, lon2):
    """Simple function to calculate distance between coordinates in km"""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


@app.get("/debug-data/{lat}/{lon}")
async def debug_data(lat: float, lon: float):
    """Debug endpoint to test data download and processing"""
    try:
        # Set up test parameters
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()

        # Fix 2 & 3: Use run_in_threadpool instead of direct await
        data_file = await run_in_threadpool(
            download_ocean_data,
            lat, lon, start_time, end_time,
            COPERNICUS_USERNAME, COPERNICUS_PASSWORD
        )

        # Read the file to verify contents
        if os.path.exists(data_file):
            ds = xr.open_dataset(data_file)
            variables = list(ds.variables.keys())
            dims = {dim: len(ds[dim]) for dim in ds.dims}

            # Get some sample data
            time_range_ds = [str(ds.time.values[0]), str(ds.time.values[-1])] if 'time' in ds else "N/A"
            lat_range_ds = [float(ds.latitude.values[0]), float(ds.latitude.values[-1])] if 'latitude' in ds else "N/A"
            lon_range_ds = [float(ds.longitude.values[0]), float(ds.longitude.values[-1])] if 'longitude' in ds else "N/A"

            # Get some current samples
            if 'uo' in ds and 'vo' in ds:
                uo_mean = float(ds.uo.mean().values)
                vo_mean = float(ds.vo.mean().values)
                current_samples = {"uo_mean": round(uo_mean, 3), "vo_mean": round(vo_mean, 3)}
            else:
                current_samples = {"error": "Current variables not found in dataset"}

            ds.close()

            return {
                "status": "success",
                "data_file": data_file,
                "variables": variables,
                "dimensions": dims,
                "time_range": time_range_ds,
                "latitude_range": lat_range_ds,
                "longitude_range": lon_range_ds,
                "current_samples": current_samples
            }
        else:
            return {"status": "error", "message": "Data file not created."}

    except Exception as e:
        return {"status": "error", "message": str(e), "details": traceback.format_exc()}


# Favicon is now served automatically by the static file mounting


# Make sure these functions are available for import
__all__ = [
    'download_ocean_data',
    'calculate_drift',
    'calculate_drift_path',
    'haversine',
    'recommend_search_pattern',
    'OBJECT_PROFILES',
    'app'
]

# Keep the standalone execution
if __name__ == "__main__":
    print("\n\n*** STARTING STANDALONE DRIFT SERVER ON PORT 8001 ***\n\n")
    # Ensure TEMPLATES_DIR and STATIC_DIR are correctly configured before running.
    # The app mounts static files based on STATIC_DIR or static_dir.
    # Verify these paths are correct relative to where this script is run.
    # Example: if run from DriftTracker/backend/, then cli/static and cli/templates should exist.
    
    # Check if templates and static dirs are correctly found from this script's perspective
    print(f"Running from: {os.getcwd()}")
    print(f"Base dir for __init__.py: {BASE_DIR}")
    print(f"Templates dir: {TEMPLATES_DIR}, Exists: {os.path.exists(TEMPLATES_DIR)}")
    print(f"Static dir for app mount: {STATIC_DIR}, Exists: {os.path.exists(STATIC_DIR)}")
    print(f"Static dir for explicit mount: {static_dir}, Exists: {os.path.exists(static_dir)}")

    if not os.path.exists(TEMPLATES_DIR):
        print(f"ERROR: Templates directory not found at {TEMPLATES_DIR}")
        print("Please ensure your 'templates' folder is correctly placed relative to this script.")
    if not os.path.exists(STATIC_DIR) and not os.path.exists(static_dir):
         print(f"ERROR: Static directory not found at {STATIC_DIR} or {static_dir}")
         print("Please ensure your 'static' folder is correctly placed relative to this script.")
    
    uvicorn.run(app, host="127.0.0.1", port=8001)