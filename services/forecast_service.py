import pandas as pd
import numpy as np
from prophet import Prophet
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ForecastService:
    def __init__(self):
        self.time_series_data = None
        
    def prepare_time_series_data(self, df):
        """
        Convert raw data to monthly time series for each company
        """
        try:
            # Convert dates
            df['DateTransactionJulian'] = pd.to_datetime(df['DateTransactionJulian'], format='%Y-%m-%d')
            df['year_month'] = df['DateTransactionJulian'].dt.to_period('M')

            # Aggregate by company and month
            monthly_returns = df.groupby(['NameAlpha', 'year_month'])['Orig_Inv_Ttl_Prod_Value'].sum().reset_index()

            # Convert to proper time series format
            monthly_returns['year_month'] = monthly_returns['year_month'].dt.to_timestamp()
            monthly_pivot = monthly_returns.pivot_table(
                index='year_month',
                columns='NameAlpha',
                values='Orig_Inv_Ttl_Prod_Value',
                fill_value=0
            )

            return monthly_pivot
        except Exception as e:
            print(f"Error preparing time series data: {e}")
            return None

    def prepare_state_time_series_data(self, df):
        """
        Convert raw data to monthly time series for each state
        """
        try:
            # Convert dates
            df['DateTransactionJulian'] = pd.to_datetime(df['DateTransactionJulian'], format='%Y-%m-%d')
            df['year_month'] = df['DateTransactionJulian'].dt.to_period('M')

            # Aggregate by state and month
            monthly_returns = df.groupby(['State', 'year_month'])['Orig_Inv_Ttl_Prod_Value'].sum().reset_index()

            # Convert to proper time series format
            monthly_returns['year_month'] = monthly_returns['year_month'].dt.to_timestamp()
            monthly_pivot = monthly_returns.pivot_table(
                index='year_month',
                columns='State',
                values='Orig_Inv_Ttl_Prod_Value',
                fill_value=0
            )

            return monthly_pivot
        except Exception as e:
            print(f"Error preparing state time series data: {e}")
            return None

    def forecast_company_returns(self, company_series, company_name, periods=6):
        """
        Forecast future returns for a single company using Prophet with confidence intervals
        """
        try:
            # Prepare data for Prophet
            prophet_df = company_series.reset_index()
            prophet_df.columns = ['ds', 'y']
            prophet_df = prophet_df[prophet_df['y'] > 0]  # Remove zero values

            if len(prophet_df) < 4:  # Need minimum data points
                print(f"⚠️ Insufficient data for {company_name}, skipping...")
                return None

            # Initialize and fit model with optimized parameters
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
                holidays_prior_scale=0.05,
                seasonality_mode='multiplicative'
            )

            # Add monthly seasonality
            model.add_seasonality(name='monthly', period=30.5, fourier_order=3)

            model.fit(prophet_df)

            # Make future dataframe
            future = model.make_future_dataframe(periods=periods, freq='M', include_history=True)
            forecast = model.predict(future)

            # Calculate accuracy metrics on historical data
            historical_forecast = forecast[forecast['ds'].isin(prophet_df['ds'])]
            mape = np.mean(np.abs((historical_forecast['yhat'] - prophet_df['y']) / prophet_df['y'])) * 100

            print(f"✅ {company_name}: Forecast created (MAPE: {mape:.1f}%)")

            return {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
                'historical': prophet_df,
                'accuracy': mape
            }

        except Exception as e:
            print(f"❌ Error forecasting {company_name}: {str(e)}")
            return None

    def get_top_companies_forecast(self, time_series_data, top_n=5, forecast_months=6):
        """
        Get forecasts for top N companies with highest average returns
        """
        try:
            # Identify top companies by historical volume (last 6 months)
            recent_data = time_series_data.tail(6)
            company_totals = recent_data.sum().sort_values(ascending=False)
            top_companies = company_totals.head(top_n).index.tolist()

            print("🏆 Top Companies Selected for Forecasting:")
            for i, company in enumerate(top_companies, 1):
                print(f"  {i}. {company} (Recent volume: ${company_totals[company]:,.0f})")

            forecasts = {}

            for company in top_companies:
                company_data = time_series_data[company]
                forecast_result = self.forecast_company_returns(company_data, company, periods=forecast_months)

                if forecast_result is not None:
                    forecasts[company] = forecast_result

            return forecasts
        except Exception as e:
            print(f"Error getting top companies forecast: {e}")
            return {}

    def forecast_state_returns(self, state_series, state_name, periods=6):
        """
        Forecast future returns for a single state using Prophet with confidence intervals
        """
        try:
            # Prepare data for Prophet
            prophet_df = state_series.reset_index()
            prophet_df.columns = ['ds', 'y']
            prophet_df = prophet_df[prophet_df['y'] > 0]  # Remove zero values

            if len(prophet_df) < 4:  # Need minimum data points
                print(f"⚠️ Insufficient data for {state_name}, skipping...")
                return None

            # Initialize and fit model with optimized parameters
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
                holidays_prior_scale=0.05,
                seasonality_mode='multiplicative'
            )

            # Add monthly seasonality
            model.add_seasonality(name='monthly', period=30.5, fourier_order=3)

            model.fit(prophet_df)

            # Make future dataframe
            future = model.make_future_dataframe(periods=periods, freq='M', include_history=True)
            forecast = model.predict(future)

            # Calculate accuracy metrics on historical data
            historical_forecast = forecast[forecast['ds'].isin(prophet_df['ds'])]
            mape = np.mean(np.abs((historical_forecast['yhat'] - prophet_df['y']) / prophet_df['y'])) * 100

            print(f"✅ {state_name}: State forecast created (MAPE: {mape:.1f}%)")

            return {
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
                'historical': prophet_df,
                'accuracy': mape
            }

        except Exception as e:
            print(f"❌ Error forecasting {state_name}: {str(e)}")
            return None

    def get_top_states_forecast(self, state_time_series_data, top_n=5, forecast_months=6):
        """
        Get forecasts for top N states with highest average returns
        """
        try:
            # Identify top states by historical volume (last 6 months)
            recent_data = state_time_series_data.tail(6)
            state_totals = recent_data.sum().sort_values(ascending=False)
            top_states = state_totals.head(top_n).index.tolist()

            print("🏆 Top States Selected for Forecasting:")
            for i, state in enumerate(top_states, 1):
                print(f"  {i}. {state} (Recent volume: ${state_totals[state]:,.0f})")

            forecasts = {}

            for state in top_states:
                state_data = state_time_series_data[state]
                forecast_result = self.forecast_state_returns(state_data, state, periods=forecast_months)

                if forecast_result is not None:
                    forecasts[state] = forecast_result

            return forecasts
        except Exception as e:
            print(f"Error getting top states forecast: {e}")
            return {}

    def get_current_month_info(self):
        """Get current month and calculate timeline periods"""
        current_date = datetime.now()
        current_month = current_date.replace(day=1)  # First day of current month

        # Previous month (last complete month)
        if current_month.month == 1:
            previous_month = current_month.replace(year=current_month.year-1, month=12)
        else:
            previous_month = current_month.replace(month=current_month.month-1)

        # Start of historical data (12 months back from previous month)
        historical_start = previous_month - timedelta(days=365)
        historical_start = historical_start.replace(day=1)

        # Forecast months (current month + next 5 months)
        forecast_months = []
        for i in range(6):  # Current month + 5 future months
            months_to_add = i
            total_months = current_month.month + months_to_add
            year = current_month.year + (total_months - 1) // 12
            month = (total_months - 1) % 12 + 1
            forecast_month = datetime(year, month, 1)
            forecast_months.append(forecast_month)

        return {
            'current_date': current_date,
            'current_month': current_month,
            'previous_month': previous_month,
            'historical_start': historical_start,
            'forecast_months': forecast_months,
            'historical_period': 12,  # Last 12 complete months
            'forecast_period': 6     # Current + next 5 months
        }

    def generate_react_forecast_data(self, forecasts, time_series_data):
        """Generate React-compatible forecast data with proper timeline"""

        if not forecasts:
            return {"forecastData": [], "metadata": {"companies": [], "error": "No forecasts generated"}}

        # Get timeline information
        timeline = self.get_current_month_info()

        # Get top companies from forecasts
        top_companies = list(forecasts.keys())

        react_data = []

        # Historical data (last 12 complete months)
        historical_end = timeline['previous_month']
        historical_start = timeline['historical_start']

        # Filter historical data for the period
        historical_start_dt = pd.to_datetime(historical_start)
        historical_end_dt = pd.to_datetime(historical_end)

        historical_mask = (time_series_data.index >= historical_start_dt) & (time_series_data.index <= historical_end_dt)
        historical_data = time_series_data[historical_mask]

        print(f"📅 Timeline Info:")
        print(f"   Current Date: {timeline['current_date'].strftime('%Y-%m-%d')}")
        print(f"   Current Month: {timeline['current_month'].strftime('%b %Y')}")
        print(f"   Previous Month: {timeline['previous_month'].strftime('%b %Y')}")
        print(f"   Historical Period: {historical_start.strftime('%b %Y')} to {historical_end.strftime('%b %Y')}")
        print(f"   Forecast Period: {timeline['forecast_months'][0].strftime('%b %Y')} to {timeline['forecast_months'][-1].strftime('%b %Y')}")

        # Add historical data
        for date in historical_data.index:
            month_data = {'month': date.strftime('%b %Y'), 'isHistorical': True}
            for company in top_companies:
                if company in historical_data.columns:
                    month_data[company] = int(historical_data.loc[date, company])
                else:
                    month_data[company] = 0
            react_data.append(month_data)

        # Add forecast data (current month + next 5 months)
        for i, forecast_date in enumerate(timeline['forecast_months']):
            month_data = {'month': forecast_date.strftime('%b %Y'), 'isHistorical': False}

            # Mark if this is current month (partial data might be available)
            is_current_month = (i == 0)
            month_data['isCurrentMonth'] = is_current_month

            for company in top_companies:
                if company in forecasts:
                    pred_data = forecasts[company]['forecast']
                    # Convert both to same format for comparison
                    forecast_date_str = forecast_date.strftime('%Y-%m')
                    pred_row = pred_data[pred_data['ds'].dt.strftime('%Y-%m') == forecast_date_str]
                    if not pred_row.empty:
                        month_data[f"{company}_pred"] = max(0, int(pred_row['yhat'].values[0]))
                    else:
                        month_data[f"{company}_pred"] = 0
                else:
                    month_data[f"{company}_pred"] = 0
            react_data.append(month_data)

        # Sort by date
        react_data.sort(key=lambda x: datetime.strptime(x['month'], '%b %Y'))

        # Calculate KPIs for React dashboard
        kpis = self.calculate_kpis(react_data, top_companies, timeline)

        # Create final structure
        final_data = {
            "forecastData": react_data,
            "kpis": kpis,
            "metadata": {
                "companies": top_companies,
                "timeline": {
                    "currentDate": timeline['current_date'].strftime('%Y-%m-%d'),
                    "currentMonth": timeline['current_month'].strftime('%b %Y'),
                    "previousMonth": timeline['previous_month'].strftime('%b %Y'),
                    "forecastStart": timeline['forecast_months'][0].strftime('%b %Y'),
                    "forecastEnd": timeline['forecast_months'][-1].strftime('%b %Y'),
                    "historicalMonths": len(historical_data),
                    "forecastMonths": len(timeline['forecast_months'])
                },
                "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "totalCompanies": len(top_companies)
            }
        }

        return final_data

    def generate_state_react_forecast_data(self, state_forecasts, state_time_series_data):
        """Generate React-compatible state forecast data with proper timeline"""

        if not state_forecasts:
            return {"forecastData": [], "metadata": {"states": [], "error": "No state forecasts generated"}}

        # Get timeline information
        timeline = self.get_current_month_info()

        # Get top states from forecasts
        top_states = list(state_forecasts.keys())

        react_data = []

        # Historical data (last 12 complete months)
        historical_end = timeline['previous_month']
        historical_start = timeline['historical_start']

        # Filter historical data for the period
        historical_start_dt = pd.to_datetime(historical_start)
        historical_end_dt = pd.to_datetime(historical_end)

        historical_mask = (state_time_series_data.index >= historical_start_dt) & (state_time_series_data.index <= historical_end_dt)
        historical_data = state_time_series_data[historical_mask]

        print(f"📅 State Timeline Info:")
        print(f"   Current Date: {timeline['current_date'].strftime('%Y-%m-%d')}")
        print(f"   Current Month: {timeline['current_month'].strftime('%b %Y')}")
        print(f"   Previous Month: {timeline['previous_month'].strftime('%b %Y')}")
        print(f"   Historical Period: {historical_start.strftime('%b %Y')} to {historical_end.strftime('%b %Y')}")
        print(f"   Forecast Period: {timeline['forecast_months'][0].strftime('%b %Y')} to {timeline['forecast_months'][-1].strftime('%b %Y')}")

        # Add historical data
        for date in historical_data.index:
            month_data = {'month': date.strftime('%b %Y'), 'isHistorical': True}
            for state in top_states:
                if state in historical_data.columns:
                    month_data[state] = int(historical_data.loc[date, state])
                else:
                    month_data[state] = 0
            react_data.append(month_data)

        # Add forecast data (current month + next 5 months)
        for i, forecast_date in enumerate(timeline['forecast_months']):
            month_data = {'month': forecast_date.strftime('%b %Y'), 'isHistorical': False}

            # Mark if this is current month (partial data might be available)
            is_current_month = (i == 0)
            month_data['isCurrentMonth'] = is_current_month

            for state in top_states:
                if state in state_forecasts:
                    pred_data = state_forecasts[state]['forecast']
                    # Convert both to same format for comparison
                    forecast_date_str = forecast_date.strftime('%Y-%m')
                    pred_row = pred_data[pred_data['ds'].dt.strftime('%Y-%m') == forecast_date_str]
                    if not pred_row.empty:
                        month_data[f"{state}_pred"] = max(0, int(pred_row['yhat'].values[0]))
                    else:
                        month_data[f"{state}_pred"] = 0
                else:
                    month_data[f"{state}_pred"] = 0
            react_data.append(month_data)

        # Sort by date
        react_data.sort(key=lambda x: datetime.strptime(x['month'], '%b %Y'))

        # Calculate KPIs for React dashboard
        kpis = self.calculate_state_kpis(react_data, top_states, timeline)

        # Create final structure
        final_data = {
            "forecastData": react_data,
            "kpis": kpis,
            "metadata": {
                "states": top_states,
                "timeline": {
                    "currentDate": timeline['current_date'].strftime('%Y-%m-%d'),
                    "currentMonth": timeline['current_month'].strftime('%b %Y'),
                    "previousMonth": timeline['previous_month'].strftime('%b %Y'),
                    "forecastStart": timeline['forecast_months'][0].strftime('%b %Y'),
                    "forecastEnd": timeline['forecast_months'][-1].strftime('%b %Y'),
                    "historicalMonths": len(historical_data),
                    "forecastMonths": len(timeline['forecast_months'])
                },
                "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "totalStates": len(top_states)
            }
        }

        return final_data

    def calculate_kpis(self, forecast_data, companies, timeline):
        """Calculate KPIs for the React dashboard"""

        # Separate historical and forecast data
        historical_data = [d for d in forecast_data if d.get('isHistorical', False)]
        forecast_data_only = [d for d in forecast_data if not d.get('isHistorical', False)]

        # Calculate previous month total (last complete historical month)
        previous_month_total = 0
        if historical_data:
            last_historical = historical_data[-1]  # This should be the previous month
            for company in companies:
                previous_month_total += last_historical.get(company, 0)

        # Calculate current month predicted total
        current_month_predicted = 0
        current_month_data = forecast_data_only[0] if forecast_data_only else None
        if current_month_data:
            for company in companies:
                current_month_predicted += current_month_data.get(f"{company}_pred", 0)

        # Calculate next month predicted total
        next_month_predicted = 0
        next_month_data = forecast_data_only[1] if len(forecast_data_only) > 1 else None
        if next_month_data:
            for company in companies:
                next_month_predicted += next_month_data.get(f"{company}_pred", 0)

        # Calculate growth percentages
        growth_current_vs_previous = 0
        if previous_month_total > 0:
            growth_current_vs_previous = ((current_month_predicted - previous_month_total) / previous_month_total * 100)

        growth_next_vs_current = 0
        if current_month_predicted > 0:
            growth_next_vs_current = ((next_month_predicted - current_month_predicted) / current_month_predicted * 100)

        # Calculate total forecast for next 6 months
        total_6month_forecast = 0
        for month_data in forecast_data_only:
            month_total = 0
            for company in companies:
                month_total += month_data.get(f"{company}_pred", 0)
            total_6month_forecast += month_total

        # Calculate average monthly forecast
        avg_monthly_forecast = total_6month_forecast / len(forecast_data_only) if forecast_data_only else 0

        # Calculate average rejection rate (placeholder - you can replace with actual data)
        avg_rejection = 8.2  # This would come from your actual data

        return {
            "previousMonthTotal": previous_month_total,
            "currentMonthPredicted": current_month_predicted,
            "nextMonthPredicted": next_month_predicted,
            "growthCurrentVsPrevious": round(growth_current_vs_previous, 1),
            "growthNextVsCurrent": round(growth_next_vs_current, 1),
            "total6MonthForecast": total_6month_forecast,
            "avgMonthlyForecast": round(avg_monthly_forecast),
            "avgRejection": avg_rejection,
            "totalVendors": len(companies)
        }

    def calculate_state_kpis(self, forecast_data, states, timeline):
        """Calculate KPIs for the React dashboard - State version"""

        # Separate historical and forecast data
        historical_data = [d for d in forecast_data if d.get('isHistorical', False)]
        forecast_data_only = [d for d in forecast_data if not d.get('isHistorical', False)]

        # Calculate previous month total (last complete historical month)
        previous_month_total = 0
        if historical_data:
            last_historical = historical_data[-1]  # This should be the previous month
            for state in states:
                previous_month_total += last_historical.get(state, 0)

        # Calculate current month predicted total
        current_month_predicted = 0
        current_month_data = forecast_data_only[0] if forecast_data_only else None
        if current_month_data:
            for state in states:
                current_month_predicted += current_month_data.get(f"{state}_pred", 0)

        # Calculate next month predicted total
        next_month_predicted = 0
        next_month_data = forecast_data_only[1] if len(forecast_data_only) > 1 else None
        if next_month_data:
            for state in states:
                next_month_predicted += next_month_data.get(f"{state}_pred", 0)

        # Calculate growth percentages
        growth_current_vs_previous = 0
        if previous_month_total > 0:
            growth_current_vs_previous = ((current_month_predicted - previous_month_total) / previous_month_total * 100)

        growth_next_vs_current = 0
        if current_month_predicted > 0:
            growth_next_vs_current = ((next_month_predicted - current_month_predicted) / current_month_predicted * 100)

        # Calculate total forecast for next 6 months
        total_6month_forecast = 0
        for month_data in forecast_data_only:
            month_total = 0
            for state in states:
                month_total += month_data.get(f"{state}_pred", 0)
            total_6month_forecast += month_total

        # Calculate average monthly forecast
        avg_monthly_forecast = total_6month_forecast / len(forecast_data_only) if forecast_data_only else 0

        # Calculate average rejection rate (placeholder - you can replace with actual data)
        avg_rejection = 8.2  # This would come from your actual data

        return {
            "previousMonthTotal": previous_month_total,
            "currentMonthPredicted": current_month_predicted,
            "nextMonthPredicted": next_month_predicted,
            "growthCurrentVsPrevious": round(growth_current_vs_previous, 1),
            "growthNextVsCurrent": round(growth_next_vs_current, 1),
            "total6MonthForecast": total_6month_forecast,
            "avgMonthlyForecast": round(avg_monthly_forecast),
            "avgRejection": avg_rejection,
            "totalStates": len(states)
        }

    def generate_forecast_from_csv(self, csv_path, top_n=5, forecast_months=6):
        """
        Generate forecasts from CSV file - includes both company and state forecasts
        """
        try:
            print("📊 Loading and preparing data from CSV...")
            df = pd.read_csv(csv_path)
            
            # Prepare company time series data
            self.time_series_data = self.prepare_time_series_data(df)
            if self.time_series_data is None:
                return {"error": "Failed to prepare company time series data"}

            # Prepare state time series data
            state_time_series_data = self.prepare_state_time_series_data(df)
            if state_time_series_data is None:
                return {"error": "Failed to prepare state time series data"}

            print(f"📈 Company data loaded: {len(self.time_series_data)} months, {len(self.time_series_data.columns)} companies")
            print(f"📈 State data loaded: {len(state_time_series_data)} months, {len(state_time_series_data.columns)} states")

            # Generate company forecasts
            print("\n🔮 Generating AI forecasts for top companies...")
            company_forecasts = self.get_top_companies_forecast(self.time_series_data, top_n, forecast_months)

            # Generate state forecasts
            print("\n🔮 Generating AI forecasts for top states...")
            state_forecasts = self.get_top_states_forecast(state_time_series_data, top_n, forecast_months)

            # Generate React-compatible data for companies
            print("\n🔄 Generating React-compatible company data...")
            company_react_data = self.generate_react_forecast_data(company_forecasts, self.time_series_data)

            # Generate React-compatible data for states
            print("\n🔄 Generating React-compatible state data...")
            state_react_data = self.generate_state_react_forecast_data(state_forecasts, state_time_series_data)

            # Combine both forecasts
            combined_data = {
                "companyForecasts": company_react_data,
                "stateForecasts": state_react_data,
                "metadata": {
                    "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "forecastMonths": forecast_months,
                    "topN": top_n
                }
            }

            return combined_data

        except Exception as e:
            print(f"Error generating forecast from CSV: {e}")
            return {"error": str(e)}

    def generate_forecast_from_db(self, db_connection, query, top_n=5, forecast_months=6):
        """
        Generate forecasts from database - includes both company and state forecasts
        """
        try:
            print("📊 Loading and preparing data from database...")
            df = db_connection.fetch_data(query)
            
            if df is None or df.empty:
                return {"error": "No data found in database"}

            # Prepare company time series data
            self.time_series_data = self.prepare_time_series_data(df)
            if self.time_series_data is None:
                return {"error": "Failed to prepare company time series data"}

            # Prepare state time series data
            state_time_series_data = self.prepare_state_time_series_data(df)
            if state_time_series_data is None:
                return {"error": "Failed to prepare state time series data"}

            print(f"📈 Company data loaded: {len(self.time_series_data)} months, {len(self.time_series_data.columns)} companies")
            print(f"📈 State data loaded: {len(state_time_series_data)} months, {len(state_time_series_data.columns)} states")

            # Generate company forecasts
            print("\n🔮 Generating AI forecasts for top companies...")
            company_forecasts = self.get_top_companies_forecast(self.time_series_data, top_n, forecast_months)

            # Generate state forecasts
            print("\n🔮 Generating AI forecasts for top states...")
            state_forecasts = self.get_top_states_forecast(state_time_series_data, top_n, forecast_months)

            # Generate React-compatible data for companies
            print("\n🔄 Generating React-compatible company data...")
            company_react_data = self.generate_react_forecast_data(company_forecasts, self.time_series_data)

            # Generate React-compatible data for states
            print("\n🔄 Generating React-compatible state data...")
            state_react_data = self.generate_state_react_forecast_data(state_forecasts, state_time_series_data)

            # Combine both forecasts
            combined_data = {
                "companyForecasts": company_react_data,
                "stateForecasts": state_react_data,
                "metadata": {
                    "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "forecastMonths": forecast_months,
                    "topN": top_n
                }
            }

            return combined_data

        except Exception as e:
            print(f"Error generating forecast from database: {e}")
            return {"error": str(e)}