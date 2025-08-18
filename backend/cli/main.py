# Standard library imports
import asyncio
import logging
import math
import os
from pathlib import Path
import sys
import time
import traceback
from datetime import datetime, timedelta

# Third-party imports
import copernicusmarine as cm
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import xarray as xr

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

object_profiles = {
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

# Force logging to output to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Add a simple sanity check that will print when the module loads
print("MAIN.PY LOADED - LOGGING INITIALIZED")
logger.info("Logger initialized in main.py")

def fetch_hourly_copernicus_data(lat, lon, start_time, end_time, username, password):
    """Fetch ocean current data from Copernicus Marine using the new SDK"""
    # Make sure we have absolute paths
    abs_data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
    os.makedirs(abs_data_dir, exist_ok=True)
    abs_output_file = os.path.join(abs_data_dir, "drift_data.nc")

    # Delete the file if it already exists
    if os.path.exists(abs_output_file):
        try:
            os.remove(abs_output_file)
        except:
            pass

    lat_min = lat - 0.1
    lat_max = lat + 0.1
    lon_min = lon - 0.1
    lon_max = lon + 0.1

    date_min = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    date_max = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    try:
        # Direct download with minimal logic
        cm.subset(
            dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
            username=username,
            password=password,
            variables=["uo", "vo"],
            minimum_longitude=lon_min,
            maximum_longitude=lon_max,
            minimum_latitude=lat_min,
            maximum_latitude=lat_max,
            minimum_depth=0.49402499198913574,
            maximum_depth=0.49402499198913574,
            start_datetime=date_min,
            end_datetime=date_max,
            output_directory=abs_data_dir,
            output_filename="drift_data.nc"
        )

        # Verify file exists
        if os.path.exists(abs_output_file):
            return abs_output_file
        else:
            # Search for any .nc files
            for f in os.listdir(abs_data_dir):
                if f.endswith(".nc"):
                    return os.path.join(abs_data_dir, f)

            # No files found
            raise Exception("Download completed but no .nc files found")

    except Exception as e:
        logging.error(f"Error in Copernicus download: {str(e)}")


def integrate_hourly_drift(nc_file, lat, lon, hours, drag):
    ds = xr.open_dataset(nc_file)
    coords = (lat, lon)
    for i in range(min(int(hours), len(ds.time))):
        uo = ds["uo"].isel(time=i).interp(latitude=coords[0], longitude=coords[1]).values.item()
        vo = ds["vo"].isel(time=i).interp(latitude=coords[0], longitude=coords[1]).values.item()

        dx = uo * 3.6 * drag
        dy = vo * 3.6 * drag

        delta_lat = dy / 111.0
        delta_lon = dx / (111.0 * math.cos(math.radians(coords[0])))

        coords = (coords[0] + delta_lat, coords[1] + delta_lon)
    ds.close()
    return round(coords[0], 6), round(coords[1], 6)

def integrate_drift_at_intervals(nc_file, lat, lon, total_hours, drag, interval_minutes=5):
    ds = xr.open_dataset(nc_file)
    coords = (lat, lon)
    interval_hours = interval_minutes / 60
    steps = int(total_hours / interval_hours)
    positions = []

    for step in range(steps + 1):
        hours_elapsed = step * interval_hours
        # Corrected datetime usage
        timestamp = (datetime.utcnow() + timedelta(hours=2) - timedelta(hours=total_hours - hours_elapsed)).isoformat()
        if step > 0 and step < steps:
            positions.append({
                "lat": round(coords[0], 6),
                "lon": round(coords[1], 6),
                "timestamp": timestamp,
                "hours": round(hours_elapsed, 2)
            })
        if hours_elapsed >= total_hours:
            break
        step_hours = min(interval_hours, total_hours - hours_elapsed)
        for _ in range(int(step_hours * 60)):
            uo = ds["uo"].isel(time=0).interp(latitude=coords[0], longitude=coords[1]).values.item()
            vo = ds["vo"].isel(time=0).interp(latitude=coords[0], longitude=coords[1]).values.item()

            dx = uo * 0.06 * drag
            dy = vo * 0.06 * drag

            delta_lat = dy / 111.0
            delta_lon = dx / (111.0 * math.cos(math.radians(coords[0])))

            coords = (coords[0] + delta_lat, coords[1] + delta_lon)
    ds.close()
    return positions

def recommend_search_pattern(hours, drift_km):
    if hours < 1 and drift_km < 2:
        return "Sector Search", "Use when position is recent and precise."
    elif hours < 3 and drift_km < 8:
        return "Expanding Square", "Covers moderate uncertainty zones."
    else:
        return "Parallel Sweep", "Large coverage when drift is wide."

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # This route seems to be unused or overridden by the one in backend/cli/__init__.py
    # Consider removing or reconciling it.
    pass


def reliable_download(lat, lon, start_time, end_time, username, password):
    """Download ocean current data from Copernicus Marine"""
    # Imports os, time, copernicusmarine were redundant here

    # Create data directory
    data_dir = os.path.abspath(os.path.join(os.getcwd(), "data"))
    os.makedirs(data_dir, exist_ok=True)

    # Set parameters
    lat_min, lat_max = lat - 0.1, lat + 0.1
    lon_min, lon_max = lon - 0.1, lon + 0.1
    date_min = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    date_max = end_time.strftime("%Y-%m-%dT%H:%M:%S")

    # Create unique filename
    output_filename = f"drift_{lat}_{lon}_{int(time.time())}.nc"
    output_path = os.path.join(data_dir, output_filename)

    # Download the data
    cm.subset(
        dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
        username=username,
        password=password,
        variables=["uo", "vo"],
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_depth=0.49402499198913574,
        maximum_depth=0.49402499198913574,
        start_datetime=date_min,
        end_datetime=date_max,
        output_directory=data_dir,
        output_filename=output_filename
    )

    # Check if file exists and return path
    if os.path.exists(output_path):
        return output_path

    # If not found, look for any .nc files
    for f in os.listdir(data_dir):
        if f.endswith(".nc"):
            return os.path.join(data_dir, f)

    # No file found
    raise Exception("Failed to download data")

@app.post("/predict")
async def predict(request: Request, lat: float = Form(...), lon: float = Form(...),
                  hours: int = Form(...), username: str = Form(...), password: str = Form(...),
                  date: str = Form(None), time: str = Form(None)): # Renamed 'time' parameter to avoid conflict
    """Predict drift from a starting position"""

    try:
        # Set up time range
        if date and time: # Use the renamed 'time_str'
            incident_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        else:
            incident_datetime = datetime.utcnow()

        end_time = incident_datetime
        start_time = incident_datetime - timedelta(hours=7)
        print(f"TIME RANGE: {start_time} to {end_time}")

        print("STARTING DOWNLOAD IN THREAD")
        # Run the blocking download in a thread
        result = await asyncio.to_thread(
            fetch_hourly_copernicus_data,
            lat, lon, start_time, end_time, username, password
        )
        print(f"DOWNLOAD THREAD COMPLETED: {result}")

        # Simply return success for debugging
        return {
            "status": "success",
            "message": "Data downloaded successfully",
            "file": result
        }

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERROR IN PREDICT ENDPOINT: {str(e)}\n{error_details}")

        # Return error information
        return {
            "status": "error",
            "message": f"Error occurred: {str(e)}",
            "details": error_details
        }

# Add this new route to your FastAPI app - it eliminates async complexity
@app.get("/direct-download")
def direct_download():
    """Direct synchronous download endpoint - no async or threads"""
    # Imports os, sys, time, pathlib.Path, copernicusmarine, traceback, datetime were redundant here

    # Create log file for diagnostics
    log_file_path = os.path.abspath(os.path.join(os.getcwd(), "direct_download.log"))

    try:
        with open(log_file_path, "w") as log:
            def write_log(message):
                # Corrected datetime usage
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log.write(f"{timestamp_str} - {message}\n")
                log.flush()  # Force immediate write

            write_log(f"Direct download test started")
            write_log(f"Python: {sys.executable} ({sys.version})")
            write_log(f"Working directory: {os.getcwd()}")

            # Create absolute paths
            data_dir = os.path.abspath(os.path.join(os.getcwd(), "direct_data"))
            write_log(f"Data directory: {data_dir}")

            # Ensure directory exists with explicit permissions
            if not os.path.exists(data_dir):
                write_log(f"Creating directory: {data_dir}")
                os.makedirs(data_dir, exist_ok=True)

            # Set parameters - use exactly what worked in the test
            username = "postema45@gmail.com"  # Your actual Copernicus username
            password = "IkHebAids1"  # Your actual Copernicus password

            # Define output file
            output_filename = "direct_test.nc"
            output_path = os.path.join(data_dir, output_filename)
            write_log(f"Output file will be: {output_path}")

            # Remove file if it exists
            if os.path.exists(output_path):
                write_log(f"Removing existing file: {output_path}")
                os.remove(output_path)

            write_log(f"Starting direct download...")

            try:
                # Same parameters as the successful test
                result = cm.subset(
                    dataset_id="cmems_mod_glo_phy_anfc_0.083deg_PT1H-m",
                    username=username,
                    password=password,
                    variables=["uo"],
                    minimum_longitude=-1.0,
                    maximum_longitude=1.0,
                    minimum_latitude=43.0,
                    maximum_latitude=45.0,
                    start_datetime="2023-01-01T00:00:00",
                    end_datetime="2023-01-01T01:00:00",
                    output_directory=data_dir,
                    output_filename=output_filename
                )

                write_log(f"Download call completed")
                write_log(f"Result: {result}")

                # Wait a moment (just in case there's a file system delay)
                time.sleep(1)

                # Check if file exists
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    write_log(f"SUCCESS: File created at {output_path}, size: {file_size} bytes")
                else:
                    write_log(f"ERROR: File not found at {output_path}")

                    # Check for any .nc files
                    nc_files = []
                    for root, dirs, files in os.walk(data_dir):
                        for file in files:
                            if file.endswith(".nc"):
                                nc_path = os.path.join(root, file)
                                nc_files.append(nc_path)

                    if nc_files:
                        write_log(f"Found other .nc files: {nc_files}")
                    else:
                        write_log(f"No .nc files found in {data_dir}")

                    # Check permissions on directory
                    write_log(f"Directory permissions: {oct(os.stat(data_dir).st_mode)}")

            except Exception as e:
                write_log(f"ERROR during download: {str(e)}")
                write_log(f"Traceback: {traceback.format_exc()}")

        # Return the log file path and data directory
        return {
            "message": "Direct download test completed",
            "log_file": log_file_path,
            "data_dir": data_dir
        }

    except Exception as e:
        # If we can't even write to the log file
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
