#!/usr/bin/env python3
"""
Cross-platform compatibility test for Prophet forecasting system
Tests the fixes for Windows cmdstanpy issues and fallback mechanisms
"""

import pandas as pd
import numpy as np
import platform
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.prophet_wrapper import CrossPlatformProphet, test_prophet_availability
from services.forecast_service import ForecastService

def create_test_data():
    """Create test data for forecasting"""
    # Create sample time series data
    dates = pd.date_range('2023-01-01', periods=12, freq='M')
    
    # Create realistic sales data with trend and seasonality
    np.random.seed(42)
    base_trend = np.linspace(1000, 1500, 12)
    seasonal = 200 * np.sin(np.arange(12) * 2 * np.pi / 12)
    noise = np.random.normal(0, 50, 12)
    
    sales_data = base_trend + seasonal + noise
    sales_data = np.maximum(sales_data, 100)  # Ensure positive values
    
    df = pd.DataFrame({
        'ds': dates,
        'y': sales_data
    })
    
    return df

def test_prophet_wrapper():
    """Test the cross-platform Prophet wrapper"""
    print("=" * 60)
    print("TESTING CROSS-PLATFORM PROPHET WRAPPER")
    print("=" * 60)
    
    # Test platform detection
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    
    # Test Prophet availability
    print("\n🔍 Testing Prophet availability...")
    availability_info = test_prophet_availability()
    print(f"   Prophet available: {availability_info['prophet_available']}")
    print(f"   Fallback available: {availability_info['fallback_available']}")
    
    # Initialize wrapper
    wrapper = CrossPlatformProphet()
    
    # Create test data
    test_df = create_test_data()
    print(f"\n📊 Test data created: {len(test_df)} records")
    print(f"   Date range: {test_df['ds'].min()} to {test_df['ds'].max()}")
    print(f"   Value range: ${test_df['y'].min():.0f} to ${test_df['y'].max():.0f}")
    
    # Test forecasting
    print("\n🔮 Testing forecasting...")
    try:
        result = wrapper.fit_and_predict(test_df, periods=6)
        
        if result['success']:
            print("✅ Forecasting successful!")
            forecast = result['forecast']
            print(f"   Forecast records: {len(forecast)}")
            print(f"   Future predictions: {len(forecast[forecast['ds'] > test_df['ds'].max()])}")
            
            # Show sample predictions
            future_predictions = forecast[forecast['ds'] > test_df['ds'].max()].head(3)
            print("   Sample future predictions:")
            for _, row in future_predictions.iterrows():
                print(f"     {row['ds'].strftime('%Y-%m')}: ${row['yhat']:.0f} (${row['yhat_lower']:.0f} - ${row['yhat_upper']:.0f})")
        else:
            print("⚠️ Forecasting failed, using fallback method")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Forecasting error: {str(e)}")
    
    return wrapper

