"""
Performance tests for DriftTracker components.

These tests measure the performance characteristics of key functions
and ensure they meet performance requirements.
"""

import pytest
import time
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from unittest.mock import Mock

from drifttracker.drift_calculator import DriftCalculator


class TestDriftCalculatorPerformance:
    """Performance tests for DriftCalculator."""

    @pytest.mark.performance
    def test_calculate_distance_performance(self, drift_calculator, benchmark):
        """Benchmark distance calculation performance."""
        def calculate_multiple_distances():
            for i in range(1000):
                lat1, lon1 = np.random.uniform(-90, 90), np.random.uniform(-180, 180)
                lat2, lon2 = np.random.uniform(-90, 90), np.random.uniform(-180, 180)
                drift_calculator.calculate_distance(lat1, lon1, lat2, lon2)
        
        benchmark(calculate_multiple_distances)

    @pytest.mark.performance
    def test_get_object_properties_performance(self, drift_calculator, benchmark):
        """Benchmark object properties lookup performance."""
        object_types = [
            "Person_Adult_LifeJacket",
            "Person_Adult_NoLifeJacket",
            "Catamaran",
            "Fishing_Trawler",
            "RHIB",
            "SUP_Board",
            "Windsurfer",
            "Kayak"
        ]
        
        def lookup_multiple_properties():
            for _ in range(10000):
                obj_type = np.random.choice(object_types)
                drift_calculator.get_object_properties(obj_type)
        
        benchmark(lookup_multiple_properties)

    @pytest.mark.performance
    def test_get_currents_at_position_performance(self, drift_calculator, performance_test_data):
        """Benchmark current extraction performance."""
        # Create large dataset
        times = performance_test_data["times"]
        lats = performance_test_data["lats"]
        lons = performance_test_data["lons"]
        uo = performance_test_data["uo"]
        vo = performance_test_data["vo"]
        
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
        
        def extract_currents_multiple_positions():
            for _ in range(100):
                lat = np.random.uniform(lats.min(), lats.max())
                lon = np.random.uniform(lons.min(), lons.max())
                time_idx = np.random.randint(0, len(times))
                drift_calculator.get_currents_at_position(ds, lat, lon, times[time_idx])
        
        benchmark(extract_currents_multiple_positions)

    @pytest.mark.performance
    def test_calculate_drift_trajectory_performance(self, drift_calculator, performance_test_data):
        """Benchmark drift trajectory calculation performance."""
        # Create moderate dataset for trajectory calculation
        times = performance_test_data["times"][:24]  # 24 hours
        lats = performance_test_data["lats"][:20]    # 20 lat points
        lons = performance_test_data["lons"][:20]    # 20 lon points
        
        uo = performance_test_data["uo"][:24, :20, :20]
        vo = performance_test_data["vo"][:24, :20, :20]
        
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
        
        def calculate_multiple_trajectories():
            for _ in range(10):
                lat = np.random.uniform(lats.min(), lats.max())
                lon = np.random.uniform(lons.min(), lons.max())
                hours = np.random.uniform(1, 12)
                object_type = np.random.choice([
                    "Person_Adult_LifeJacket",
                    "Catamaran",
                    "Fishing_Trawler"
                ])
                start_time = datetime(2023, 1, 1, 12, 0)
                
                drift_calculator.calculate_drift_trajectory(
                    lat, lon, hours, object_type, ds, start_time
                )
        
        benchmark(calculate_multiple_trajectories)

    @pytest.mark.performance
    def test_recommend_search_pattern_performance(self, drift_calculator, benchmark):
        """Benchmark search pattern recommendation performance."""
        def recommend_multiple_patterns():
            for _ in range(10000):
                hours = np.random.uniform(0.1, 48.0)
                distance = np.random.uniform(0.1, 100.0)
                object_type = np.random.choice([
                    "Person_Adult_LifeJacket",
                    "Catamaran",
                    "Fishing_Trawler"
                ])
                drift_calculator.recommend_search_pattern(hours, distance, object_type)
        
        benchmark(recommend_multiple_patterns)

    @pytest.mark.performance
    def test_memory_usage_trajectory_calculation(self, drift_calculator, performance_test_data):
        """Test memory usage during trajectory calculation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        times = performance_test_data["times"][:48]  # 48 hours
        lats = performance_test_data["lats"][:30]    # 30 lat points
        lons = performance_test_data["lons"][:30]    # 30 lon points
        
        uo = performance_test_data["uo"][:48, :30, :30]
        vo = performance_test_data["vo"][:48, :30, :30]
        
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
        
        # Calculate multiple trajectories
        trajectories = []
        for _ in range(5):
            lat = np.random.uniform(lats.min(), lats.max())
            lon = np.random.uniform(lons.min(), lons.max())
            hours = np.random.uniform(1, 24)
            object_type = np.random.choice([
                "Person_Adult_LifeJacket",
                "Catamaran",
                "Fishing_Trawler"
            ])
            start_time = datetime(2023, 1, 1, 12, 0)
            
            trajectory = drift_calculator.calculate_drift_trajectory(
                lat, lon, hours, object_type, ds, start_time
            )
            trajectories.append(trajectory)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for this test)
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.2f}MB"

    @pytest.mark.performance
    def test_concurrent_trajectory_calculations(self, drift_calculator, performance_test_data):
        """Test performance with concurrent trajectory calculations."""
        import concurrent.futures
        import threading
        
        # Create moderate dataset
        times = performance_test_data["times"][:24]
        lats = performance_test_data["lats"][:15]
        lons = performance_test_data["lons"][:15]
        
        uo = performance_test_data["uo"][:24, :15, :15]
        vo = performance_test_data["vo"][:24, :15, :15]
        
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
        
        def calculate_single_trajectory():
            lat = np.random.uniform(lats.min(), lats.max())
            lon = np.random.uniform(lons.min(), lons.max())
            hours = np.random.uniform(1, 6)
            object_type = np.random.choice([
                "Person_Adult_LifeJacket",
                "Catamaran",
                "Fishing_Trawler"
            ])
            start_time = datetime(2023, 1, 1, 12, 0)
            
            return drift_calculator.calculate_drift_trajectory(
                lat, lon, hours, object_type, ds, start_time
            )
        
        # Test with different numbers of concurrent workers
        for num_workers in [1, 2, 4]:
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(calculate_single_trajectory) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            end_time = time.time()
            duration = end_time - start_time
            
            # All calculations should complete successfully
            assert len(results) == 10
            assert all(isinstance(result, list) for result in results)
            
            print(f"Concurrent calculations with {num_workers} workers: {duration:.2f}s")

    @pytest.mark.performance
    def test_large_dataset_performance(self, drift_calculator):
        """Test performance with very large datasets."""
        # Create a very large dataset (simulating real-world conditions)
        times = pd.date_range("2023-01-01", periods=168, freq="H")  # 1 week
        lats = np.linspace(-35, -33, 100)  # 100 lat points
        lons = np.linspace(18, 20, 100)    # 100 lon points
        
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
        
        start_time = time.time()
        
        # Calculate trajectory with large dataset
        trajectory = drift_calculator.calculate_drift_trajectory(
            52.5, 4.2, 24.0, "Person_Adult_LifeJacket", ds,
            datetime(2023, 1, 1, 12, 0)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (< 30 seconds)
        assert duration < 30, f"Large dataset calculation too slow: {duration:.2f}s"
        assert len(trajectory) > 0 