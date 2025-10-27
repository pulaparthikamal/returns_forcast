#!/usr/bin/env python3
"""
Cross-platform test script for Flask Prophet Model API
Tests functionality on Windows, Ubuntu, and Mac
"""

import requests
import json
import time
import platform
from datetime import datetime, timedelta
import random

# Configuration
FLASK_API_URL = "http://localhost:5000"
ENDPOINT = "/process-data"

def get_platform_info():
    """Get detailed platform information"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }

def generate_test_data(num_records=20):
    """Generate comprehensive test data"""
    
    companies = [
        "TEST COMPANY A",
        "TEST COMPANY B", 
        "TEST COMPANY C",
        "TEST COMPANY D",
        "TEST COMPANY E"
    ]
    
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    
    data = []
    base_date = datetime.now() - timedelta(days=180)  # 6 months of data
    
    for i in range(num_records):
        # Generate random date within last 6 months
        random_days = random.randint(0, 180)
        transaction_date = base_date + timedelta(days=random_days)
        
        record = {
            "DateTransactionJulian": transaction_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "NameAlpha": random.choice(companies),
            "State": random.choice(states),
            "Orig_Inv_Ttl_Prod_Value": round(random.uniform(1000, 10000), 2)
        }
        data.append(record)
    
    return data

def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get(f"{FLASK_API_URL}/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed: {result['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_process_data_endpoint():
    """Test the main process-data endpoint"""
    print("\n🧪 Testing /process-data endpoint...")
    
    # Generate test data
    test_data = generate_test_data(25)
    print(f"📊 Generated {len(test_data)} test records")
    
    # Test with different scenarios
    test_scenarios = [
        {
            "name": "Standard Request",
            "data": test_data,
            "top_n": 3,
            "forecast_months": 3,
            "force_retrain": False
        },
        {
            "name": "Force Retrain",
            "data": test_data,
            "top_n": 2,
            "forecast_months": 2,
            "force_retrain": True
        },
        {
            "name": "Large Dataset",
            "data": generate_test_data(50),
            "top_n": 5,
            "forecast_months": 6,
            "force_retrain": False
        }
    ]
    
    success_count = 0
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        
        payload = {
            "data": scenario['data'],
            "top_n": scenario['top_n'],
            "forecast_months": scenario['forecast_months'],
            "force_retrain": scenario['force_retrain']
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{FLASK_API_URL}{ENDPOINT}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {scenario['name']}: Success ({end_time - start_time:.2f}s)")
                
                # Validate response structure
                if validate_response_structure(result):
                    print(f"   📊 Response structure valid")
                    success_count += 1
                else:
                    print(f"   ⚠️ Response structure invalid")
            else:
                print(f"❌ {scenario['name']}: Failed - {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {scenario['name']}: Request failed - {e}")
    
    return success_count, len(test_scenarios)

def validate_response_structure(result):
    """Validate the response structure"""
    try:
        # Check main structure
        required_keys = ['companyForecasts', 'stateForecasts', 'metadata', 'processing_info']
        for key in required_keys:
            if key not in result:
                print(f"   ❌ Missing key: {key}")
                return False
        
        # Check company forecasts
        company_data = result['companyForecasts']
        if 'forecastData' not in company_data:
            print(f"   ❌ Missing companyForecasts.forecastData")
            return False
        
        if 'kpis' not in company_data:
            print(f"   ❌ Missing companyForecasts.kpis")
            return False
        
        # Check state forecasts
        state_data = result['stateForecasts']
        if 'forecastData' not in state_data:
            print(f"   ❌ Missing stateForecasts.forecastData")
            return False
        
        if 'kpis' not in state_data:
            print(f"   ❌ Missing stateForecasts.kpis")
            return False
        
        # Check processing info
        proc_info = result['processing_info']
        required_proc_keys = ['records_processed', 'csv_path', 'models_retrained', 'processed_at']
        for key in required_proc_keys:
            if key not in proc_info:
                print(f"   ❌ Missing processing_info.{key}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing error handling...")
    
    error_scenarios = [
        {
            "name": "Empty Data",
            "payload": {"data": []},
            "expected_status": 400
        },
        {
            "name": "Invalid Data Format",
            "payload": {"data": [{"invalid": "data"}]},
            "expected_status": [400, 500]
        },
        {
            "name": "Missing Data Field",
            "payload": {"data": [{"DateTransactionJulian": "2024-01-01"}]},
            "expected_status": [400, 500]
        }
    ]
    
    error_handled_count = 0
    
    for scenario in error_scenarios:
        print(f"📋 Testing: {scenario['name']}")
        
        try:
            response = requests.post(
                f"{FLASK_API_URL}{ENDPOINT}",
                json=scenario['payload'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            expected_status = scenario['expected_status']
            if isinstance(expected_status, list):
                if response.status_code in expected_status:
                    print(f"✅ {scenario['name']}: Error handled correctly - {response.status_code}")
                    error_handled_count += 1
                else:
                    print(f"⚠️ {scenario['name']}: Expected {expected_status}, got {response.status_code}")
            else:
                if response.status_code == expected_status:
                    print(f"✅ {scenario['name']}: Error handled correctly - {response.status_code}")
                    error_handled_count += 1
                else:
                    print(f"⚠️ {scenario['name']}: Expected {expected_status}, got {response.status_code}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ {scenario['name']}: Request failed - {e}")
    
    return error_handled_count, len(error_scenarios)

def test_performance():
    """Test API performance"""
    print("\n⚡ Testing performance...")
    
    test_data = generate_test_data(30)
    payload = {
        "data": test_data,
        "top_n": 3,
        "forecast_months": 3,
        "force_retrain": False
    }
    
    times = []
    successful_requests = 0
    
    for i in range(3):  # Run 3 times
        try:
            start_time = time.time()
            response = requests.post(
                f"{FLASK_API_URL}{ENDPOINT}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                times.append(end_time - start_time)
                successful_requests += 1
                print(f"   Request {i+1}: {end_time - start_time:.2f}s")
            else:
                print(f"   Request {i+1}: Failed - {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   Request {i+1}: Error - {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"📊 Performance Results:")
        print(f"   Successful requests: {successful_requests}/3")
        print(f"   Average time: {avg_time:.2f}s")
        print(f"   Min time: {min_time:.2f}s")
        print(f"   Max time: {max_time:.2f}s")
        
        return True
    else:
        print(f"❌ No successful requests for performance testing")
        return False

def main():
    """Main test function"""
    
    print("🚀 Cross-Platform Flask Prophet Model API Test")
    print("=" * 60)
    
    # Display platform information
    platform_info = get_platform_info()
    print(f"🖥️ Platform: {platform_info['system']} {platform_info['release']}")
    print(f"🐍 Python: {platform_info['python_version']}")
    print(f"🏗️ Architecture: {platform_info['machine']}")
    print(f"⚙️ Processor: {platform_info['processor']}")
    print("=" * 60)
    
    # Run tests
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Health endpoint
    total_tests += 1
    if test_health_endpoint():
        passed_tests += 1
    
    # Test 2: Process data endpoint
    total_tests += 1
    success_count, test_count = test_process_data_endpoint()
    if success_count == test_count:
        passed_tests += 1
    
    # Test 3: Error handling
    total_tests += 1
    error_success, error_total = test_error_handling()
    if error_success == error_total:
        passed_tests += 1
    
    # Test 4: Performance
    total_tests += 1
    if test_performance():
        passed_tests += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} test suites passed")
    print(f"📈 Detailed Results:")
    print(f"   Health Check: {'✅' if test_health_endpoint() else '❌'}")
    print(f"   Process Data: {success_count}/{test_count} scenarios passed")
    print(f"   Error Handling: {error_success}/{error_total} scenarios passed")
    print(f"   Performance: {'✅' if test_performance() else '❌'}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! API is working perfectly on this platform.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    print(f"\n🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
