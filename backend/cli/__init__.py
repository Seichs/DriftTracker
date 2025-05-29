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
from fastapi.templating import Jinja2Templates
import uvicorn
from fastapi.concurrency import run_in_threadpool
from data_service import get_ocean_data_file
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import status
from starlette.middleware.sessions import SessionMiddleware
import secrets

# Create the FastAPI app
app = FastAPI(title="Standalone Drift Predictor")

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Set up templates and static files if they exist
if os.path.exists(TEMPLATES_DIR):
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    # Add global context variables available to all templates
    templates.env.globals.update({
        "favicon_url": "/favicon.ico",
    })

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Also add this line for debugging
print(f"Static files directory: {os.path.join(BASE_DIR, 'static')}")
print(f"Templates directory: {os.path.join(BASE_DIR, 'templates')}")

# Add this after creating the app but before defining routes
# Make sure this comes BEFORE any route definitions
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
css_file = os.path.join(static_dir, "style.css")
if os.path.exists(css_file):
    print(f"CSS file exists at: {css_file}")
else:
    print(f"WARNING: CSS file not found at: {css_file}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Object profiles with drag factors
OBJECT_PROFILES = {
    "Person_Adult_LifeJacket": {"drag_factor": 0.8},
    "Person_Adult_NoLifeJacket": {"drag_factor": 1.1},
    "Person_Adolescent_LifeJacket": {"drag_factor": 0.9},
    "Person_Child_LifeJacket": {"drag_factor": 1.0},
    "Catamaran": {"drag_factor": 0.4},
    "Hobby_Cat": {"drag_factor": 0.5},
    "Fishing_Trawler": {"drag_factor": 0.2},
    "RHIB": {"drag_factor": 0.6},
    "SUP_Board": {"drag_factor": 1.2},
    "Windsurfer": {"drag_factor": 1.3},
    "Kayak": {"drag_factor": 1.1}
}

# Add these constants if they're not already defined
LON_KM_PER_DEGREE_AT_EQUATOR = 111.32
LAT_KM_PER_DEGREE = 110.574

# ── Copernicus test credentials ──────────────────────────────────────────────
COPERNICUS_USERNAME = "postema45@gmail.com"
COPERNICUS_PASSWORD = "IkHebAids1"


# Add these functions right after where OBJECT_PROFILES is defined in your file
# (around line 59 after the OBJECT_PROFILES dictionary)

def get_object_properties(object_type):
    """Get drift properties for different object types"""
    # Default properties
    default_props = {
        "current_factor": 1.0,  # Current influence
        "wind_factor": 0.0,  # Wind influence (windage)
        "survival_hours": 24  # Estimated survival time
    }

    # Object-specific properties
    if "Person" in object_type:
        if "LifeJacket" in object_type:
            if "Child" in object_type:
                return {
                    "current_factor": 1.0,
                    "wind_factor": 0.015,
                    "survival_hours": 12
                }
            else:  # Adult or Adolescent
                return {
                    "current_factor": 1.0,
                    "wind_factor": 0.01,
                    "survival_hours": 24
                }
        else:  # No life jacket
            return {
                "current_factor": 1.0,
                "wind_factor": 0.005,
                "survival_hours": 6
            }
    elif "Catamaran" in object_type or "Hobby_Cat" in object_type:
        return {
            "current_factor": 1.0,
            "wind_factor": 0.05,
            "survival_hours": 72
        }
    elif "Fishing_Trawler" in object_type:
        return {
            "current_factor": 1.0,
            "wind_factor": 0.03,
            "survival_hours": 120
        }
    elif "RHIB" in object_type:
        return {
            "current_factor": 1.0,
            "wind_factor": 0.02,
            "survival_hours": 48
        }
    elif "SUP_Board" in object_type or "Windsurfer" in object_type:
        return {
            "current_factor": 1.0,
            "wind_factor": 0.06,
            "survival_hours": 12
        }
    elif "Kayak" in object_type:
        return {
            "current_factor": 1.0,
            "wind_factor": 0.01,
            "survival_hours": 24
        }

    # Return default properties if object type not recognized
    return default_props


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    # Earth radius in kilometers
    R = 6371.0

    # Convert coordinates to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c

    return distance


def get_currents_at_position_and_time(ds, lat, lon, time):
    """Extract current velocities at a specific position and time"""
    try:
        # Find nearest data points
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

        return u_current, v_current
    except Exception as e:
        print(f"Error getting currents: {e}")
        # Return reasonable defaults
        return 0.0, 0.0


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
    import copernicusmarine as cm
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
        return "Creeping Line", "Extended search for significant drift."


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
        interval_positions.append({"lat": current_lat, "lon": current_lon, "hours": 0})

        # Get object characteristics (e.g., windage) based on type
        object_properties = get_object_properties(object_type)

        # Create a time array from start_time to end_time with appropriate intervals
        # For example, one position every 15 minutes
        time_interval_minutes = 15
        time_steps = int(hours * 60 / time_interval_minutes)

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
            hours_elapsed = time_interval_minutes / 60
            lon_change = u_effective * hours_elapsed * LON_KM_PER_DEGREE_AT_EQUATOR * math.cos(
                math.radians(current_lat))
            lat_change = v_effective * hours_elapsed * LAT_KM_PER_DEGREE

            # Update position
            current_lon += lon_change
            current_lat += lat_change

            # Store position at hourly intervals for visualization
            elapsed_hours = step * time_interval_minutes / 60
            if abs(elapsed_hours - round(elapsed_hours)) < 0.01:  # If close to a whole hour
                interval_positions.append({
                    "lat": current_lat,
                    "lon": current_lon,
                    "hours": round(elapsed_hours)
                })

        # If no hourly positions were recorded, at least add the final position
        if len(interval_positions) == 1:
            interval_positions.append({
                "lat": current_lat,
                "lon": current_lon,
                "hours": hours
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
        path = [{"lat": current_lat, "lon": current_lon}]

        # Calculate time step size
        if 'time' in ds.dims:
            time_values = ds.time.values
            time_count = len(time_values)

            if time_count >= 2:
                time_delta = time_values[1] - time_values[0]
                step_hours = time_delta.astype('timedelta64[h]').item().total_seconds() / 3600.0
            else:
                step_hours = 1.0
        else:
            time_count = 1
            step_hours = 1.0

        # Calculate steps
        max_steps = min(int(hours / step_hours), time_count)

        for i in range(max_steps):
            # Get current velocities at position
            try:
                # Extract velocities
                uo = ds["uo"].sel(time=ds.time.values[min(i, len(ds.time) - 1)],
                                  latitude=current_lat,
                                  longitude=current_lon,
                                  method="nearest").values.item()

                vo = ds["vo"].sel(time=ds.time.values[min(i, len(ds.time) - 1)],
                                  latitude=current_lat,
                                  longitude=current_lon,
                                  method="nearest").values.item()

                # Calculate movement
                dx = uo * 3600 * step_hours * drag_factor
                dy = vo * 3600 * step_hours * drag_factor

                # Convert to degrees
                delta_lat = dy / 111000.0
                delta_lon = dx / (111000.0 * math.cos(math.radians(current_lat)))

                # Update position
                current_lat += delta_lat
                current_lon += delta_lon

                # Add to path
                path.append({"lat": round(current_lat, 6), "lon": round(current_lon, 6)})

            except Exception as e:
                # If error, continue with a small default drift
                current_lat += 0.001 * drag_factor
                current_lon += 0.0015 * drag_factor
                path.append({"lat": round(current_lat, 6), "lon": round(current_lon, 6)})

        ds.close()
        return path

    except Exception as e:
        # Fallback path calculation
        path = [{"lat": lat, "lon": lon}]
        for i in range(int(hours)):
            lat += 0.001 * drag_factor
            lon += 0.0015 * drag_factor
            path.append({"lat": round(lat, 6), "lon": round(lon, 6)})
        return path


def recommend_search_pattern(hours: float, drift_km: float) -> tuple:
    """Recommend search pattern based on time and drift distance"""
    if hours < 1 and drift_km < 2:
        return "Sector Search", "Use when position is recent and precise."
    elif hours < 3 and drift_km < 8:
        return "Expanding Square", "Covers moderate uncertainty zones."
    else:
        return "Parallel Sweep", "Large coverage when drift is wide."


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers"""
    R = 6371.0  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Define API status check function
def check_api_status():
    """Check if Copernicus API is available"""
    return {"status": "available"}


# Make login page the default landing page at the root URL
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, error: str = None):
    """Display the login page at the root URL"""
    # Add more debug to help troubleshoot
    print("Rendering login page")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": error,
            "favicon_url": "/static/favicon.png",
            "css_url": "/static/style.css"  # Explicitly pass CSS URL
        }
    )


# Process login form submission - fixed to properly handle password
@app.post("/")
async def process_login(request: Request):
    """Process login form submission from root URL"""
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    if not username or not password:
        # If either field is missing
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Username and password are required",
                "username": username,
                "favicon_url": "/static/favicon.png"
            }
        )

    try:
        # Try authenticating with Copernicus API
        import copernicusmarine as cm
        print(f"Attempting login with username: {username} and password: {'*' * len(password)}")

        cm.login(username=username, password=password, force_overwrite=True)

        # If successful, redirect to the main application page
        return RedirectResponse(url=f"/app?username={username}", status_code=303)

    except Exception as e:
        # Authentication failed
        error_msg = "Invalid credentials or API connection error"
        print(f"Login error: {str(e)}")

        # Return to login page with error
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": error_msg,
                "username": username,
                "favicon_url": "/static/favicon.png"
            }
        )


# Make the main application page at /app
@app.get("/app", response_class=HTMLResponse)
async def app_home(request: Request, username: str = None):
    """Render the main application page after login"""
    # If no username, redirect to login
    if not username:
        return RedirectResponse(url="/", status_code=303)

    # Display the main application page
    current_timestamp = datetime.now(timezone.utc).isoformat()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "current_timestamp": current_timestamp,
            "username": username  # Pass this along for display
        }
    )


# Update your predict route to also check for username
@app.post("/predict")
async def predict(request: Request):
    """Calculate drift prediction and render result.html"""
    try:
        # Parse form data
        form_data = await request.form()

        # Continue with your existing prediction code...

    except Exception as e:
        # Handle errors
        print(f"Prediction error: {str(e)}")
        # You can redirect to login if needed
        # return RedirectResponse(url="/", status_code=303)


def calculate_simple_distance(lat1, lon1, lat2, lon2):
    """Simple function to calculate distance between coordinates in km"""
    # Earth radius in kilometers
    R = 6371.0

    # Convert coordinates to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
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
            lat, lon, start_time, end_time
        )

        # Read the file to verify contents
        if os.path.exists(data_file):
            ds = xr.open_dataset(data_file)
            variables = list(ds.variables.keys())
            dims = {dim: len(ds[dim]) for dim in ds.dims}

            # Get some sample data
            time_range = [str(ds.time.values[0]), str(ds.time.values[-1])]
            lat_range = [float(ds.latitude.values[0]), float(ds.latitude.values[-1])]
            lon_range = [float(ds.longitude.values[0]), float(ds.longitude.values[-1])]

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
                "file_info": {
                    "path": data_file,
                    "exists": os.path.exists(data_file),
                    "size_bytes": os.path.getsize(data_file) if os.path.exists(data_file) else 0
                },
                "data_summary": {
                    "variables": variables,
                    "dimensions": dims,
                    "time_range": time_range,
                    "latitude_range": lat_range,
                    "longitude_range": lon_range,
                    "current_samples": current_samples
                }
            }
        else:
            return {
                "status": "error",
                "message": "Data file not found",
                "file_info": {
                    "path": data_file,
                    "exists": False
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/test-download")
async def test_download():
    """Test endpoint to verify Copernicus download works"""
    try:
        # Use test coordinates
        lat, lon = 43.5, 0.0
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=7)

        # Get credentials
        username = os.getenv("COPERNICUS_USERNAME", "postema45@gmail.com")
        password = os.getenv("COPERNICUS_PASSWORD", "IkHebAids1")

        # Try the download
        data_file = await download_ocean_data(lat, lon, start_time, end_time, username, password)

        # Check file size
        file_size = os.path.getsize(data_file) if os.path.exists(data_file) else 0

        return {
            "status": "success",
            "message": "Download test completed",
            "file_path": data_file,
            "file_exists": os.path.exists(data_file),
            "file_size_bytes": file_size,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "coordinates": {"lat": lat, "lon": lon}
        }

    except Exception as e:
        error_details = traceback.format_exc()
        return {
            "status": "error",
            "message": f"Download test failed: {str(e)}",
            "traceback": error_details
        }


@app.get("/test-form")
async def test_form():
    """Simple HTML form for testing the predict endpoint"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Drift Prediction Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input, select { width: 100%; padding: 8px; box-sizing: border-box; }
            button { padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            #result { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>Drift Prediction Test Form</h1>
        <div class="form-group">
            <label for="lat">Latitude:</label>
            <input type="number" id="lat" step="0.000001" value="34.0" />
        </div>
        <div class="form-group">
            <label for="lon">Longitude:</label>
            <input type="number" id="lon" step="0.000001" value="-47.0" />
        </div>
        <div class="form-group">
            <label for="hours">Hours:</label>
            <input type="number" id="hours" step="1" value="24" />
        </div>
        <div class="form-group">
            <label for="object">Object Type:</label>
            <select id="object">
                <option value="Person_Adult_LifeJacket">Person with Life Jacket</option>
                <option value="Person_Adult_NoLifeJacket">Person without Life Jacket</option>
                <option value="Person_Adolescent_LifeJacket">Adolescent with Life Jacket</option>
                <option value="Person_Child_LifeJacket">Child with Life Jacket</option>
                <option value="Catamaran">Catamaran</option>
                <option value="Hobby_Cat">Hobby Cat</option>
                <option value="Fishing_Trawler">Fishing Trawler</option>
                <option value="RHIB">RHIB</option>
                <option value="SUP_Board">SUP Board</option>
                <option value="Windsurfer">Windsurfer</option>
                <option value="Kayak">Kayak</option>
            </select>
        </div>
        <button onclick="submitPrediction()">Submit Prediction</button>

        <div id="result">Results will appear here...</div>

        <script>
            async function submitPrediction() {
                const result = document.getElementById('result');
                result.textContent = 'Calculating...';

                try {
                    const response = await fetch('/predict', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            lat: parseFloat(document.getElementById('lat').value),
                            lon: parseFloat(document.getElementById('lon').value),
                            object_type: document.getElementById('object').value
                        }),
                    });

                    const data = await response.json();
                    result.textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    result.textContent = 'Error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# Update favicon route to look in the static folder
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    # Check for both favicon.ico and favicon.png in the static folder
    ico_path = os.path.join(STATIC_DIR, 'favicon.ico')
    png_path = os.path.join(STATIC_DIR, 'favicon.png')

    # Print debug info
    print(f"Looking for favicon.ico at: {ico_path} - Exists: {os.path.exists(ico_path)}")
    print(f"Looking for favicon.png at: {png_path} - Exists: {os.path.exists(png_path)}")

    # Try ico first, then png
    if os.path.exists(ico_path):
        print(f"Serving favicon.ico from {ico_path}")
        return FileResponse(ico_path, media_type="image/x-icon")
    elif os.path.exists(png_path):
        print(f"Serving favicon.png from {png_path}")
        return FileResponse(png_path, media_type="image/png")
    else:
        print("No favicon found in static folder")
        return Response(status_code=404)


# Make sure these functions are available for import
__all__ = [
    'download_ocean_data',
    'calculate_drift',
    'calculate_drift_path',
    'haversine',
    'recommend_search_pattern',
    'OBJECT_PROFILES'
]

# Keep the standalone execution
if __name__ == "__main__":
    print("\n\n*** STARTING STANDALONE DRIFT SERVER ON PORT 8001 ***\n\n")
    uvicorn.run(app, host="127.0.0.1", port=8001)