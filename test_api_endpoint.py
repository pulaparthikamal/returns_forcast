#!/usr/bin/env python3
"""
Test script for the /process-data API endpoint
Tests the cross-platform fixes with sample data
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample data similar to what .NET server would send"""
    # Create sample data for testing
    companies = ['TEST COMPANY A', 'TEST COMPANY B', 'TEST COMPANY C', 'MCKESSON CORPORATION', 'CARDINAL HEALTH']
    states = ['CA', 'TX', 'NY', 'FL', 'IL']
    
    # Generate 6 months of data
    start_date = datetime.now() - timedelta(days=180)
    data = []
    
    for i in range(180):  # 6 months of daily data
        date = start_date + timedelta(days=i)
        
        # Skip weekends (simplified)
        if date.weekday() < 5:
            for company in companies:
                # Generate realistic sales data
                np.random.seed(hash(company + str(i)) % 2**32)
                base_value = np.random.uniform(1000, 5000)
                seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 30)  # Monthly seasonality
                noise = np.random.uniform(0.8, 1.2)
                value = base_value * seasonal_factor * noise
                
                data.append({
                    "DateTransactionJulian": date.strftime('%Y-%m-%dT00:00:00'),
                    "NameAlpha": company,
                    "State": np.random.choice(states),
                    "Orig_Inv_Ttl_Prod_Value": round(value, 2)
                })
    
    return data

def test_api_endpoint():
    """Test the /process-data API endpoint"""
    print("🧪 Testing /process-data API endpoint...")
    
    # Create sample data
    sample_data = create_sample_data()
    print(f"📊 Created {len(sample_data)} sample records")
    
    # Prepare request payload
    payload = {
        "data": sample_data,
        "top_n": 3,
        "forecast_months": 6,
        "force_retrain": True
    }
    
    try:
        # Send request to API
        print("🚀 Sending request to API...")
        response = requests.post(
            'http://localhost:5000/process-data',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API request successful!")
            
            # Check if forecasts were generated
            if 'companyForecasts' in result:
                company_forecasts = result['companyForecasts']
                if 'forecastData' in company_forecasts:
                    forecast_data = company_forecasts['forecastData']
                    print(f"📈 Generated {len(forecast_data)} forecast records")
                    
                    # Show sample forecast data
                    print("\n📊 Sample forecast data:")
                    for i, month_data in enumerate(forecast_data[:3]):
                        print(f"   {month_data['month']}: Historical={month_data.get('isHistorical', False)}")
                        for key, value in month_data.items():
                            if key not in ['month', 'isHistorical', 'isCurrentMonth']:
                                if isinstance(value, (int, float)) and value > 0:
                                    print(f"     {key}: ${value:,.0f}")
                else:
                    print("⚠️ No forecast data in response")
            else:
                print("⚠️ No company forecasts in response")
            
            # Check for errors
            if 'error' in result:
                print(f"❌ API returned error: {result['error']}")
            else:
                print("✅ No errors in API response")
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ API request timed out")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the API server running?")
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🏥 Testing /health endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/health', timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed: {result['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")

def main():
    """Main test function"""
    print("🚀 API ENDPOINT TEST")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test main endpoint
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ API testing completed!")

if __name__ == "__main__":
    main()
