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
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

# Suppress Prophet warnings
warnings.filterwarnings('ignore')

# Windows-specific environment configuration for cmdstanpy
if platform.system() == "Windows":
    # Set environment variables to help with cmdstanpy issues
    os.environ['STAN_THREADS'] = '1'  # Use single thread to avoid issues
    os.environ['OMP_NUM_THREADS'] = '1'  # Limit OpenMP threads
    os.environ['MKL_NUM_THREADS'] = '1'  # Limit MKL threads
    os.environ['NUMEXPR_NUM_THREADS'] = '1'  # Limit NumExpr threads

class CrossPlatformProphet:
    """Cross-platform Prophet wrapper with fallback methods"""
    
    def __init__(self):
        self.platform = platform.system()
        self.prophet_available = self._check_prophet_availability()
        self.fallback_model = None
        self._timeout_occurred = False
        
    def _check_prophet_availability(self):
        """Check if Prophet is available and working with enhanced error handling"""
        try:
            from prophet import Prophet
            import signal
            import time
            
            # Test with minimal data
            test_df = pd.DataFrame({
                'ds': pd.date_range('2023-01-01', periods=5, freq='M'),
                'y': [100, 110, 120, 130, 140]
            })
            
            # Set up timeout handler for Windows cmdstanpy issues
            def timeout_handler(signum, frame):
                raise TimeoutError("Prophet initialization timed out")
            
            # Only set timeout on Unix systems (Windows doesn't support signal.SIGALRM)
            if self.platform != "Windows":
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)  # 30 second timeout
            
            try:
                model = Prophet(
                    yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    changepoint_prior_scale=0.1,
                    seasonality_prior_scale=1.0,
                    holidays_prior_scale=0.1
                )
                
                # Try to fit with timeout
                model.fit(test_df)
                
                # Cancel timeout if successful
                if self.platform != "Windows":
                    signal.alarm(0)
                
                return True
                
            except TimeoutError:
                print(f"⚠️ Prophet initialization timed out on {self.platform}")
                return False
            except Exception as e:
                error_msg = str(e)
                if "terminated by signal" in error_msg or "cmdstanpy" in error_msg.lower():
                    print(f"⚠️ Prophet cmdstanpy error on {self.platform}: {error_msg}")
                else:
                    print(f"⚠️ Prophet initialization error on {self.platform}: {error_msg}")
                return False
            finally:
                # Ensure timeout is cancelled
                if self.platform != "Windows":
                    signal.alarm(0)
                    
        except ImportError as e:
            print(f"⚠️ Prophet not installed on {self.platform}: {str(e)}")
            return False
        except Exception as e:
            print(f"⚠️ Prophet availability check failed on {self.platform}: {str(e)}")
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
            print(f"❌ Error creating Prophet model: {str(e)}")
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
            print(f"⚠️ Operation timed out after {timeout_seconds} seconds on Windows")
            return None
        
        if exception[0]:
            raise exception[0]
        
        return result[0]

    def fit_and_predict(self, df, periods=6, **kwargs):
        """Fit model and make predictions with fallback support and enhanced error handling"""
        if not self.prophet_available:
            print("⚠️ Prophet not available, using fallback method")
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
                print(f"🔄 Fitting Prophet model on {self.platform}...")
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
                    print(f"⚠️ Prophet training timed out on {self.platform}, using fallback")
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
                    print(f"✅ Prophet model successfully fitted and predicted on {self.platform}")
                    return result
                except TimeoutError:
                    print(f"⚠️ Prophet training timed out on {self.platform}, using fallback")
                    signal.alarm(0)
                    return self._fallback_fit_and_predict(df, periods)
                finally:
                    signal.alarm(0)
                
        except Exception as e:
            error_msg = str(e)
            if "terminated by signal" in error_msg or "cmdstanpy" in error_msg.lower():
                print(f"⚠️ Prophet cmdstanpy error on {self.platform}: {error_msg}")
                print(f"🔄 Switching to fallback method...")
            else:
                print(f"⚠️ Prophet error on {self.platform}: {error_msg}")
                print(f"🔄 Switching to fallback method...")
            
            return self._fallback_fit_and_predict(df, periods)
    
    def _fallback_fit_and_predict(self, df, periods=6):
        """Fallback prediction method using scikit-learn"""
        try:
            fallback_model = FallbackForecastModel()
            result = fallback_model.fit_and_predict(df, periods)
            result['success'] = False  # Mark as fallback
            return result
        except Exception as e:
            print(f"❌ Fallback model also failed: {str(e)}")
            return {
                'forecast': None,
                'model': None,
                'success': False,
                'error': str(e)
            }


class FallbackForecastModel:
    """Fallback forecasting model using scikit-learn"""
    
    def __init__(self):
        self.model = None
        self.is_fitted = False
        self.trend_model = None
        self.seasonal_model = None
        
    def fit(self, df):
        """Fit the fallback model"""
        try:
            # Prepare features
            df_processed = self._prepare_features(df.copy())
            
            # Create time-based features
            X = df_processed[['time_index', 'month', 'year', 'quarter']].values
            y = df_processed['y'].values
            
            # Use polynomial regression for trend
            self.trend_model = Pipeline([
                ('poly', PolynomialFeatures(degree=2)),
                ('linear', LinearRegression())
            ])
            
            # Use linear regression for seasonal component
            self.seasonal_model = LinearRegression()
            
            # Fit trend model
            self.trend_model.fit(X, y)
            
            # Calculate seasonal component
            trend_predictions = self.trend_model.predict(X)
            seasonal_component = y - trend_predictions
            
            # Fit seasonal model
            X_seasonal = df_processed[['month', 'quarter']].values
            self.seasonal_model.fit(X_seasonal, seasonal_component)
            
            self.is_fitted = True
            return self
            
        except Exception as e:
            print(f"❌ Error fitting fallback model: {str(e)}")
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
            print(f"❌ Error creating future dataframe: {str(e)}")
            raise e
    
    def predict(self, future_df):
        """Make predictions"""
        try:
            if not self.is_fitted:
                raise ValueError("Model must be fitted before making predictions")
            
            # Prepare features
            future_processed = self._prepare_features(future_df.copy())
            
            # Make predictions
            X = future_processed[['time_index', 'month', 'year', 'quarter']].values
            X_seasonal = future_processed[['month', 'quarter']].values
            
            # Predict trend
            trend_predictions = self.trend_model.predict(X)
            
            # Predict seasonal component
            seasonal_predictions = self.seasonal_model.predict(X_seasonal)
            
            # Combine predictions
            yhat = trend_predictions + seasonal_predictions
            
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
            print(f"❌ Error making predictions: {str(e)}")
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
            print(f"❌ Error in fit_and_predict: {str(e)}")
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
        print("✅ Prophet is available and working")
    else:
        print("⚠️ Prophet not available, using fallback methods")
    
    return info
