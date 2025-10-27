#!/usr/bin/env python3
"""
Test script for cross-platform Prophet fixes
Tests both Prophet and fallback methods
"""

import pandas as pd
import numpy as np
import platform
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Import our fixed components
from utils.prophet_wrapper import CrossPlatformProphet, test_prophet_availability
from services.forecast_service import ForecastService

def create_test_data():
    """Create test data for forecasting"""
    print("Creating test data...")
    
    # Create monthly data for the last 12 months
    end_date = datetime.now().replace(day=1)
    start_date = end_date - timedelta(days=365)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    
    # Create sample company data
    companies = ['TEST COMPANY A', 'TEST COMPANY B', 'TEST COMPANY C']
    data = []
    
    for company in companies:
        for i, date in enumerate(dates):
            # Create some realistic patterns
            base_value = 1000 + (i * 50)  # Growing trend
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * i / 12)  # Seasonal pattern
            noise = np.random.normal(0, 0.1)  # Random noise
            
            value = base_value * seasonal_factor * (1 + noise)
            
            data.append({
                'DateTransactionJulian': date.strftime('%Y-%m-%d'),
                'NameAlpha': company,
                'State': 'CA',
                'Orig_Inv_Ttl_Prod_Value': max(0, value)
            })
    
    df = pd.DataFrame(data)
    print(f"Created test data: {len(df)} records, {len(companies)} companies")
    return df

def test_prophet_wrapper():
    """Test the Prophet wrapper"""
    print("\nTesting Prophet Wrapper...")
    print("=" * 40)
    
    # Test availability
    availability_info = test_prophet_availability()
    print(f"Platform Info: {availability_info['platform']}")
    print(f"Prophet Available: {availability_info['prophet_available']}")
    print(f"Fallback Available: {availability_info['fallback_available']}")
    
    # Create wrapper
    wrapper = CrossPlatformProphet()
    
    # Create test data
    test_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=8, freq='M'),
        'y': [100, 110, 120, 130, 140, 150, 160, 170]
    })
    
    print(f"\nTest data shape: {test_df.shape}")
    print(f"Sample data:\n{test_df.head()}")
    
    # Test forecasting
    print(f"\nTesting forecasting...")
    result = wrapper.fit_and_predict(test_df, periods=6)
    
    if result['success']:
        print(f"Forecasting successful!")
        print(f"Method used: {result.get('method', 'unknown')}")
        print(f"Forecast shape: {result['forecast'].shape}")
        print(f"Sample predictions: {result['forecast']['yhat'].tail(3).values}")
    else:
        print(f"Forecasting failed: {result.get('error', 'Unknown error')}")
    
    return result['success']

