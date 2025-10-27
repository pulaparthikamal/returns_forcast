# Flask Prophet Model API Documentation

## Overview
This Flask API provides intelligent forecasting capabilities for company and state returns data using Prophet models. The API supports both CSV and JSON data input, with intelligent model management that only retrains when data changes.

## Features
- **Intelligent Model Management**: Only retrains models when data changes
- **JSON to CSV Conversion**: Automatically converts JSON data from .NET server
- **Dual Forecasting**: Company and state-level predictions
- **Model Caching**: Loads existing models for faster predictions
- **Data Validation**: Comprehensive data cleaning and validation
- **RESTful API**: Easy integration with .NET and React applications

## API Endpoints

### 1. Health Check
```
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Process Data from .NET Server
```
POST /process-data
```
**Description:** Main endpoint for processing JSON data from .NET server and generating forecasts.

**Request Body:**
```json
{
  "data": [
    {
      "DateTransactionJulian": "2024-01-15",
      "NameAlpha": "COMPANY NAME",
      "State": "CA",
      "Orig_Inv_Ttl_Prod_Value": 1000.50
    },
    {
      "DateTransactionJulian": "2024-01-16",
      "NameAlpha": "ANOTHER COMPANY",
      "State": "NY",
      "Orig_Inv_Ttl_Prod_Value": 2500.75
    }
  ],
  "top_n": 5,
  "forecast_months": 6,
  "force_retrain": false
}
```

**Parameters:**
- `data` (required): Array of transaction records
- `top_n` (optional): Number of top companies/states to forecast (default: 5)
- `forecast_months` (optional): Number of months to forecast (default: 6)
- `force_retrain` (optional): Force model retraining (default: false)

**Response:**
```json
{
  "companyForecasts": {
    "forecastData": [
      {
        "month": "Jan 2024",
        "isHistorical": true,
        "COMPANY NAME": 1000,
        "ANOTHER COMPANY": 2500
      },
      {
        "month": "Feb 2024",
        "isHistorical": false,
        "isCurrentMonth": true,
        "COMPANY NAME_pred": 1200,
        "ANOTHER COMPANY_pred": 2800
      }
    ],
    "kpis": {
      "previousMonthTotal": 3500,
      "currentMonthPredicted": 4000,
      "nextMonthPredicted": 4200,
      "growthCurrentVsPrevious": 14.3,
      "growthNextVsCurrent": 5.0,
      "total6MonthForecast": 25000,
      "avgMonthlyForecast": 4167,
      "avgRejection": 8.2,
      "totalVendors": 5
    },
    "metadata": {
      "companies": ["COMPANY NAME", "ANOTHER COMPANY"],
      "timeline": {
        "currentDate": "2024-01-15",
        "currentMonth": "Jan 2024",
        "previousMonth": "Dec 2023",
        "forecastStart": "Jan 2024",
        "forecastEnd": "Jun 2024",
        "historicalMonths": 12,
        "forecastMonths": 6
      },
      "generatedAt": "2024-01-15 10:30:00",
      "totalCompanies": 5
    }
  },
  "stateForecasts": {
    "forecastData": [...],
    "kpis": {...},
    "metadata": {...}
  },
  "metadata": {
    "generatedAt": "2024-01-15T10:30:00.000Z",
    "forecastMonths": 6,
    "topN": 5
  },
  "processing_info": {
    "records_processed": 100,
    "csv_path": "data/processed_data_20240115_103000.csv",
    "models_retrained": false,
    "processed_at": "2024-01-15T10:30:00.000Z"
  }
}
```

### 3. Generate Forecast from CSV (Testing)
```
GET /forecast/csv
```
**Description:** Generate forecasts using default CSV data for testing purposes.

**Response:** Same structure as `/process-data` endpoint.

### 4. Generate Forecast (Legacy)
```
POST /forecast
```
**Description:** Legacy endpoint for generating forecasts from CSV or database.

**Request Body:**
```json
{
  "data_source": "csv",
  "top_n": 5,
  "forecast_months": 6,
  "query": "SELECT * FROM transactions"
}
```

## Data Format Requirements

### JSON Data Structure
The API expects JSON data in the following format:

```json
[
  {
    "DateTransactionJulian": "2024-01-15",  // Date in YYYY-MM-DD format
    "NameAlpha": "COMPANY NAME",            // Company name (string)
    "State": "CA",                          // State code (string)
    "Orig_Inv_Ttl_Prod_Value": 1000.50     // Numeric value (float)
  }
]
```

### Required Fields
- `DateTransactionJulian`: Transaction date
- `NameAlpha`: Company name
- `State`: State code
- `Orig_Inv_Ttl_Prod_Value`: Transaction value

## Model Management

### Intelligent Training
The API automatically determines when to retrain models based on:
1. **Data Hash Comparison**: Compares current data hash with stored model hashes
2. **New Companies**: Detects new companies not in existing models
3. **Force Retrain**: Manual override via `force_retrain` parameter

### Model Storage
- Models are stored in `models/trained_models/` directory
- Model registry is maintained in `models/model_registry.json`
- Models are cached in memory for faster subsequent predictions

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "No data provided in request"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to convert JSON data to CSV"
}
```

