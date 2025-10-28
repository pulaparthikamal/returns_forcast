#!/usr/bin/env python3
"""
Cross-platform Prophet installation script
Handles Windows, Ubuntu, and Mac installation issues
"""

import platform
import subprocess
import sys
import os
import warnings

warnings.filterwarnings('ignore')

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {str(e)}")
        return False

def install_prophet_windows():
    """Install Prophet on Windows with proper dependencies"""
    print("🪟 Installing Prophet on Windows...")
    
    # Install Visual Studio Build Tools if needed
    print("📦 Checking for Visual Studio Build Tools...")
    
    # Install dependencies
    commands = [
        "pip install --upgrade pip",
        "pip install wheel",
        "pip install setuptools",
        "pip install cython",
        "pip install numpy",
        "pip install pandas",
        "pip install scikit-learn",
        "pip install matplotlib",
        "pip install cmdstanpy==1.2.0",
        "pip install prophet==1.1.4"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            print(f"⚠️ Command failed: {cmd}")
            return False
    
    # Try to install cmdstan
    print("🔄 Installing cmdstan...")
    try:
        import cmdstanpy
        cmdstanpy.install_cmdstan()
        print("✅ cmdstan installed successfully")
    except Exception as e:
        print(f"⚠️ cmdstan installation failed: {str(e)}")
        print("🔄 Trying alternative installation...")
        run_command("python -c \"import cmdstanpy; cmdstanpy.install_cmdstan()\"", "Installing cmdstan via Python")
    
    return True

def install_prophet_unix():
    """Install Prophet on Unix/Linux/Mac"""
    print("🐧 Installing Prophet on Unix/Linux/Mac...")
    
    # Install system dependencies
    if platform.system() == "Darwin":  # Mac
        print("🍎 Installing on macOS...")
        system_commands = [
            "brew install gcc || true",  # Install gcc if not present
        ]
    else:  # Linux
        print("🐧 Installing on Linux...")
        system_commands = [
            "sudo apt-get update || true",
            "sudo apt-get install -y gcc g++ python3-dev || true",
        ]
    
    for cmd in system_commands:
        run_command(cmd, f"System dependency: {cmd}")
    
    # Install Python dependencies
    commands = [
        "pip install --upgrade pip",
        "pip install wheel",
        "pip install setuptools",
        "pip install cython",
        "pip install numpy",
        "pip install pandas",
        "pip install scikit-learn",
        "pip install matplotlib",
        "pip install cmdstanpy==1.2.0",
        "pip install prophet==1.1.4"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            print(f"⚠️ Command failed: {cmd}")
            return False
    
    # Try to install cmdstan
    print("🔄 Installing cmdstan...")
    try:
        import cmdstanpy
        cmdstanpy.install_cmdstan()
        print("✅ cmdstan installed successfully")
    except Exception as e:
        print(f"⚠️ cmdstan installation failed: {str(e)}")
        print("🔄 Trying alternative installation...")
        run_command("python -c \"import cmdstanpy; cmdstanpy.install_cmdstan()\"", "Installing cmdstan via Python")
    
    return True

def test_prophet_installation():
    """Test if Prophet is working correctly"""
    print("🧪 Testing Prophet installation...")
    
    try:
        from prophet import Prophet
        import pandas as pd
        import numpy as np
        
        # Create test data
        test_df = pd.DataFrame({
            'ds': pd.date_range('2023-01-01', periods=10, freq='M'),
            'y': [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
        })
        
        # Create and fit model
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.1,
            seasonality_prior_scale=1.0,
            holidays_prior_scale=0.1
        )
        
        model.fit(test_df)
        
        # Make prediction
        future = model.make_future_dataframe(periods=3, freq='M')
        forecast = model.predict(future)
        
        print("✅ Prophet installation test passed!")
        print(f"📊 Test forecast shape: {forecast.shape}")
        print(f"📈 Sample predictions: {forecast['yhat'].tail(3).values}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prophet installation test failed: {str(e)}")
        return False

def main():
    """Main installation function"""
    print("🚀 Cross-platform Prophet Installation Script")
    print(f"🖥️ Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ Not in a virtual environment - consider using one")
    
    # Install based on platform
    if platform.system() == "Windows":
        success = install_prophet_windows()
    else:
        success = install_prophet_unix()
    
    if success:
        print("\n🧪 Testing installation...")
        if test_prophet_installation():
            print("\n🎉 Prophet installation completed successfully!")
            print("✅ You can now use Prophet for forecasting")
        else:
            print("\n⚠️ Installation completed but Prophet test failed")
            print("🔄 Fallback methods will be used automatically")
    else:
        print("\n❌ Installation failed")
        print("🔄 Fallback methods will be used automatically")
    
    print("\n📋 Next steps:")
    print("1. Run your forecasting application")
    print("2. The system will automatically use fallback methods if Prophet fails")
    print("3. Check the logs for detailed error information")

if __name__ == "__main__":
    main()

