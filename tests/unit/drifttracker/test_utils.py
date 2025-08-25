"""
Unit tests for utility functions.

Tests individual utility functions with various input scenarios
and edge cases.
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from drifttracker.utils import (
    validate_coordinates,
    calculate_haversine_distance,
    format_coordinates,
    calculate_bearing,
    create_bounding_box,
    parse_datetime_string,
    safe_float_conversion,
    safe_int_conversion,
    ensure_directory_exists,
    format_duration,
    interpolate_positions,
    knots_to_ms,
    ms_to_knots,
    nautical_miles_to_km,
    km_to_nautical_miles
)


class TestCoordinateValidation:
    """Test coordinate validation functions."""

    @pytest.mark.unit
    def test_validate_coordinates_valid(self):
        """Test valid coordinate validation."""
        assert validate_coordinates(0.0, 0.0) is True
        assert validate_coordinates(90.0, 180.0) is True
        assert validate_coordinates(-90.0, -180.0) is True
        assert validate_coordinates(45.5, -120.3) is True

    @pytest.mark.unit
    def test_validate_coordinates_invalid_latitude(self):
        """Test invalid latitude validation."""
        assert validate_coordinates(91.0, 0.0) is False
        assert validate_coordinates(-91.0, 0.0) is False
        assert validate_coordinates(100.0, 0.0) is False

    @pytest.mark.unit
    def test_validate_coordinates_invalid_longitude(self):
        """Test invalid longitude validation."""
        assert validate_coordinates(0.0, 181.0) is False
        assert validate_coordinates(0.0, -181.0) is False
        assert validate_coordinates(0.0, 200.0) is False

    @pytest.mark.unit
    def test_validate_coordinates_invalid_types(self):
        """Test coordinate validation with invalid types."""
        assert validate_coordinates("invalid", 0.0) is False
        assert validate_coordinates(0.0, "invalid") is False
        assert validate_coordinates(None, 0.0) is False
        assert validate_coordinates(0.0, None) is False


class TestDistanceCalculations:
    """Test distance calculation functions."""

    @pytest.mark.unit
    def test_calculate_haversine_distance_same_point(self):
        """Test distance calculation for same point."""
        distance = calculate_haversine_distance(0.0, 0.0, 0.0, 0.0)
        assert distance == 0.0

    @pytest.mark.unit
    def test_calculate_haversine_distance_known_values(self):
        """Test distance calculation with known values."""
        # Distance between two points approximately 1 degree apart
        distance = calculate_haversine_distance(0.0, 0.0, 1.0, 0.0)
        assert abs(distance - 111.32) < 1.0  # Approximate km per degree

    @pytest.mark.unit
    def test_calculate_haversine_distance_opposite_hemispheres(self):
        """Test distance calculation across hemispheres."""
        distance = calculate_haversine_distance(45.0, -180.0, 45.0, 180.0)
        assert distance > 0
        assert distance < 10000  # Reasonable maximum

    @pytest.mark.unit
    def test_calculate_bearing_north(self):
        """Test bearing calculation for north direction."""
        bearing = calculate_bearing(0.0, 0.0, 1.0, 0.0)
        assert abs(bearing - 0.0) < 1.0  # North

    @pytest.mark.unit
    def test_calculate_bearing_east(self):
        """Test bearing calculation for east direction."""
        bearing = calculate_bearing(0.0, 0.0, 0.0, 1.0)
        assert abs(bearing - 90.0) < 1.0  # East

    @pytest.mark.unit
    def test_calculate_bearing_south(self):
        """Test bearing calculation for south direction."""
        bearing = calculate_bearing(1.0, 0.0, 0.0, 0.0)
        assert abs(bearing - 180.0) < 1.0  # South

    @pytest.mark.unit
    def test_calculate_bearing_west(self):
        """Test bearing calculation for west direction."""
        bearing = calculate_bearing(0.0, 1.0, 0.0, 0.0)
        assert abs(bearing - 270.0) < 1.0  # West


class TestCoordinateFormatting:
    """Test coordinate formatting functions."""

    @pytest.mark.unit
    def test_format_coordinates_positive(self):
        """Test coordinate formatting for positive values."""
        formatted = format_coordinates(45.123456, 120.654321)
        assert "45.123456°N" in formatted
        assert "120.654321°E" in formatted

    @pytest.mark.unit
    def test_format_coordinates_negative(self):
        """Test coordinate formatting for negative values."""
        formatted = format_coordinates(-45.123456, -120.654321)
        assert "45.123456°S" in formatted
        assert "120.654321°W" in formatted

    @pytest.mark.unit
    def test_format_coordinates_zero(self):
        """Test coordinate formatting for zero values."""
        formatted = format_coordinates(0.0, 0.0)
        assert "0.000000°N" in formatted
        assert "0.000000°E" in formatted

    @pytest.mark.unit
    def test_format_coordinates_custom_precision(self):
        """Test coordinate formatting with custom precision."""
        formatted = format_coordinates(45.123456, 120.654321, precision=2)
        assert "45.12°N" in formatted
        assert "120.65°E" in formatted


class TestBoundingBox:
    """Test bounding box creation."""

    @pytest.mark.unit
    def test_create_bounding_box_small_radius(self):
        """Test bounding box creation with small radius."""
        bbox = create_bounding_box(0.0, 0.0, 1.0)  # 1km radius
        
        assert bbox["min_lat"] < 0.0
        assert bbox["max_lat"] > 0.0
        assert bbox["min_lon"] < 0.0
        assert bbox["max_lon"] > 0.0

    @pytest.mark.unit
    def test_create_bounding_box_large_radius(self):
        """Test bounding box creation with large radius."""
        bbox = create_bounding_box(45.0, -120.0, 100.0)  # 100km radius
        
        assert bbox["min_lat"] < 45.0
        assert bbox["max_lat"] > 45.0
        assert bbox["min_lon"] < -120.0
        assert bbox["max_lon"] > -120.0

    @pytest.mark.unit
    def test_create_bounding_box_polar_regions(self):
        """Test bounding box creation in polar regions."""
        bbox = create_bounding_box(80.0, 0.0, 10.0)  # Near North Pole
        
        assert bbox["min_lat"] < 80.0
        assert bbox["max_lat"] > 80.0
        # Longitude bounds should be adjusted for high latitudes


class TestDateTimeParsing:
    """Test datetime string parsing."""

    @pytest.mark.unit
    def test_parse_datetime_string_iso_format(self):
        """Test parsing ISO format datetime strings."""
        dt = parse_datetime_string("2023-01-01T12:00:00")
        assert dt is not None
        assert dt.year == 2023
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 12

    @pytest.mark.unit
    def test_parse_datetime_string_date_only(self):
        """Test parsing date-only strings."""
        dt = parse_datetime_string("2023-01-01")
        assert dt is not None
        assert dt.year == 2023
        assert dt.month == 1
        assert dt.day == 1

    @pytest.mark.unit
    def test_parse_datetime_string_custom_format(self):
        """Test parsing custom format datetime strings."""
        dt = parse_datetime_string("2023-01-01 12:00:00")
        assert dt is not None
        assert dt.year == 2023
        assert dt.hour == 12

    @pytest.mark.unit
    def test_parse_datetime_string_invalid(self):
        """Test parsing invalid datetime strings."""
        dt = parse_datetime_string("invalid")
        assert dt is None

    @pytest.mark.unit
    def test_parse_datetime_string_none(self):
        """Test parsing None value."""
        dt = parse_datetime_string(None)
        assert dt is None


class TestSafeConversions:
    """Test safe type conversion functions."""

    @pytest.mark.unit
    def test_safe_float_conversion_valid(self):
        """Test safe float conversion with valid values."""
        assert safe_float_conversion("123.45") == 123.45
        assert safe_float_conversion(123.45) == 123.45
        assert safe_float_conversion(123) == 123.0

    @pytest.mark.unit
    def test_safe_float_conversion_invalid(self):
        """Test safe float conversion with invalid values."""
        assert safe_float_conversion("invalid") == 0.0
        assert safe_float_conversion(None) == 0.0
        assert safe_float_conversion("invalid", default=42.0) == 42.0

    @pytest.mark.unit
    def test_safe_int_conversion_valid(self):
        """Test safe int conversion with valid values."""
        assert safe_int_conversion("123") == 123
        assert safe_int_conversion(123.45) == 123
        assert safe_int_conversion(123) == 123

    @pytest.mark.unit
    def test_safe_int_conversion_invalid(self):
        """Test safe int conversion with invalid values."""
        assert safe_int_conversion("invalid") == 0
        assert safe_int_conversion(None) == 0
        assert safe_int_conversion("invalid", default=42) == 42


class TestFileOperations:
    """Test file and directory operations."""

    @pytest.mark.unit
    def test_ensure_directory_exists_new(self, tmp_path):
        """Test creating new directory."""
        new_dir = tmp_path / "new_directory"
        result = ensure_directory_exists(str(new_dir))
        assert new_dir.exists()
        assert result == str(new_dir.absolute())

    @pytest.mark.unit
    def test_ensure_directory_exists_existing(self, tmp_path):
        """Test with existing directory."""
        existing_dir = tmp_path / "existing_directory"
        existing_dir.mkdir()
        
        result = ensure_directory_exists(str(existing_dir))
        assert existing_dir.exists()
        assert result == str(existing_dir.absolute())


class TestDurationFormatting:
    """Test duration formatting functions."""

    @pytest.mark.unit
    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        assert "seconds" in format_duration(30.0)
        assert "30.0" in format_duration(30.0)

    @pytest.mark.unit
    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        assert "minutes" in format_duration(1800.0)  # 30 minutes in seconds
        assert "30.0" in format_duration(1800.0)

    @pytest.mark.unit
    def test_format_duration_hours(self):
        """Test duration formatting for hours."""
        assert "hours" in format_duration(3600.0)  # 1 hour in seconds
        assert "1.0" in format_duration(3600.0)

    @pytest.mark.unit
    def test_format_duration_days(self):
        """Test duration formatting for days."""
        assert "days" in format_duration(172800.0)  # 2 days in seconds
        assert "2.0" in format_duration(172800.0)


class TestPositionInterpolation:
    """Test position interpolation functions."""

    @pytest.mark.unit
    def test_interpolate_positions_valid(self):
        """Test position interpolation with valid data."""
        positions = [
            {"lat": 0.0, "lon": 0.0, "hours_elapsed": 0.0},
            {"lat": 1.0, "lon": 1.0, "hours_elapsed": 2.0}
        ]
        
        interpolated = interpolate_positions(positions, 1.0)
        assert interpolated is not None
        assert interpolated["lat"] == 0.5
        assert interpolated["lon"] == 0.5
        assert interpolated["hours_elapsed"] == 1.0

    @pytest.mark.unit
    def test_interpolate_positions_empty(self):
        """Test position interpolation with empty data."""
        interpolated = interpolate_positions([], 1.0)
        assert interpolated is None

    @pytest.mark.unit
    def test_interpolate_positions_single_point(self):
        """Test position interpolation with single point."""
        positions = [{"lat": 0.0, "lon": 0.0, "hours_elapsed": 0.0}]
        interpolated = interpolate_positions(positions, 1.0)
        assert interpolated is None


class TestUnitConversions:
    """Test unit conversion functions."""

    @pytest.mark.unit
    def test_knots_to_ms(self):
        """Test knots to meters per second conversion."""
        ms = knots_to_ms(10.0)
        expected = 10.0 * 0.514444
        assert abs(ms - expected) < 0.001

    @pytest.mark.unit
    def test_ms_to_knots(self):
        """Test meters per second to knots conversion."""
        knots = ms_to_knots(5.14444)
        expected = 5.14444 * 1.944012
        assert abs(knots - expected) < 0.001

    @pytest.mark.unit
    def test_nautical_miles_to_km(self):
        """Test nautical miles to kilometers conversion."""
        km = nautical_miles_to_km(1.0)
        assert abs(km - 1.852) < 0.001

    @pytest.mark.unit
    def test_km_to_nautical_miles(self):
        """Test kilometers to nautical miles conversion."""
        nm = km_to_nautical_miles(1.852)
        assert abs(nm - 1.0) < 0.001 