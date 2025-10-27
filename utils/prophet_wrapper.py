"""
Cross-platform Prophet wrapper with fallback methods
Handles Windows, Ubuntu, and Mac compatibility issues
"""

import pandas as pd
import numpy as np
import platform
import os
import warnings
import threading
import time
import subprocess
import sys
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error

# Suppress Prophet warnings
warnings.filterwarnings('ignore')

# Cross-platform environment configuration for cmdstanpy
if platform.system() == "Windows":
    # Set environment variables to help with cmdstanpy issues
    os.environ['STAN_THREADS'] = '1'  # Use single thread to avoid issues
    os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenMP threads
    os.environ['MKL_NUM_THREADS'] = '1'  # Limit MKL threads
    os.environ['NUMEXPR_NUM_THREADS'] = '1'  # Limit NumExpr threads
    os.environ['TMPDIR'] = os.environ.get('TEMP', 'C:\\temp')  # Set temp directory
else:
    # Unix/Linux/Mac settings
    os.environ['STAN_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'

class CrossPlatformProphet:
    """Cross-platform Prophet wrapper with fallback methods"""
    
    def __init__(self):
        self.platform = platform.system()
        self.prophet_available = False
        self.cmdstanpy_available = False
        self.fallback_model = None
        self._timeout_occurred = False
        self._check_dependencies()
        
    def _check_dependencies(self):
        """Check if Prophet and cmdstanpy are available and working"""
        try:
            # First check if Prophet can be imported
            try:
                from prophet import Prophet
                print(f"Prophet imported successfully on {self.platform}")
            except ImportError as e:
                print(f"Prophet not installed on {self.platform}: {str(e)}")
                self.prophet_available = False
                return
            
            # Check cmdstanpy availability
            try:
                import cmdstanpy
                print(f"cmdstanpy imported successfully on {self.platform}")
                self.cmdstanpy_available = True
            except ImportError as e:
                print(f"cmdstanpy not installed on {self.platform}: {str(e)}")
                self.cmdstanpy_available = False
                self.prophet_available = False
                return
            
            # Try to install cmdstan if not available
            if not self._check_cmdstan_installation():
                print(f"cmdstan not properly installed, attempting installation...")
                if self._install_cmdstan():
                    print(f"cmdstan installed successfully")
                else:
                    print(f"Failed to install cmdstan, using fallback methods")
                    self.prophet_available = False
                    return
            
            # Test Prophet with minimal data
            self.prophet_available = self._test_prophet_functionality()
            
        except Exception as e:
            print(f"Error checking dependencies on {self.platform}: {str(e)}")
            self.prophet_available = False
    
    def _check_cmdstan_installation(self):
        """Check if cmdstan is properly installed"""
        try:
            import cmdstanpy
            # Try to get cmdstan version
            version = cmdstanpy.cmdstan_version()
            print(f"cmdstan version {version} found")
            return True
        except Exception as e:
            print(f"cmdstan installation check failed: {str(e)}")
            return False
    
    def _install_cmdstan(self):
        """Install cmdstan if not available"""
        try:
            import cmdstanpy
            print(f"Installing cmdstan on {self.platform}...")
            cmdstanpy.install_cmdstan()
            return True
        except Exception as e:
            print(f"Failed to install cmdstan: {str(e)}")
            return False
    
    def _test_prophet_functionality(self):
        """Test Prophet with minimal data to ensure it works"""
        try:
            from prophet import Prophet
            
            # Create minimal test data
            test_df = pd.DataFrame({
                'ds': pd.date_range('2023-01-01', periods=5, freq='M'),
                'y': [100, 110, 120, 130, 140]
            })
            
            # Create simple Prophet model
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.1,
                seasonality_prior_scale=1.0,
                holidays_prior_scale=0.1
            )
            
            # Test fit with timeout
            if self.platform == "Windows":
                result = self._windows_timeout_wrapper(
                    lambda: model.fit(test_df), 
                    timeout_seconds=30
                )
                if result is None:
                    print(f"Prophet test timed out on Windows")
                    return False
            else:
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("Prophet test timed out")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
                
                try:
                    model.fit(test_df)
                    signal.alarm(0)
                except TimeoutError:
                    print(f"Prophet test timed out on {self.platform}")
                    signal.alarm(0)
                    return False
                finally:
                    signal.alarm(0)
            
            print(f"Prophet functionality test passed on {self.platform}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "cmdstanpy" in error_msg.lower() or "stan" in error_msg.lower():
                print(f"Prophet cmdstanpy error on {self.platform}: {error_msg}")
            else:
                print(f"Prophet test error on {self.platform}: {error_msg}")
            return False
    
    def create_model(self, **kwargs):
        """Create a Prophet model with platform-specific optimizations"""
        if not self.prophet_available:
            return self._create_fallback_model()
        
        try:
            from prophet import Prophet
            
            # Platform-specific optimizations
            if self.platform == "Windows":
                # Windows-specific settings
                model = Prophet(
                    yearly_seasonality=kwargs.get('yearly_seasonality', False),
                    weekly_seasonality=kwargs.get('weekly_seasonality', False),
                    daily_seasonality=kwargs.get('daily_seasonality', False),
                    changepoint_prior_scale=kwargs.get('changepoint_prior_scale', 0.1),
                    seasonality_prior_scale=kwargs.get('seasonality_prior_scale', 1.0),
                    holidays_prior_scale=kwargs.get('holidays_prior_scale', 0.1),
                    seasonality_mode=kwargs.get('seasonality_mode', 'additive'),
                    interval_width=kwargs.get('interval_width', 0.8)
                )
            else:
                # Linux/Mac settings
                model = Prophet(
                    yearly_seasonality=kwargs.get('yearly_seasonality', True),
                    weekly_seasonality=kwargs.get('weekly_seasonality', False),
                    daily_seasonality=kwargs.get('daily_seasonality', False),
                    changepoint_prior_scale=kwargs.get('changepoint_prior_scale', 0.05),
                    seasonality_prior_scale=kwargs.get('seasonality_prior_scale', 10),
                    holidays_prior_scale=kwargs.get('holidays_prior_scale', 0.05),
                    seasonality_mode=kwargs.get('seasonality_mode', 'multiplicative'),
                    interval_width=kwargs.get('interval_width', 0.8)
                )
            
            return model
            
        except Exception as e:
            print(f"Error creating Prophet model: {str(e)}")
            return self._create_fallback_model()
    
    def _create_fallback_model(self):
        """Create a fallback model when Prophet is not available"""
        return FallbackForecastModel()
    
    def _windows_timeout_wrapper(self, func, timeout_seconds=60):
        """Windows-compatible timeout wrapper using threading"""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            self._timeout_occurred = True
            print(f"Operation timed out after {timeout_seconds} seconds on Windows")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]

    def fit_and_predict(self, df, periods=6, **kwargs):
        """Fit model and make predictions with fallback support and enhanced error handling"""
        if not self.prophet_available:
            print("Prophet not available, using fallback method")
            return self._fallback_fit_and_predict(df, periods)
        
        try:
            from prophet import Prophet
            import signal
            
            def _prophet_operation():
                # Create model
                model = self.create_model(**kwargs)
                
                # Add seasonality if specified
                if kwargs.get('add_monthly_seasonality', True):
                    model.add_seasonality(name='monthly', period=30.5, fourier_order=2)
                
                # Fit model
                print(f"Fitting Prophet model on {self.platform}...")
                model.fit(df)
                
                # Make future dataframe
                future = model.make_future_dataframe(periods=periods, freq='M', include_history=True)
                forecast = model.predict(future)
                
                return {
                    'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
                    'model': model,
                    'success': True
                }
            
            # Use platform-specific timeout mechanism
            if self.platform == "Windows":
                # Use threading-based timeout for Windows
                result = self._windows_timeout_wrapper(_prophet_operation, timeout_seconds=60)
                if result is None:  # Timeout occurred
                    print(f"Prophet training timed out on {self.platform}, using fallback")
                    return self._fallback_fit_and_predict(df, periods)
                return result
            else:
                # Use signal-based timeout for Unix systems
                def timeout_handler(signum, frame):
                    raise TimeoutError("Prophet training timed out")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)  # 60 second timeout for training
                
                try:
                    result = _prophet_operation()
                    signal.alarm(0)  # Cancel timeout
                    print(f"Prophet model successfully fitted and predicted on {self.platform}")
                    return result
                except TimeoutError:
                    print(f"Prophet training timed out on {self.platform}, using fallback")
                    signal.alarm(0)
                    return self._fallback_fit_and_predict(df, periods)
                finally:
                    signal.alarm(0)
                
        except Exception as e:
            error_msg = str(e)
            if "terminated by signal" in error_msg or "cmdstanpy" in error_msg.lower():
                print(f"Prophet cmdstanpy error on {self.platform}: {error_msg}")
                print(f"Switching to fallback method...")
            else:
                print(f"Prophet error on {self.platform}: {error_msg}")
                print(f"Switching to fallback method...")
            
            return self._fallback_fit_and_predict(df, periods)
    
    def _fallback_fit_and_predict(self, df, periods=6):
        """Fallback prediction method using scikit-learn with enhanced error handling"""
        try:
            print(f"Using fallback forecasting method on {self.platform}")
            fallback_model = FallbackForecastModel()
            result = fallback_model.fit_and_predict(df, periods)
            result['success'] = True  # Mark as successful fallback
            result['method'] = 'fallback'
            print(f"Fallback model successfully generated forecast")
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"Fallback model failed: {error_msg}")
            
            # Try even simpler fallback
            try:
                print(f"Trying ultra-simple fallback method...")
                simple_result = self._ultra_simple_fallback(df, periods)
                simple_result['success'] = True
                simple_result['method'] = 'ultra_simple_fallback'
                return simple_result
            except Exception as e2:
                print(f"Ultra-simple fallback also failed: {str(e2)}")
                return {
                    'forecast': None,
                    'model': None,
                    'success': False,
                    'error': f"All fallback methods failed: {error_msg}, {str(e2)}"
                }
    
    def _ultra_simple_fallback(self, df, periods=6):
        """Ultra-simple fallback using basic trend extrapolation"""
        try:
            # Ensure ds is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['ds']):
                df['ds'] = pd.to_datetime(df['ds'])
            
            # Sort by date
            df = df.sort_values('ds').reset_index(drop=True)
            
            # Simple linear trend
            x = np.arange(len(df))
            y = df['y'].values
            
            # Remove any NaN values
            mask = ~np.isnan(y)
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(y_clean) < 2:
                raise ValueError("Not enough valid data points for trend calculation")
            
            # Simple linear regression
            slope = np.polyfit(x_clean, y_clean, 1)[0]
            intercept = np.polyfit(x_clean, y_clean, 1)[1]
            
            # Create future dates
            last_date = df['ds'].max()
            future_dates = pd.date_range(start=last_date, periods=periods+1, freq='M')[1:]
            
            # Create forecast dataframe
            forecast_data = []
            
            # Add historical data
            for i, row in df.iterrows():
                forecast_data.append({
                    'ds': row['ds'],
                    'yhat': row['y'],
                    'yhat_lower': row['y'] * 0.8,
                    'yhat_upper': row['y'] * 1.2
                })
            
            # Add future predictions
            for i, future_date in enumerate(future_dates):
                future_x = len(df) + i
                predicted_y = slope * future_x + intercept
                forecast_data.append({
                    'ds': future_date,
                    'yhat': max(0, predicted_y),  # Ensure non-negative
                    'yhat_lower': max(0, predicted_y * 0.8),
                    'yhat_upper': max(0, predicted_y * 1.2)
                })
            
            forecast_df = pd.DataFrame(forecast_data)
            
            return {
                'forecast': forecast_df,
                'model': None,
                'success': True,
                'method': 'ultra_simple_fallback'
            }
            
        except Exception as e:
            raise Exception(f"Ultra-simple fallback failed: {str(e)}")