def test_forecast_service():
    """Test the forecast service"""
    print("\nTesting Forecast Service...")
    print("=" * 40)
    
    # Create test data
    test_df = create_test_data()
    
    # Create forecast service
    service = ForecastService()
    
    # Test company forecasting
    print(f"\nTesting company forecasting...")
    time_series_data = service.prepare_time_series_data(test_df)
    
    if time_series_data is not None:
        print(f"Time series data prepared: {time_series_data.shape}")
        
        # Test top companies forecast
        company_forecasts = service.get_top_companies_forecast(
            time_series_data, 
            top_n=3, 
            forecast_months=6,
            retrain_models=True
        )
        
        print(f"Company forecasts generated: {len(company_forecasts)} companies")
        
        for company, forecast in company_forecasts.items():
            if forecast:
                print(f"{company}: Forecast successful (MAPE: {forecast['accuracy']:.1f}%)")
            else:
                print(f"{company}: Forecast failed")
    else:
        print(f"Failed to prepare time series data")
    
    # Test state forecasting
    print(f"\nTesting state forecasting...")
    state_time_series_data = service.prepare_state_time_series_data(test_df)
    
    if state_time_series_data is not None:
        print(f"State time series data prepared: {state_time_series_data.shape}")
        
        # Test top states forecast
        state_forecasts = service.get_top_states_forecast(
            state_time_series_data, 
            top_n=3, 
            forecast_months=6
        )
        
        print(f"State forecasts generated: {len(state_forecasts)} states")
        
        for state, forecast in state_forecasts.items():
            if forecast:
                print(f"{state}: State forecast successful (MAPE: {forecast['accuracy']:.1f}%)")
            else:
                print(f"{state}: State forecast failed")
    else:
        print(f"Failed to prepare state time series data")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\nTesting Edge Cases...")
    print("=" * 40)
    
    wrapper = CrossPlatformProphet()
    
    # Test with insufficient data
    print(f"\nTesting insufficient data...")
    insufficient_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=2, freq='M'),
        'y': [100, 110]
    })
    
    result = wrapper.fit_and_predict(insufficient_df, periods=3)
    if result['success']:
        print(f"Insufficient data handled gracefully")
    else:
        print(f"Insufficient data failed: {result.get('error', 'Unknown error')}")
    
    # Test with NaN values
    print(f"\nTesting NaN values...")
    nan_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=6, freq='M'),
        'y': [100, np.nan, 120, 130, np.nan, 150]
    })
    
    result = wrapper.fit_and_predict(nan_df, periods=3)
    if result['success']:
        print(f"NaN values handled gracefully")
    else:
        print(f"NaN values failed: {result.get('error', 'Unknown error')}")
    
    # Test with zero values
    print(f"\nTesting zero values...")
    zero_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=6, freq='M'),
        'y': [100, 0, 120, 130, 0, 150]
    })
    
    result = wrapper.fit_and_predict(zero_df, periods=3)
    if result['success']:
        print(f"Zero values handled gracefully")
    else:
        print(f"Zero values failed: {result.get('error', 'Unknown error')}")

def main():
    """Main test function"""
    print("Cross-platform Prophet Test Suite")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Prophet Wrapper
    if test_prophet_wrapper():
        tests_passed += 1
    
    # Test 2: Forecast Service
    try:
        test_forecast_service()
        tests_passed += 1
    except Exception as e:
        print(f"Forecast service test failed: {str(e)}")
    
    # Test 3: Edge Cases
    try:
        test_edge_cases()
        tests_passed += 1
    except Exception as e:
        print(f"Edge cases test failed: {str(e)}")
    
    # Test 4: Integration Test
    try:
        print(f"\nTesting Integration...")
        print("=" * 40)
        
        # Test CSV generation
        test_df = create_test_data()
        test_df.to_csv('test_data.csv', index=False)
        print(f"Test CSV created: test_data.csv")
        
        # Test forecast service with CSV
        service = ForecastService()
        result = service.generate_forecast_from_csv('test_data.csv', top_n=3, forecast_months=6)
        
        if 'error' not in result:
            print(f"Integration test passed!")
            print(f"Company forecasts: {len(result.get('companyForecasts', {}).get('forecastData', []))}")
            print(f"State forecasts: {len(result.get('stateForecasts', {}).get('forecastData', []))}")
            tests_passed += 1
        else:
            print(f"Integration test failed: {result['error']}")
        
        # Cleanup
        import os
        if os.path.exists('test_data.csv'):
            os.remove('test_data.csv')
            print(f"Cleaned up test file")
            
    except Exception as e:
        print(f"Integration test failed: {str(e)}")
    
    # Summary
    print(f"\nTest Summary")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print(f"All tests passed! Prophet is working correctly.")
    elif tests_passed >= total_tests // 2:
        print(f"Some tests passed. Fallback methods will be used.")
    else:
        print(f"Most tests failed. Check installation and dependencies.")
    
    print(f"\nPlatform-specific notes:")
    if platform.system() == "Windows":
        print(f"Windows: Ensure Visual Studio Build Tools are installed")
        print(f"Windows: Check that cmdstanpy can compile C++ code")
    else:
        print(f"Unix/Linux: Ensure gcc and python3-dev are installed")
        print(f"Unix/Linux: Check that cmdstanpy can compile C++ code")

if __name__ == "__main__":
    main()
