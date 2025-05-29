"""
Data service module for ocean data acquisition
"""
import os
import datetime
import logging
from pathlib import Path

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


def get_ocean_data_file(lat, lon, start_time, end_time, force_download=False):
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
    start_str = start_time.strftime("%Y%m%d")
    end_str = end_time.strftime("%Y%m%d")

    filename = f"ocean_data_lat{lat_rounded}_lon{lon_rounded}_{start_str}_{end_str}.nc"
    file_path = os.path.join(DATA_DIR, filename)

    # Check if file already exists and is valid
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0 and not force_download:
        logger.info(f"Using existing data file: {file_path}")
        return file_path

    # If not, download the data
    logger.info(f"Downloading new data file for lat={lat}, lon={lon}, {start_time} to {end_time}")
    return download_ocean_data(lat, lon, start_time, end_time, file_path)


def download_ocean_data(lat, lon, start_time, end_time, output_file=None):
    """
    Download ocean current data from Copernicus Marine API

    Args:
        lat: Latitude (float)
        lon: Longitude (float)
        start_time: Start datetime
        end_time: End datetime
        output_file: Specific output file path (optional)

    Returns:
        str: Path to the downloaded data file
    """
    try:
        # Calculate area around the point (±2 degrees)
        lat_buffer = 2.0
        lon_buffer = 2.0

        min_lat = lat - lat_buffer
        max_lat = lat + lat_buffer
        min_lon = lon - lon_buffer
        max_lon = lon + lon_buffer

        # Create a default filename if not provided
        if output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(DATA_DIR, f"currents_{timestamp}.nc")

        logger.info(f"Downloading ocean data to {output_file}")
        logger.info(f"Area: Lat {min_lat:.2f} to {max_lat:.2f}, Lon {min_lon:.2f} to {max_lon:.2f}")
        logger.info(f"Time: {start_time} to {end_time}")

        # Import copernicusmarine here so it's only loaded when needed
        import copernicusmarine as cm
        logger.info(f"Using Copernicus-Marine toolbox version {cm.__version__}")

        # Authenticate
        cm.login(username=COPERNICUS_USERNAME,
                 password=COPERNICUS_PASSWORD,
                 force_overwrite=False)

        # Define dataset and variables
        dataset_id = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"
        variables = ["uo", "vo"]

        # Download the data using v2 API
        resp = cm.subset(
            dataset_id=dataset_id,
            variables=variables,
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
            start_datetime=start_time,
            end_datetime=end_time,
            output_filename=output_file,
            force_download=True
        )

        # Get file path from response
        data_file = getattr(resp, "file_path", output_file)

        if os.path.exists(data_file) and os.path.getsize(data_file) > 0:
            logger.info(f"Downloaded ocean data to {data_file} ({os.path.getsize(data_file)} bytes)")
            return data_file
        else:
            logger.error(f"Download failed or produced empty file")
            raise Exception("Download failed: empty or missing file")

    except Exception as e:
        logger.exception(f"Error downloading ocean data: {e}")
        raise


if __name__ == "__main__":
    # Simple test function when run directly
    lat, lon = 43.5, 0.0
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(hours=24)

    try:
        data_file = get_ocean_data_file(lat, lon, start_time, end_time, force_download=True)
        print(f"Success! Data file: {data_file}")
    except Exception as e:
        print(f"Error: {e}")
