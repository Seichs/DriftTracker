"""
Integration tests for drift prediction API endpoints.

Tests the complete API workflow from request to response,
including data validation, processing, and response formatting.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from cli import app


class TestDriftPredictionAPI:
    """Integration tests for drift prediction API."""

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_success(self, fastapi_client, sample_drift_request):
        """Test successful drift prediction request."""
        with patch('cli.download_ocean_data') as mock_download, \
             patch('cli.calculate_drift_path') as mock_calculate:
            
            # Mock successful data download
            mock_download.return_value = "/tmp/test_data.nc"
            
            # Mock drift calculation
            mock_calculate.return_value = [
                {"lat": 52.5, "lon": 4.2, "hours_elapsed": 0.0},
                {"lat": 52.51, "lon": 4.21, "hours_elapsed": 6.0}
            ]
            
            # Make request
            response = fastapi_client.post("/predict", data=sample_drift_request)
            
            # Verify response
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Verify mocks were called
            mock_download.assert_called_once()
            mock_calculate.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_missing_username(self, fastapi_client):
        """Test drift prediction request without username."""
        request_data = {
            "lat": 52.5,
            "lon": 4.2,
            "hours": 6,
            "object_type": "Person_Adult_LifeJacket",
            "date": "2023-01-01",
            "time": "12:00"
            # Missing username
        }
        
        response = fastapi_client.post("/predict", data=request_data)
        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_invalid_coordinates(self, fastapi_client, sample_drift_request):
        """Test drift prediction with invalid coordinates."""
        invalid_request = sample_drift_request.copy()
        invalid_request["lat"] = 100.0  # Invalid latitude
        
        response = fastapi_client.post("/predict", data=invalid_request)
        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_future_date(self, fastapi_client, sample_drift_request):
        """Test drift prediction with future date."""
        future_request = sample_drift_request.copy()
        future_request["date"] = "2030-01-01"
        future_request["time"] = "12:00"
        
        response = fastapi_client.post("/predict", data=future_request)
        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_data_download_failure(self, fastapi_client, sample_drift_request):
        """Test drift prediction when data download fails."""
        with patch('cli.download_ocean_data') as mock_download:
            # Mock download failure
            mock_download.side_effect = Exception("Download failed")
            
            response = fastapi_client.post("/predict", data=sample_drift_request)
            assert response.status_code == 500

    @pytest.mark.integration
    @pytest.mark.api
    def test_predict_endpoint_calculation_failure(self, fastapi_client, sample_drift_request):
        """Test drift prediction when calculation fails."""
        with patch('cli.download_ocean_data') as mock_download, \
             patch('cli.calculate_drift_path') as mock_calculate:
            
            # Mock successful download but failed calculation
            mock_download.return_value = "/tmp/test_data.nc"
            mock_calculate.side_effect = Exception("Calculation failed")
            
            response = fastapi_client.post("/predict", data=sample_drift_request)
            assert response.status_code == 500

    @pytest.mark.integration
    @pytest.mark.api
    def test_root_endpoint(self, fastapi_client):
        """Test root endpoint returns login page."""
        response = fastapi_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "DriftTracker" in response.text

    @pytest.mark.integration
    @pytest.mark.api
    def test_app_endpoint_with_username(self, fastapi_client):
        """Test app endpoint with username parameter."""
        response = fastapi_client.get("/app?username=test@example.com")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "DriftTracker" in response.text

    @pytest.mark.integration
    @pytest.mark.api
    def test_app_endpoint_without_username(self, fastapi_client):
        """Test app endpoint without username redirects to login."""
        response = fastapi_client.get("/app", allow_redirects=False)
        assert response.status_code == 303  # Redirect

    @pytest.mark.integration
    @pytest.mark.api
    def test_login_process_success(self, fastapi_client):
        """Test successful login process."""
        with patch('cli.cm.login') as mock_login:
            # Mock successful login
            mock_login.return_value = None
            
            response = fastapi_client.post("/", data={
                "username": "test@example.com",
                "password": "test_password"
            }, allow_redirects=False)
            
            assert response.status_code == 303  # Redirect to app

    @pytest.mark.integration
    @pytest.mark.api
    def test_login_process_failure(self, fastapi_client):
        """Test failed login process."""
        with patch('cli.cm.login') as mock_login:
            # Mock failed login
            mock_login.side_effect = Exception("Invalid credentials")
            
            response = fastapi_client.post("/", data={
                "username": "test@example.com",
                "password": "wrong_password"
            })
            
            assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.api
    def test_favicon_endpoint(self, fastapi_client):
        """Test favicon endpoint."""
        response = fastapi_client.get("/favicon.ico")
        # Should return either favicon or 404
        assert response.status_code in [200, 404]

    @pytest.mark.integration
    @pytest.mark.api
    def test_debug_data_endpoint(self, fastapi_client):
        """Test debug data endpoint."""
        with patch('cli.download_ocean_data') as mock_download:
            # Mock successful data download
            mock_download.return_value = "/tmp/test_data.nc"
            
            response = fastapi_client.get("/debug-data/52.5/4.2")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "data_file" in data

    @pytest.mark.integration
    @pytest.mark.api
    def test_debug_data_endpoint_failure(self, fastapi_client):
        """Test debug data endpoint with failure."""
        with patch('cli.download_ocean_data') as mock_download:
            # Mock failed data download
            mock_download.side_effect = Exception("Download failed")
            
            response = fastapi_client.get("/debug-data/52.5/4.2")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "error" 