## Setup and Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd returns_forcast
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create environment file:**
```bash
# Create .env file
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=prophet_db
DB_PORT=3306
DEBUG=True
```

4. **Run the application:**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Integration Steps

### Step 1: React to .NET Server
1. **React Application** makes API call to .NET server
2. **.NET Server** fetches data from database
3. **.NET Server** prepares JSON payload

### Step 2: .NET to Flask API
1. **.NET Server** makes POST request to Flask API
2. **Flask API** receives JSON data at `/process-data` endpoint
3. **Flask API** converts JSON to CSV format
4. **Flask API** checks if models need retraining
5. **Flask API** generates forecasts using Prophet models
6. **Flask API** returns forecast data to .NET server

### Step 3: .NET to React
1. **.NET Server** receives forecast data from Flask API
2. **.NET Server** processes and formats data for React
3. **.NET Server** returns formatted data to React application
4. **React Application** displays forecasts in dashboard

## Example Integration Code

### .NET Server (C#)
```csharp
public async Task<IActionResult> GetForecasts()
{
    // 1. Fetch data from database
    var transactions = await _dbContext.Transactions.ToListAsync();
    
    // 2. Prepare JSON payload
    var jsonData = transactions.Select(t => new
    {
        DateTransactionJulian = t.Date.ToString("yyyy-MM-dd"),
        NameAlpha = t.CompanyName,
        State = t.State,
        Orig_Inv_Ttl_Prod_Value = t.Value
    }).ToList();
    
    var payload = new
    {
        data = jsonData,
        top_n = 5,
        forecast_months = 6,
        force_retrain = false
    };
    
    // 3. Call Flask API
    using var httpClient = new HttpClient();
    var json = JsonSerializer.Serialize(payload);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await httpClient.PostAsync("http://localhost:5000/process-data", content);
    var result = await response.Content.ReadAsStringAsync();
    
    // 4. Return to React
    return Ok(JsonSerializer.Deserialize<object>(result));
}
```

### React Application (JavaScript)
```javascript
const fetchForecasts = async () => {
  try {
    const response = await fetch('/api/forecasts');
    const data = await response.json();
    
    // Process forecast data for dashboard
    setForecastData(data.companyForecasts.forecastData);
    setKpis(data.companyForecasts.kpis);
    
  } catch (error) {
    console.error('Error fetching forecasts:', error);
  }
};
```

## Performance Considerations

### Model Caching
- Models are cached in memory after first load
- Subsequent predictions use cached models for faster response
- Models are automatically reloaded if data changes

### Data Processing
- JSON to CSV conversion is optimized for large datasets
- Data validation removes invalid records automatically
- Hash-based change detection minimizes unnecessary retraining

### Response Times
- **First Request**: 5-10 seconds (model training)
- **Subsequent Requests**: 1-3 seconds (cached models)
- **Data Changes**: 5-10 seconds (retraining required)

## Monitoring and Logging

### Console Output
The API provides detailed console output including:
- Data processing status
- Model training progress
- Forecast generation steps
- Error messages and warnings

### Log Levels
- ✅ Success messages
- ⚠️ Warning messages
- ❌ Error messages
- 🔄 Processing status
- 📊 Data statistics

## Troubleshooting

### Common Issues

1. **Model Training Fails**
   - Check data quality and format
   - Ensure sufficient historical data (minimum 4 months)
   - Verify all required fields are present

2. **Slow Response Times**
   - Check if models are being retrained unnecessarily
   - Verify data hash comparison is working correctly
   - Monitor memory usage for model caching

3. **Data Validation Errors**
   - Ensure date format is YYYY-MM-DD
   - Check numeric values are valid
   - Verify company names and state codes are properly formatted

### Debug Mode
Enable debug mode by setting `DEBUG=True` in the `.env` file for detailed logging.

## Support

For technical support or questions about the API, please refer to the console output for detailed error messages and processing information.
