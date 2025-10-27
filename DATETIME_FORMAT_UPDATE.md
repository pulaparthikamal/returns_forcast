# Datetime Format Update

## Overview
Updated the Flask Prophet Model API to handle the new datetime format `"2017-04-22T00:00:00"` while maintaining backward compatibility with the legacy `"2017-04-22"` format.

## Changes Made

### 1. Data Processor (`utils/data_processor.py`)
- **Updated `_clean_data()` method**: Now uses `pd.to_datetime()` with `errors='coerce'` to handle both formats
- **Updated `calculate_data_hash()` method**: Converts dates to consistent `YYYY-MM-DD` format for hashing
- **Enhanced error handling**: Gracefully handles invalid datetime formats

### 2. Forecast Service (`services/forecast_service.py`)
- **Updated `prepare_time_series_data()` method**: Uses flexible datetime parsing
- **Updated `prepare_state_time_series_data()` method**: Uses flexible datetime parsing
- **Updated `_calculate_data_hash()` method**: Ensures consistent date formatting for hash calculation

### 3. API Documentation (`API_DOCUMENTATION.md`)
- **Updated request examples**: Now shows the new `YYYY-MM-DDTHH:MM:SS` format
- **Added backward compatibility note**: Documents support for both formats
- **Updated data structure documentation**: Reflects the new datetime format

### 4. Integration Examples
- **Updated `.NET_Integration_Example.cs`**: Uses `yyyy-MM-ddTHH:mm:ss` format
- **Updated `integration_example.py`**: Uses `%Y-%m-%dT%H:%M:%S` format
- **Updated `app.py`**: Updated endpoint documentation with new format

### 5. Test Scripts
- **Created `test_datetime_format.py`**: Comprehensive test for both formats
- **Tests mixed format data**: Ensures compatibility with mixed datetime formats
- **Error handling tests**: Verifies proper handling of invalid datetime formats

## Supported Datetime Formats

### Primary Format (New)
```
"2024-01-15T00:00:00"
"2024-01-15T12:30:45"
"2024-01-15T23:59:59"
```

### Legacy Format (Backward Compatible)
```
"2024-01-15"
"2024-01-16"
"2024-01-17"
```

### Mixed Format Support
The API can handle datasets with mixed datetime formats in the same request:
```json
[
  {
    "DateTransactionJulian": "2024-01-15T00:00:00",
    "NameAlpha": "COMPANY 1",
    "State": "CA",
    "Orig_Inv_Ttl_Prod_Value": 1000.50
  },
  {
    "DateTransactionJulian": "2024-01-16",
    "NameAlpha": "COMPANY 2", 
    "State": "NY",
    "Orig_Inv_Ttl_Prod_Value": 2500.75
  }
]
```

## Technical Implementation

### Pandas Datetime Parsing
```python
# Handles both formats automatically
df['DateTransactionJulian'] = pd.to_datetime(df['DateTransactionJulian'], errors='coerce')
```

### Hash Calculation
```python
# Converts to consistent format for hashing
df_sorted['DateTransactionJulian'] = pd.to_datetime(df_sorted['DateTransactionJulian']).dt.strftime('%Y-%m-%d')
```

### Error Handling
- Invalid datetime strings are converted to `NaT` (Not a Time)
- Rows with invalid dates are automatically filtered out
- Detailed error logging for debugging

## Testing

### Run Datetime Format Tests
```bash
python test_datetime_format.py
```

### Test Both Formats
```bash
# Test new format
curl -X POST http://localhost:5000/process-data \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {
        "DateTransactionJulian": "2024-01-15T00:00:00",
        "NameAlpha": "TEST COMPANY",
        "State": "CA",
        "Orig_Inv_Ttl_Prod_Value": 1000.50
      }
    ]
  }'

# Test legacy format
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
    ]
  }'
```

## Migration Guide

### For .NET Applications
Update your datetime formatting:
```csharp
// Old format
DateTransactionJulian = transactionDate.ToString("yyyy-MM-dd")

// New format
DateTransactionJulian = transactionDate.ToString("yyyy-MM-ddTHH:mm:ss")
```

### For Python Applications
Update your datetime formatting:
```python
# Old format
"DateTransactionJulian": transaction_date.strftime("%Y-%m-%d")

# New format
"DateTransactionJulian": transaction_date.strftime("%Y-%m-%dT%H:%M:%S")
```

### For Database Queries
If your database stores datetime with time components:
```sql
-- Convert to ISO 8601 format
SELECT 
    DATE_FORMAT(transaction_date, '%Y-%m-%dT%H:%i:%s') as DateTransactionJulian,
    company_name as NameAlpha,
    state as State,
    value as Orig_Inv_Ttl_Prod_Value
FROM transactions
```

## Backward Compatibility

✅ **Fully Backward Compatible**
- Existing integrations using `YYYY-MM-DD` format will continue to work
- No breaking changes to existing API contracts
- Gradual migration supported

## Performance Impact

- **Minimal**: Pandas `to_datetime()` is highly optimized
- **No additional overhead**: Single parsing operation handles both formats
- **Consistent hashing**: Date normalization ensures reliable model management

## Error Handling

### Invalid Datetime Formats
- `"invalid-date"` → Filtered out with warning
- `""` (empty string) → Filtered out with warning  
- `null` → Filtered out with warning
- `"15/01/2024"` → Filtered out with warning

### Logging
```
📊 Data cleaned: 95 valid records remaining
⚠️ 5 records filtered due to invalid datetime format
```

## Validation

The API validates datetime formats and provides clear feedback:
- Valid formats are processed normally
- Invalid formats are logged and filtered out
- Processing continues with valid records
- Error messages indicate the number of filtered records

## Conclusion

The datetime format update provides:
- ✅ Support for the new `YYYY-MM-DDTHH:MM:SS` format
- ✅ Backward compatibility with `YYYY-MM-DD` format
- ✅ Mixed format support in the same request
- ✅ Robust error handling for invalid formats
- ✅ No breaking changes to existing integrations
- ✅ Comprehensive testing and validation

The API is now ready to handle the new datetime format while maintaining full compatibility with existing systems.
