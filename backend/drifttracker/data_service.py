"""
Data service module for ocean data acquisition
"""
import os
import datetime
import logging

# Third-party imports
import copernicusmarine as cm

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("data_service")

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COPERNICUS_USERNAME = "postema45@gmail.com"
COPERNICUS_PASSWORD = "IkHebAids1"


def ensure_data_dir():
    """Ensure the data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def get_ocean_data_file(lat: float, lon: float, 
                        start_time: datetime.datetime, end_time: datetime.datetime, 
                        force_download: bool = False) -> str:
    """
    Check if data file exists for the given parameters, or download if needed.

    Args:
        lat: Latitude (float)
        lon: Longitude (float)
        start_time: Start datetime
        end_time: End datetime
        force_download: Whether to force a new download even if file exists

    Returns:
        str: Path to the data file
    """
    ensure_data_dir()

    # Generate a deterministic filename based on parameters
    lat_rounded = round(lat, 2)
    lon_rounded = round(lon, 2)
    start_str = start_time.strftime("%Y%m%d%H%M") # Added H M for more granularity if needed
    end_str = end_time.strftime("%Y%m%d%H%M")   # Added H M

    filename = f"ocean_data_lat{lat_rounded}_lon{lon_rounded}_{start_str}_{end_str}.nc"
    file_path = os.path.join(DATA_DIR, filename)

    # Check if file already exists and is valid
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0 and not force_download:
        logger.info(f"Using existing data file: {file_path}")
        return file_path

    # If not, download the data
    logger.info(f"Downloading new data file for lat={lat}, lon={lon}, from {start_time} to {end_time}")
    
    try:
        return download_ocean_data(lat, lon, start_time, end_time, output_file=file_path)
    except Exception as e:
        logger.error(f"Failed to download data for {file_path}: {e}")
        # Depending on desired behavior, either re-raise or return None/empty or handle fallback
        raise # Re-raise the exception to be handled by the caller


def download_ocean_data(lat: float, lon: float, 
                        start_time: datetime.datetime, end_time: datetime.datetime, 
                        output_file: str = None) -> str:
    """
    Download ocean current data from Copernicus Marine API.

    Args:
        lat: Latitude (float)
        lon: Longitude (float)
        start_time: Start datetime
        end_time: End datetime
        output_file: Specific output file path (optional)

    Returns:
        str: Path to the downloaded data file
    """
    # cm was imported at the top
    ensure_data_dir() # Ensure data directory exists

    try:
        # Calculate area around the point (e.g., ±0.5 to ±2 degrees, depending on needs)
        # The dataset cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m is daily, so a smaller spatial window might be fine
        # if the drift is not expected to be very large in a single day.
        # For hourly data (if using a different dataset_id), a larger buffer might be needed for longer drifts.
        lat_buffer = 1.0  # Adjusted buffer, can be tuned
        lon_buffer = 1.0  # Adjusted buffer

        min_lat = lat - lat_buffer
        max_lat = lat + lat_buffer
        min_lon = lon - lon_buffer
        max_lon = lon + lon_buffer

        # Create a default filename if not provided
        if output_file is None:
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(DATA_DIR, f"currents_lat{lat:.2f}_lon{lon:.2f}_{timestamp_str}.nc")

        logger.info(f"Downloading ocean data to {output_file}")
        logger.info(f"Area: Lat {min_lat:.2f} to {max_lat:.2f}, Lon {min_lon:.2f} to {max_lon:.2f}")
        logger.info(f"Time: {start_time.strftime('%Y-%m-%dT%H:%M:%S')} to {end_time.strftime('%Y-%m-%dT%H:%M:%S')}")
        
        logger.info(f"Using Copernicus-Marine toolbox version {cm.__version__}")

        # Authenticate (consider if login needs to be called every time or can be cached/checked)
        # cm.login might be better called once at application startup if credentials don't change.
        cm.login(username=COPERNICUS_USERNAME,
                 password=COPERNICUS_PASSWORD,
                 force_overwrite=False) # Avoid overwriting credentials file unnecessarily

        # Define dataset and variables
        # cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m is DAILY average currents.
        # For hourly drift, you need an HOURLY dataset, e.g.,
        # "cmems_mod_glo_phy_anfc_0.083deg_PT1H-m" (Global Ocean Physics Analysis and Forecast - Hourly Mean)
        # Ensure the dataset_id matches the required temporal resolution.
        dataset_id = "cmems_mod_glo_phy_anfc_0.083deg_PT1H-m" # HOURLY data
        variables = ["uo", "vo"] # Eastward and Northward velocity components

        # Download the data using v2 API
        resp = cm.subset(
            dataset_id=dataset_id,
            variables=variables,
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
            start_datetime=start_time.strftime("%Y-%m-%dT%H:%M:%S"), # Ensure ISO format string
            end_datetime=end_time.strftime("%Y-%m-%dT%H:%M:%S"),     # Ensure ISO format string
            output_filename=os.path.basename(output_file), # Pass only filename
            output_directory=os.path.dirname(output_file), # Pass directory
            force_download=True # Force download if file exists, aligns with get_ocean_data_file logic
        )

        # Get file path from response
        # The file_path attribute should give the full path if output_directory and output_filename are used.
        data_file = getattr(resp, "file_path", output_file) 
        # If resp.file_path is None, it might mean the library didn't return it as expected,
        # so falling back to output_file is a safeguard.

        if os.path.exists(data_file) and os.path.getsize(data_file) > 0:
            logger.info(f"Downloaded ocean data to {data_file} ({os.path.getsize(data_file)} bytes)")
            return data_file
        else:
            logger.error(f"Download failed or produced empty file at {data_file}")
            raise Exception(f"Download failed: empty or missing file at {data_file}")

    except Exception as e:
        logger.exception(f"Error downloading ocean data: {e}") # .exception logs stack trace
        raise


if __name__ == "__main__":
    # Simple test function when run directly
    test_lat, test_lon = 43.5, 0.0 # Renamed to avoid conflict
    test_end_time = datetime.datetime.now(datetime.timezone.utc) # Use timezone-aware datetime
    test_start_time = test_end_time - datetime.timedelta(hours=24)

    logger.info(f"Starting direct test for data_service: lat={test_lat}, lon={test_lon}")
    try:
        # Test get_ocean_data_file which internally calls download_ocean_data
        data_file_path = get_ocean_data_file(test_lat, test_lon, test_start_time, test_end_time, force_download=True)
        print(f"Success! Data file: {data_file_path}")
        
        # Optional: Verify content
        # import xarray as xr
        # ds = xr.open_dataset(data_file_path)
        # print(ds)
        # ds.close()

    except Exception as e:
        print(f"Error during test: {e}")
        # logger.exception("Test run failed") # For full traceback in logs
