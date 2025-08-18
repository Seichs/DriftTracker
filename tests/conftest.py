"""
Pytest configuration and shared fixtures for DriftTracker tests.

This file contains:
- Global pytest configuration
- Shared fixtures for common test scenarios
- Test data and mock objects
- Environment setup and teardown
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

import pytest
import numpy as np
import pandas as pd
import xarray as xr
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from cli import app
from drifttracker.drift_calculator import DriftCalculator
from drifttracker.data_service import get_ocean_data_file, download_ocean_data
from drifttracker.utils import validate_coordinates, calculate_haversine_distance


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Create a temporary directory for test data files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="drifttracker_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def sample_ocean_data() -> xr.Dataset:
    """Create sample ocean current data for testing."""
    # Create synthetic ocean current data
    times = pd.date_range("2023-01-01", periods=24, freq="H")
    lats = np.linspace(52.0, 53.0, 10)
    lons = np.linspace(3.5, 4.8, 10)
    
    # Create realistic current patterns
    uo = np.random.normal(0.2, 0.1, (len(times), len(lats), len(lons)))
    vo = np.random.normal(0.1, 0.05, (len(times), len(lats), len(lons)))
    
    ds = xr.Dataset(
        data_vars={
            "uo": (["time", "latitude", "longitude"], uo),
            "vo": (["time", "latitude", "longitude"], vo),
        },
        coords={
            "time": times,
            "latitude": lats,
            "longitude": lons,
        },
    )
    
    return ds


@pytest.fixture
def drift_calculator() -> DriftCalculator:
    """Create a DriftCalculator instance for testing."""
    return DriftCalculator()


@pytest.fixture
def test_coordinates() -> Dict[str, float]:
    """Sample coordinates for testing."""
    return {
        "lat": 52.5,
        "lon": 4.2,
        "lat2": 52.51,
        "lon2": 4.21,
    }


@pytest.fixture
def test_object_types() -> list:
    """Sample object types for testing."""
    return [
        "Person_Adult_LifeJacket",
        "Person_Adult_NoLifeJacket",
        "Catamaran",
        "Fishing_Trawler",
        "RHIB",
    ]


@pytest.fixture
def mock_copernicus_response():
    """Mock response from Copernicus Marine API."""
    return Mock(
        file_path="/tmp/test_data.nc",
        status_code=200,
        headers={"content-type": "application/x-netcdf"}
    )


@pytest.fixture
def fastapi_client() -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_drift_request() -> Dict[str, Any]:
    """Sample drift prediction request data."""
    return {
        "lat": 52.5,
        "lon": 4.2,
        "hours": 6,
        "object_type": "Person_Adult_LifeJacket",
        "date": "2023-01-01",
        "time": "12:00",
        "username": "test@example.com",
        "password": "test_password"
    }


@pytest.fixture
def mock_environment_variables():
    """Set up mock environment variables for testing."""
    with patch.dict(os.environ, {
        "COPERNICUS_USERNAME": "test@example.com",
        "COPERNICUS_PASSWORD": "test_password",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true"
    }):
        yield


@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """Large dataset for performance testing."""
    # Create larger datasets for performance tests
    large_times = pd.date_range("2023-01-01", periods=168, freq="H")  # 1 week
    large_lats = np.linspace(51.5, 53.5, 50)
    large_lons = np.linspace(3.0, 5.0, 50)
    
    large_uo = np.random.normal(0.2, 0.1, (len(large_times), len(large_lats), len(large_lons)))
    large_vo = np.random.normal(0.1, 0.05, (len(large_times), len(large_lats), len(large_lons)))
    
    return {
        "times": large_times,
        "lats": large_lats,
        "lons": large_lons,
        "uo": large_uo,
        "vo": large_vo
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def error_test_cases() -> Dict[str, Any]:
    """Test cases that should generate errors."""
    return {
        "invalid_coordinates": {
            "lat": 100.0,  # Invalid latitude
            "lon": 4.2,
            "hours": 6,
            "object_type": "Person_Adult_LifeJacket"
        },
        "negative_hours": {
            "lat": 52.5,
            "lon": 4.2,
            "hours": -1,  # Invalid hours
            "object_type": "Person_Adult_LifeJacket"
        },
        "invalid_object_type": {
            "lat": 52.5,
            "lon": 4.2,
            "hours": 6,
            "object_type": "InvalidObject"  # Invalid object type
        },
        "future_date": {
            "lat": 52.5,
            "lon": 4.2,
            "hours": 6,
            "object_type": "Person_Adult_LifeJacket",
            "date": "2030-01-01",  # Future date
            "time": "12:00"
        }
    }


# Test markers for different test categories
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "data: mark test as a data processing test"
    )
    config.addinivalue_line(
        "markers", "ml: mark test as a machine learning test"
    )
    config.addinivalue_line(
        "markers", "cli: mark test as a command line interface test"
    )
    config.addinivalue_line(
        "markers", "web: mark test as a web interface test"
    ) 