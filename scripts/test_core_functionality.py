#!/usr/bin/env python3
"""
Core functionality test for DriftTracker
This script verifies that all major components work correctly.
"""

import sys
import os
import pickle
from datetime import datetime

# Add backend to path (from scripts directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")
    
    try:
        from drifttracker.drift_calculator import DriftCalculator
                            print("  [OK] DriftCalculator imported")
    except Exception as e:
        print(f"  [ERROR] DriftCalculator import failed: {e}")
        return False
    
    try:
        from drifttracker.data_service import get_ocean_data_file
                            print("  [OK] DataService imported")
    except Exception as e:
        print(f"  [ERROR] DataService import failed: {e}")
        return False
    
    try:
        from drifttracker.utils import calculate_haversine_distance
                            print("  [OK] Utils imported")
    except Exception as e:
        print(f"  [ERROR] Utils import failed: {e}")
        return False
    
    try:
        from cli import app
                            print("  [OK] FastAPI app imported")
    except Exception as e:
        print(f"  [ERROR] FastAPI app import failed: {e}")
        return False
    
    return True

def test_ml_models():
    """Test that ML models can be loaded"""
    print("\nTesting ML models...")
    
    model_files = [
        'backend/ml/model_drift.pkl',
        'backend/ml/model_pattern.pkl',
        'backend/ml/object_encoder.pkl',
        'backend/ml/pattern_encoder.pkl'
    ]
    
    for model_file in model_files:
        if os.path.exists(model_file):
            try:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
                                            print(f"  [OK] {model_file} loads successfully")
            except Exception as e:
                print(f"  [ERROR] {model_file} failed to load: {e}")
                return False
        else:
            print(f"  [ERROR] {model_file} not found")
            return False
    
    return True

def test_drift_calculator():
    """Test drift calculation functionality"""
    print("\nTesting drift calculator...")
    
    try:
        from drifttracker.drift_calculator import DriftCalculator
        calc = DriftCalculator()
        
        # Test distance calculation
        distance = calc.calculate_distance(52.5, 4.2, 52.6, 4.3)
        print(f"  [OK] Distance calculation: {distance:.2f} km")
        
        # Test object properties
        props = calc.get_object_properties('Person_Adult_LifeJacket')
        print(f"  [OK] Object properties: {props}")
        
        # Test drift trajectory (with fallback)
        trajectory = calc.calculate_drift_trajectory(52.5, 4.2, 24, 'Person_Adult_LifeJacket', None)
        print(f"  [OK] Drift trajectory: {len(trajectory)} points calculated")
        
        # Test search pattern recommendation
        pattern, desc = calc.recommend_search_pattern(12, 15, 'Person_Adult_LifeJacket')
        print(f"  [OK] Search pattern: {pattern} - {desc}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] DriftCalculator test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    try:
        from drifttracker.utils import calculate_haversine_distance, validate_coordinates
        
        # Test distance calculation
        distance = calculate_haversine_distance(52.5, 4.2, 52.6, 4.3)
        print(f"  [OK] Haversine distance: {distance:.2f} km")
        
        # Test coordinate validation
        valid = validate_coordinates(52.5, 4.2)
        print(f"  [OK] Coordinate validation: {valid}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Utils test failed: {e}")
        return False

def test_fastapi_endpoints():
    """Test that FastAPI endpoints are configured"""
    print("\nTesting FastAPI endpoints...")
    
    try:
        from cli import app
        
        # Check that expected endpoints exist
        expected_endpoints = ['/', '/app', '/predict', '/debug-data/{lat}/{lon}']
        found_endpoints = []
        
        for route in app.routes:
            if hasattr(route, 'path'):
                found_endpoints.append(route.path)
        
        for endpoint in expected_endpoints:
            if endpoint in found_endpoints:
                                        print(f"  [OK] Endpoint {endpoint} found")
            else:
                                    print(f"  [ERROR] Endpoint {endpoint} missing")
                return False
        
        return True
    except Exception as e:
        print(f"  [ERROR] FastAPI test failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files exist"""
    print("\nTesting frontend files...")
    
    frontend_files = [
        'frontend/html/index.html',
        'frontend/html/login.html',
        'frontend/html/result.html',
        'frontend/src/js/map.js',
        'frontend/src/js/enhancements.js'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"  [OK] {file_path} exists")
        else:
            print(f"  [ERROR] {file_path} missing")
            return False
    
    return True

def test_docker_files():
    """Test that Docker files exist"""
    print("\nTesting Docker files...")
    
    docker_files = ['docker/Dockerfile', 'docker/docker-compose.yml']
    
    for file_path in docker_files:
        if os.path.exists(file_path):
            print(f"  [OK] {file_path} exists")
        else:
            print(f"  [ERROR] {file_path} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("DriftTracker Core Functionality Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_ml_models,
        test_drift_calculator,
        test_utils,
        test_fastapi_endpoints,
        test_frontend_files,
        test_docker_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"  [ERROR] Test failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! DriftTracker is ready for use.")
        return True
    else:
        print("Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 