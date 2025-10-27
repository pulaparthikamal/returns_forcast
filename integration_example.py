#!/usr/bin/env python3
"""
Integration Example for Flask Prophet Model API

This script demonstrates how to integrate with the Flask API from a .NET server
or any other client application.
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Configuration
FLASK_API_URL = "http://localhost:5000"
ENDPOINT = "/process-data"

def generate_sample_data(num_records=100):
    """Generate sample data for testing the API"""
    
    companies = [
        "AMERISOURCEBERGEN DRUG CORP",
        "CARDINAL HEALTH",
        "MCKESSON CORPORATION",
        "WALMART PHARMACY",
        "CVS HEALTH",
        "WALGREENS",
        "RITE AID",
        "KROGER PHARMACY"
    ]
    
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    
    data = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_records):
        # Generate random date within last year
        random_days = random.randint(0, 365)
        transaction_date = base_date + timedelta(days=random_days)
        
        record = {
            "DateTransactionJulian": transaction_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "NameAlpha": random.choice(companies),
            "State": random.choice(states),
            "Orig_Inv_Ttl_Prod_Value": round(random.uniform(100, 5000), 2)
        }
        data.append(record)
    
    return data

def test_api_health():
    """Test if the API is running and healthy"""
    try:
        response = requests.get(f"{FLASK_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def test_process_data_endpoint():
    """Test the main process-data endpoint"""
    
    print("\n🧪 Testing /process-data endpoint...")
    
    # Generate sample data
    sample_data = generate_sample_data(50)
    print(f"📊 Generated {len(sample_data)} sample records")
    
    # Prepare payload
    payload = {
        "data": sample_data,
        "top_n": 5,
        "forecast_months": 6,
        "force_retrain": False
    }
    
    try:
        # Make API request
        print("🚀 Sending request to Flask API...")
        response = requests.post(
            f"{FLASK_API_URL}{ENDPOINT}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful!")
            
            # Display results summary
            if "companyForecasts" in result:
                company_data = result["companyForecasts"]
                print(f"\n📈 Company Forecasts:")
                print(f"   - Total companies: {company_data['metadata']['totalCompanies']}")
                print(f"   - Forecast months: {company_data['metadata']['timeline']['forecastMonths']}")
                print(f"   - Data points: {len(company_data['forecastData'])}")
                
                # Display KPIs
                if "kpis" in company_data:
                    kpis = company_data["kpis"]
                    print(f"\n📊 Key Performance Indicators:")
                    print(f"   - Previous Month Total: ${kpis['previousMonthTotal']:,.0f}")
                    print(f"   - Current Month Predicted: ${kpis['currentMonthPredicted']:,.0f}")
                    print(f"   - Growth Rate: {kpis['growthCurrentVsPrevious']:.1f}%")
                    print(f"   - 6-Month Forecast: ${kpis['total6MonthForecast']:,.0f}")
            
            # Display processing info
            if "processing_info" in result:
                proc_info = result["processing_info"]
                print(f"\n⚙️ Processing Information:")
                print(f"   - Records processed: {proc_info['records_processed']}")
                print(f"   - Models retrained: {proc_info['models_retrained']}")
                print(f"   - CSV path: {proc_info['csv_path']}")
            
            return True
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_force_retrain():
    """Test the force retrain functionality"""
    
    print("\n🔄 Testing force retrain functionality...")
    
    # Generate sample data
    sample_data = generate_sample_data(30)
    
    # Prepare payload with force_retrain=True
    payload = {
        "data": sample_data,
        "top_n": 3,
        "forecast_months": 3,
        "force_retrain": True
    }
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}{ENDPOINT}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("processing_info", {}).get("models_retrained", False):
                print("✅ Force retrain successful - models were retrained")
            else:
                print("⚠️ Force retrain requested but models were not retrained")
            return True
        else:
            print(f"❌ Force retrain test failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Force retrain test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid data"""
    
    print("\n🚨 Testing error handling...")
    
    # Test with empty data
    payload = {"data": []}
    
    try:
        response = requests.post(
            f"{FLASK_API_URL}{ENDPOINT}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Empty data error handled correctly")
        else:
            print(f"⚠️ Expected 400 error, got {response.status_code}")
        
        # Test with missing required fields
        invalid_payload = {
            "data": [{"invalid_field": "test"}]
        }
        
        response = requests.post(
            f"{FLASK_API_URL}{ENDPOINT}",
            json=invalid_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [400, 500]:
            print("✅ Invalid data error handled correctly")
        else:
            print(f"⚠️ Expected error for invalid data, got {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Flask Prophet Model API Integration Test")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("\n❌ API is not available. Please start the Flask server first.")
        print("Run: python app.py")
        return
    
    # Test main functionality
    success_count = 0
    total_tests = 4
    
    if test_process_data_endpoint():
        success_count += 1
    
    if test_force_retrain():
        success_count += 1
    
    if test_error_handling():
        success_count += 1
    
    # Test CSV endpoint
    try:
        print("\n📁 Testing CSV endpoint...")
        response = requests.get(f"{FLASK_API_URL}/forecast/csv", timeout=30)
        if response.status_code == 200:
            print("✅ CSV endpoint working")
            success_count += 1
        else:
            print(f"❌ CSV endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ CSV endpoint test failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! API is ready for integration.")
    else:
        print("⚠️ Some tests failed. Please check the API configuration.")

if __name__ == "__main__":
    main()
