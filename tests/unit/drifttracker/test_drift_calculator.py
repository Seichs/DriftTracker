"""
Unit tests for DriftCalculator class.

Tests individual methods and functionality of the DriftCalculator class
with mocked dependencies and controlled test scenarios.
"""

import pytest
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from drifttracker.drift_calculator import DriftCalculator


class TestDriftCalculator:
    """Test suite for DriftCalculator class."""

    def test_init(self):
        """Test DriftCalculator initialization."""
        calculator = DriftCalculator()
        assert calculator.earth_radius_km == 6371.0
        assert calculator.meters_per_degree_lat == 111574.0
        assert calculator.meters_per_degree_lon_at_equator == 111320.0

    @pytest.mark.unit
    def test_calculate_distance_valid_coordinates(self, drift_calculator, test_coordinates):
        """Test distance calculation with valid coordinates."""
        distance = drift_calculator.calculate_distance(
            test_coordinates["lat"], test_coordinates["lon"],
            test_coordinates["lat2"], test_coordinates["lon2"]
        )
        
        assert isinstance(distance, float)
        assert distance > 0
        assert distance < 100  # Should be reasonable distance

    @pytest.mark.unit
    def test_calculate_distance_same_point(self, drift_calculator):
        """Test distance calculation for same point."""
        lat, lon = 52.5, 4.2
        distance = drift_calculator.calculate_distance(lat, lon, lat, lon)
        assert distance == 0.0

    @pytest.mark.unit
    def test_calculate_distance_known_values(self, drift_calculator):
        """Test distance calculation with known values."""
        # Test with coordinates that should give predictable results
        lat1, lon1 = 0.0, 0.0
        lat2, lon2 = 1.0, 0.0  # 1 degree north
        
        distance = drift_calculator.calculate_distance(lat1, lon1, lat2, lon2)
        expected_distance = 111.32  # Approximate km per degree at equator
        assert abs(distance - expected_distance) < 1.0

    @pytest.mark.unit
    def test_get_object_properties_person_lifejacket(self, drift_calculator):
        """Test object properties for person with life jacket."""
        props = drift_calculator.get_object_properties("Person_Adult_LifeJacket")
        
        assert props["current_factor"] == 1.0
        assert props["wind_factor"] == 0.01
        assert props["drag_factor"] == 0.8

    @pytest.mark.unit
    def test_get_object_properties_person_no_lifejacket(self, drift_calculator):
        """Test object properties for person without life jacket."""
        props = drift_calculator.get_object_properties("Person_Adult_NoLifeJacket")
        
        assert props["current_factor"] == 1.0
        assert props["wind_factor"] == 0.005
        assert props["drag_factor"] == 1.1

    @pytest.mark.unit
    def test_get_object_properties_boat(self, drift_calculator):
        """Test object properties for boat types."""
        props = drift_calculator.get_object_properties("Catamaran")
        
        assert props["current_factor"] == 1.0
        assert props["wind_factor"] == 0.05
        assert props["drag_factor"] == 0.4

    @pytest.mark.unit
    def test_get_object_properties_unknown_type(self, drift_calculator):
        """Test object properties for unknown object type."""
        props = drift_calculator.get_object_properties("UnknownObject")
        
        assert props["current_factor"] == 1.0
        assert props["wind_factor"] == 0.0
        assert props["drag_factor"] == 1.0

    @pytest.mark.unit
    def test_get_currents_at_position_valid_data(self, drift_calculator, sample_ocean_data):
        """Test getting currents at valid position."""
        lat, lon = 52.5, 4.2
        time = sample_ocean_data.time.values[0]
        
        u_current, v_current = drift_calculator.get_currents_at_position(
            sample_ocean_data, lat, lon, time
        )
        
        assert isinstance(u_current, float)
        assert isinstance(v_current, float)
        assert not np.isnan(u_current)
        assert not np.isnan(v_current)

    @pytest.mark.unit
    def test_get_currents_at_position_no_time(self, drift_calculator, sample_ocean_data):
        """Test getting currents without specifying time."""
        lat, lon = 52.5, 4.2
        
        u_current, v_current = drift_calculator.get_currents_at_position(
            sample_ocean_data, lat, lon
        )
        
        assert isinstance(u_current, float)
        assert isinstance(v_current, float)

    @pytest.mark.unit
    def test_get_currents_at_position_outside_bounds(self, drift_calculator, sample_ocean_data):
        """Test getting currents at position outside data bounds."""
        lat, lon = -90.0, 180.0  # Outside bounds
        
        u_current, v_current = drift_calculator.get_currents_at_position(
            sample_ocean_data, lat, lon
        )
        
        # Should return default values
        assert u_current == 0.0
        assert v_current == 0.0

    @pytest.mark.unit
    def test_calculate_drift_trajectory_basic(self, drift_calculator, sample_ocean_data):
        """Test basic drift trajectory calculation."""
        initial_lat, initial_lon = 52.5, 4.2
        drift_hours = 2.0
        object_type = "Person_Adult_LifeJacket"
        start_time = datetime(2023, 1, 1, 12, 0)
        
        trajectory = drift_calculator.calculate_drift_trajectory(
            initial_lat, initial_lon, drift_hours, object_type,
            sample_ocean_data, start_time
        )
        
        assert isinstance(trajectory, list)
        assert len(trajectory) > 0
        
        # Check first position
        first_pos = trajectory[0]
        assert first_pos["lat"] == initial_lat
        assert first_pos["lon"] == initial_lon
        assert first_pos["hours_elapsed"] == 0.0
        
        # Check last position
        last_pos = trajectory[-1]
        assert last_pos["hours_elapsed"] <= drift_hours

    @pytest.mark.unit
    def test_calculate_drift_trajectory_different_object_types(self, drift_calculator, sample_ocean_data, test_object_types):
        """Test drift trajectory with different object types."""
        initial_lat, initial_lon = 52.5, 4.2
        drift_hours = 1.0
        start_time = datetime(2023, 1, 1, 12, 0)
        
        for object_type in test_object_types:
            trajectory = drift_calculator.calculate_drift_trajectory(
                initial_lat, initial_lon, drift_hours, object_type,
                sample_ocean_data, start_time
            )
            
            assert len(trajectory) > 0
            assert trajectory[0]["lat"] == initial_lat
            assert trajectory[0]["lon"] == initial_lon

    @pytest.mark.unit
    def test_calculate_drift_trajectory_error_handling(self, drift_calculator):
        """Test drift trajectory calculation with invalid data."""
        # Test with None data
        trajectory = drift_calculator.calculate_drift_trajectory(
            52.5, 4.2, 1.0, "Person_Adult_LifeJacket", None
        )
        
        # Should return fallback trajectory
        assert isinstance(trajectory, list)
        assert len(trajectory) > 0

    @pytest.mark.unit
    def test_recommend_search_pattern_short_time(self, drift_calculator):
        """Test search pattern recommendation for short time."""
        pattern, description = drift_calculator.recommend_search_pattern(0.5, 1.0, "Person_Adult_LifeJacket")
        
        assert pattern == "Sector Search"
        assert "recent" in description.lower()

    @pytest.mark.unit
    def test_recommend_search_pattern_medium_time(self, drift_calculator):
        """Test search pattern recommendation for medium time."""
        pattern, description = drift_calculator.recommend_search_pattern(2.0, 5.0, "Person_Adult_LifeJacket")
        
        assert pattern == "Expanding Square"
        assert "moderate" in description.lower()

    @pytest.mark.unit
    def test_recommend_search_pattern_long_time(self, drift_calculator):
        """Test search pattern recommendation for long time."""
        pattern, description = drift_calculator.recommend_search_pattern(10.0, 20.0, "Catamaran")
        
        assert pattern == "Parallel Sweep"
        assert "large" in description.lower()

    @pytest.mark.unit
    def test_recommend_search_pattern_life_jacket(self, drift_calculator):
        """Test search pattern recommendation for person with life jacket."""
        pattern, description = drift_calculator.recommend_search_pattern(12.0, 15.0, "Person_Adult_LifeJacket")
        
        assert pattern == "Parallel Track"
        assert "life jacket" in description.lower()

    @pytest.mark.unit
    def test_fallback_trajectory(self, drift_calculator):
        """Test fallback trajectory calculation."""
        lat, lon = 52.5, 4.2
        hours = 3.0
        object_type = "Person_Adult_LifeJacket"
        
        trajectory = drift_calculator._fallback_trajectory(lat, lon, hours, object_type)
        
        assert isinstance(trajectory, list)
        assert len(trajectory) == int(hours) + 1
        
        # Check first position
        assert trajectory[0]["lat"] == lat
        assert trajectory[0]["lon"] == lon
        assert trajectory[0]["hours_elapsed"] == 0.0
        
        # Check last position
        assert trajectory[-1]["hours_elapsed"] == hours 