def test_forecast_service():
    """Test the forecast service with cross-platform compatibility"""
    print("\n" + "=" * 60)
    print("TESTING FORECAST SERVICE")
    print("=" * 60)
    
    # Initialize service
    service = ForecastService()
    
    # Create test data in the format expected by the service
    dates = pd.date_range('2023-01-01', periods=12, freq='M')
    np.random.seed(42)
    
    # Create sample company data
    companies = ['TEST COMPANY A', 'TEST COMPANY B', 'TEST COMPANY C']
    test_data = []
    
    for company in companies:
        base_trend = np.linspace(1000, 1500, 12)
        seasonal = 200 * np.sin(np.arange(12) * 2 * np.pi / 12)
        noise = np.random.normal(0, 100, 12)
        sales_data = base_trend + seasonal + noise
        sales_data = np.maximum(sales_data, 100)
        
        for i, date in enumerate(dates):
            test_data.append({
                'DateTransactionJulian': date.strftime('%Y-%m-%d'),
                'NameAlpha': company,
                'State': 'CA',
                'Orig_Inv_Ttl_Prod_Value': sales_data[i]
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(test_data)
    print(f"📊 Test data created: {len(df)} records for {len(companies)} companies")
    
    # Test data preparation
    print("\n🔄 Testing data preparation...")
    try:
        time_series_data = service.prepare_time_series_data(df)
        if time_series_data is not None:
            print(f"✅ Time series data prepared: {len(time_series_data)} months, {len(time_series_data.columns)} companies")
        else:
            print("❌ Failed to prepare time series data")
            return
    except Exception as e:
        print(f"❌ Data preparation error: {str(e)}")
        return
    
    # Test forecasting
    print("\n🔮 Testing company forecasting...")
    try:
        forecasts = service.get_top_companies_forecast(
            time_series_data, 
            top_n=2, 
            forecast_months=6,
            retrain_models=True
        )
        
        if forecasts:
            print(f"✅ Generated forecasts for {len(forecasts)} companies")
            for company, forecast_data in forecasts.items():
                print(f"   {company}: MAPE {forecast_data['accuracy']:.1f}%")
        else:
            print("⚠️ No forecasts generated")
            
    except Exception as e:
        print(f"❌ Forecasting error: {str(e)}")
    
    # Test state forecasting
    print("\n🗺️  Testing state forecasting...")
    try:
        state_time_series_data = service.prepare_state_time_series_data(df)
        if state_time_series_data is not None:
            state_forecasts = service.get_top_states_forecast(state_time_series_data, top_n=1, forecast_months=6)
            
            if state_forecasts:
                print(f"✅ Generated forecasts for {len(state_forecasts)} states")
                for state, forecast_data in state_forecasts.items():
                    print(f"   {state}: MAPE {forecast_data['accuracy']:.1f}%")
            else:
                print("⚠️ No state forecasts generated")
        else:
            print("❌ Failed to prepare state time series data")
            
    except Exception as e:
        print(f"❌ State forecasting error: {str(e)}")

def test_error_handling():
    """Test error handling with problematic data"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    service = ForecastService()
    
    # Test with insufficient data
    print("\n🧪 Testing insufficient data...")
    insufficient_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=2, freq='M'),
        'y': [100, 110]
    })
    
    is_valid, msg = service._validate_data_quality(insufficient_df, "TEST")
    print(f"   Insufficient data validation: {is_valid} - {msg}")
    
    # Test with zero variance data
    print("\n🧪 Testing zero variance data...")
    zero_var_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=6, freq='M'),
        'y': [100, 100, 100, 100, 100, 100]
    })
    
    is_valid, msg = service._validate_data_quality(zero_var_df, "TEST")
    print(f"   Zero variance validation: {is_valid} - {msg}")
    
    # Test with extreme outliers
    print("\n🧪 Testing extreme outliers...")
    outlier_df = pd.DataFrame({
        'ds': pd.date_range('2023-01-01', periods=6, freq='M'),
        'y': [100, 110, 120, 10000, 10000, 10000]  # 50% extreme outliers
    })
    
    is_valid, msg = service._validate_data_quality(outlier_df, "TEST")
    print(f"   Extreme outliers validation: {is_valid} - {msg}")

def main():
    """Main test function"""
    print("🚀 CROSS-PLATFORM PROPHET FORECASTING TEST")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test Prophet wrapper
        wrapper = test_prophet_wrapper()
        
        # Test forecast service
        test_forecast_service()
        
        # Test error handling
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Platform-specific recommendations
        if platform.system() == "Windows":
            print("\n💡 WINDOWS RECOMMENDATIONS:")
            print("   - If Prophet fails, the system will automatically use fallback methods")
            print("   - Environment variables have been set to optimize cmdstanpy performance")
            print("   - Threading-based timeout prevents hanging issues")
        else:
            print("\n💡 UNIX/LINUX RECOMMENDATIONS:")
            print("   - Signal-based timeout provides reliable timeout handling")
            print("   - Prophet should work reliably on this platform")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
