# Sequential Integration Steps

## Overview
This document provides step-by-step instructions for integrating the Flask Prophet Model API with your React and .NET applications.

## Prerequisites
- Python 3.8+ installed
- .NET 6+ installed
- React application ready
- Database with transaction data

## Step 1: Setup Flask API

### 1.1 Install Dependencies
```bash
cd /home/Kamal_Pulaparthi/Documents/pythonProjects/returns_forcast
pip install -r requirements.txt
```

### 1.2 Configure Environment
Create a `.env` file:
```bash
# Database configuration (if using database endpoint)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=prophet_db
DB_PORT=3306

# API configuration
DEBUG=True
```

### 1.3 Test Flask API
```bash
python app.py
```

The API should start on `http://localhost:5000`

### 1.4 Verify API Health
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Step 2: Test API with Sample Data

### 2.1 Run Integration Test
```bash
python integration_example.py
```

This will test all API endpoints and verify functionality.

### 2.2 Test JSON Processing
```bash
curl -X POST http://localhost:5000/process-data \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "DateTransactionJulian": "2024-01-15",
        "NameAlpha": "TEST COMPANY",
        "State": "CA",
        "Orig_Inv_Ttl_Prod_Value": 1000.50
      }
    ],
    "top_n": 5,
    "forecast_months": 6,
    "force_retrain": false
  }'
```

## Step 3: Setup .NET Server

### 3.1 Create .NET Web API Project
```bash
dotnet new webapi -n ReturnsForecastAPI
cd ReturnsForecastAPI
```

### 3.2 Install Required Packages
```bash
dotnet add package Microsoft.AspNetCore.Http
dotnet add package System.Text.Json
```

### 3.3 Add Forecast Controller
Copy the content from `.NET_Integration_Example.cs` to your `Controllers/ForecastController.cs`

### 3.4 Configure HttpClient
In `Program.cs`:
```csharp
builder.Services.AddHttpClient<ForecastController>();
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowReactApp", policy =>
    {
        policy.WithOrigins("http://localhost:3000")
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});
```

### 3.5 Update Database Context
Replace the `FetchTransactionsFromDatabase()` method with your actual database query:

```csharp
private async Task<List<Transaction>> FetchTransactionsFromDatabase()
{
    using var context = new YourDbContext();
    return await context.Transactions
        .Where(t => t.Date >= DateTime.Now.AddYears(-1))
        .Select(t => new Transaction
        {
            DateTransactionJulian = t.Date.ToString("yyyy-MM-dd"),
            NameAlpha = t.CompanyName,
            State = t.State,
            Orig_Inv_Ttl_Prod_Value = t.Value
        })
        .ToListAsync();
}
```

### 3.6 Test .NET API
```bash
dotnet run
```

Test the health endpoint:
```bash
curl http://localhost:5001/api/forecast/health
```

## Step 4: Setup React Application

### 4.1 Create React Component
Create `src/components/ForecastDashboard.js`:

```javascript
import React, { useState, useEffect } from 'react';

const ForecastDashboard = () => {
    const [forecastData, setForecastData] = useState(null);
    const [kpis, setKpis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchForecasts = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch('/api/forecast/forecasts');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.companyForecasts) {
                setForecastData(data.companyForecasts.forecastData);
                setKpis(data.companyForecasts.kpis);
            }
            
        } catch (err) {
            setError(err.message);
            console.error('Error fetching forecasts:', err);
        } finally {
            setLoading(false);
        }
    };

    const retrainModels = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch('/api/forecast/forecasts/retrain', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topN: 5,
                    forecastMonths: 6
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.companyForecasts) {
                setForecastData(data.companyForecasts.forecastData);
                setKpis(data.companyForecasts.kpis);
            }
            
        } catch (err) {
            setError(err.message);
            console.error('Error retraining models:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchForecasts();
    }, []);

    if (loading) return <div>Loading forecasts...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <h1>Returns Forecast Dashboard</h1>
            <button onClick={retrainModels} disabled={loading}>
                Retrain Models
            </button>
            
            {kpis && (
                <div className="kpis">
                    <h2>Key Performance Indicators</h2>
                    <p>Previous Month: ${kpis.previousMonthTotal.toLocaleString()}</p>
                    <p>Current Month Predicted: ${kpis.currentMonthPredicted.toLocaleString()}</p>
                    <p>Growth Rate: {kpis.growthCurrentVsPrevious}%</p>
                    <p>6-Month Forecast: ${kpis.total6MonthForecast.toLocaleString()}</p>
                </div>
            )}
            
            {forecastData && (
                <div className="forecast-chart">
                    <h2>Forecast Data</h2>
                    {/* Render your chart component here */}
                    <pre>{JSON.stringify(forecastData, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default ForecastDashboard;
```