class FallbackForecastModel:
    """Fallback forecasting model using scikit-learn with enhanced error handling"""
    
    def __init__(self):
        self.model = None
        self.is_fitted = False
        self.trend_model = None
        self.seasonal_model = None
        self.df = None
        
    def fit(self, df):
        """Fit the fallback model with enhanced error handling"""
        try:
            # Store original data
            self.df = df.copy()
            
            # Prepare features
            df_processed = self._prepare_features(df.copy())
            
            # Check for sufficient data
            if len(df_processed) < 2:
                raise ValueError(f"Insufficient data points: {len(df_processed)} (minimum 2 required)")
            
            # Create time-based features
            X = df_processed[['time_index', 'month', 'year', 'quarter']].values
            y = df_processed['y'].values
            
            # Remove any NaN values
            mask = ~np.isnan(y)
            X_clean = X[mask]
            y_clean = y[mask]
            
            if len(y_clean) < 2:
                raise ValueError("Not enough valid data points after removing NaN values")
            
            # Use simpler models for small datasets
            if len(y_clean) < 5:
                # Use simple linear regression for small datasets
                self.trend_model = LinearRegression()
                self.trend_model.fit(X_clean[:, [0]], y_clean)  # Only use time_index
                self.seasonal_model = None
            else:
                # Use polynomial regression for trend with larger datasets
                self.trend_model = Pipeline([
                    ('poly', PolynomialFeatures(degree=min(2, len(y_clean)-1))),
                    ('linear', LinearRegression())
                ])
                
                # Use linear regression for seasonal component
                self.seasonal_model = LinearRegression()
                
                # Fit trend model
                self.trend_model.fit(X_clean, y_clean)
                
                # Calculate seasonal component
                trend_predictions = self.trend_model.predict(X_clean)
                seasonal_component = y_clean - trend_predictions
                
                # Fit seasonal model
                X_seasonal = X_clean[:, [1, 3]]  # month and quarter
                self.seasonal_model.fit(X_seasonal, seasonal_component)
            
            self.is_fitted = True
            return self
            
        except Exception as e:
            print(f"Error fitting fallback model: {str(e)}")
            raise e
    
    def _prepare_features(self, df):
        """Prepare features for the fallback model"""
        # Ensure ds is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['ds']):
            df['ds'] = pd.to_datetime(df['ds'])
        
        # Create time-based features
        df['time_index'] = range(len(df))
        df['month'] = df['ds'].dt.month
        df['year'] = df['ds'].dt.year
        df['quarter'] = df['ds'].dt.quarter
        
        return df
    
    def make_future_dataframe(self, periods, freq='M', include_history=True):
        """Create future dataframe"""
        try:
            if not self.is_fitted:
                raise ValueError("Model must be fitted before making predictions")
            
            # Get last date from training data
            last_date = self.df['ds'].max()
            
            # Create future dates
            if freq == 'M':
                future_dates = pd.date_range(start=last_date, periods=periods+1, freq='MS')[1:]
            else:
                future_dates = pd.date_range(start=last_date, periods=periods+1, freq=freq)[1:]
            
            future_df = pd.DataFrame({'ds': future_dates})
            future_df = self._prepare_features(future_df)
            
            if include_history:
                return pd.concat([self.df, future_df], ignore_index=True)
            return future_df
            
        except Exception as e:
            print(f"Error creating future dataframe: {str(e)}")
            raise e
    
    def predict(self, future_df):
        """Make predictions with enhanced error handling"""
        try:
            if not self.is_fitted:
                raise ValueError("Model must be fitted before making predictions")
            
            # Prepare features
            future_processed = self._prepare_features(future_df.copy())
            
            # Make predictions
            X = future_processed[['time_index', 'month', 'year', 'quarter']].values
            
            # Predict trend
            if self.seasonal_model is None:
                # Simple linear model
                trend_predictions = self.trend_model.predict(X[:, [0]])  # Only time_index
                seasonal_predictions = np.zeros(len(X))
            else:
                # Complex model with seasonal component
                trend_predictions = self.trend_model.predict(X)
                X_seasonal = X[:, [1, 3]]  # month and quarter
                seasonal_predictions = self.seasonal_model.predict(X_seasonal)
            
            # Combine predictions
            yhat = trend_predictions + seasonal_predictions
            
            # Ensure non-negative predictions
            yhat = np.maximum(yhat, 0)
            
            # Create confidence intervals (simple approach)
            yhat_lower = yhat * 0.8
            yhat_upper = yhat * 1.2
            
            # Create result dataframe
            result_df = future_df.copy()
            result_df['yhat'] = yhat
            result_df['yhat_lower'] = yhat_lower
            result_df['yhat_upper'] = yhat_upper
            
            return result_df
            
        except Exception as e:
            print(f"Error making predictions: {str(e)}")
            raise e
    
    def fit_and_predict(self, df, periods=6):
        """Fit model and make predictions in one step"""
        try:
            # Store original data
            self.df = df.copy()
            
            # Fit model
            self.fit(df)
            
            # Make future dataframe
            future = self.make_future_dataframe(periods, freq='M', include_history=True)
            
            # Make predictions
            forecast = self.predict(future)
            
            return {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
                'model': self,
                'success': True
            }
            
        except Exception as e:
            print(f"Error in fit_and_predict: {str(e)}")
            return {
                'forecast': None,
                'model': None,
                'success': False,
                'error': str(e)
            }


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


def test_prophet_availability():
    """Test Prophet availability and return detailed info"""
    wrapper = CrossPlatformProphet()
    
    info = {
        'platform': get_platform_info(),
        'prophet_available': wrapper.prophet_available,
        'fallback_available': True
    }
    
    if wrapper.prophet_available:
        print("Prophet is available and working")
    else:
        print("Prophet not available, using fallback methods")
    
    return info