### 4.2 Add to App.js
```javascript
import ForecastDashboard from './components/ForecastDashboard';

function App() {
  return (
    <div className="App">
      <ForecastDashboard />
    </div>
  );
}

export default App;
```

## Step 5: Complete Integration Flow

### 5.1 Start All Services

**Terminal 1 - Flask API:**
```bash
cd /home/Kamal_Pulaparthi/Documents/pythonProjects/returns_forcast
python app.py
```

**Terminal 2 - .NET API:**
```bash
cd ReturnsForecastAPI
dotnet run
```

**Terminal 3 - React App:**
```bash
npm start
```

### 5.2 Test Complete Flow

1. **React → .NET**: React app calls `/api/forecast/forecasts`
2. **.NET → Database**: .NET fetches data from database
3. **.NET → Flask**: .NET calls Flask API with JSON data
4. **Flask Processing**: 
   - Converts JSON to CSV
   - Checks if models need retraining
   - Generates forecasts using Prophet models
   - Returns forecast data
5. **Flask → .NET**: Flask returns forecast results
6. **.NET → React**: .NET returns formatted data to React
7. **React Display**: React displays forecasts in dashboard

## Step 6: Monitoring and Maintenance

### 6.1 Monitor API Health
- Flask API: `http://localhost:5000/health`
- .NET API: `http://localhost:5001/api/forecast/health`

### 6.2 Check Model Status
- Models are stored in `models/trained_models/`
- Model registry: `models/model_registry.json`
- CSV data: `data/processed_data_*.csv`

### 6.3 Performance Monitoring
- First request: 5-10 seconds (model training)
- Subsequent requests: 1-3 seconds (cached models)
- Data changes trigger automatic retraining

## Troubleshooting

### Common Issues

1. **Flask API not starting**
   - Check Python version (3.8+)
   - Install dependencies: `pip install -r requirements.txt`
   - Check port 5000 is available

2. **.NET API connection issues**
   - Verify Flask API is running
   - Check CORS configuration
   - Update Flask API URL in .NET code

3. **React fetch errors**
   - Check .NET API is running
   - Verify CORS policy
   - Check network tab in browser dev tools

4. **Model training failures**
   - Ensure sufficient data (minimum 4 months)
   - Check data format and validation
   - Review console logs for errors

### Debug Mode
Enable detailed logging by setting `DEBUG=True` in Flask `.env` file.

## Production Deployment

### Flask API
- Use production WSGI server (Gunicorn)
- Set up reverse proxy (Nginx)
- Configure environment variables
- Set up monitoring and logging

### .NET API
- Configure for production environment
- Set up database connection strings
- Configure CORS for production domains
- Set up health checks and monitoring

### React App
- Build for production: `npm run build`
- Deploy to web server or CDN
- Configure API endpoints for production

## Support

For technical support:
1. Check console logs for detailed error messages
2. Verify all services are running and accessible
3. Test individual components using the provided examples
4. Review the API documentation for detailed endpoint information
