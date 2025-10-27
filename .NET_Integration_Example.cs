using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;

namespace ReturnsForecast.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ForecastController : ControllerBase
    {
        private readonly HttpClient _httpClient;
        private readonly string _flaskApiUrl = "http://localhost:5000";

        public ForecastController(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        /// <summary>
        /// Get forecasts by fetching data from database and calling Flask API
        /// </summary>
        [HttpGet("forecasts")]
        public async Task<IActionResult> GetForecasts()
        {
            try
            {
                // Step 1: Fetch data from database
                var transactions = await FetchTransactionsFromDatabase();
                
                if (transactions == null || transactions.Count == 0)
                {
                    return BadRequest(new { error = "No transaction data found" });
                }

                // Step 2: Prepare JSON payload for Flask API
                var jsonPayload = PrepareJsonPayload(transactions);

                // Step 3: Call Flask API
                var forecastResult = await CallFlaskApi(jsonPayload);

                if (forecastResult == null)
                {
                    return StatusCode(500, new { error = "Failed to get forecasts from Flask API" });
                }

                // Step 4: Return formatted result to React
                return Ok(forecastResult);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        /// <summary>
        /// Force retrain models and get forecasts
        /// </summary>
        [HttpPost("forecasts/retrain")]
        public async Task<IActionResult> RetrainAndGetForecasts([FromBody] RetrainRequest request)
        {
            try
            {
                // Step 1: Fetch data from database
                var transactions = await FetchTransactionsFromDatabase();
                
                if (transactions == null || transactions.Count == 0)
                {
                    return BadRequest(new { error = "No transaction data found" });
                }

                // Step 2: Prepare JSON payload with force retrain
                var jsonPayload = PrepareJsonPayload(transactions, request.TopN, request.ForecastMonths, true);

                // Step 3: Call Flask API
                var forecastResult = await CallFlaskApi(jsonPayload);

                if (forecastResult == null)
                {
                    return StatusCode(500, new { error = "Failed to retrain models and get forecasts" });
                }

                return Ok(forecastResult);
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        /// <summary>
        /// Health check endpoint
        /// </summary>
        [HttpGet("health")]
        public async Task<IActionResult> HealthCheck()
        {
            try
            {
                // Check Flask API health
                var response = await _httpClient.GetAsync($"{_flaskApiUrl}/health");
                
                if (response.IsSuccessStatusCode)
                {
                    var content = await response.Content.ReadAsStringAsync();
                    return Ok(new { 
                        status = "healthy", 
                        flask_api = "connected",
                        flask_response = JsonSerializer.Deserialize<object>(content)
                    });
                }
                else
                {
                    return StatusCode(503, new { 
                        status = "unhealthy", 
                        flask_api = "disconnected",
                        error = "Flask API is not responding"
                    });
                }
            }
            catch (Exception ex)
            {
                return StatusCode(503, new { 
                    status = "unhealthy", 
                    flask_api = "error",
                    error = ex.Message
                });
            }
        }

        private async Task<List<Transaction>> FetchTransactionsFromDatabase()
        {
            // TODO: Implement your database query here
            // This is a placeholder - replace with your actual database logic
            
            // Example using Entity Framework:
            /*
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
            */
            
            // For testing purposes, return sample data
            return GenerateSampleData();
        }

        private List<Transaction> GenerateSampleData()
        {
            var random = new Random();
            var companies = new[] { "AMERISOURCEBERGEN DRUG CORP", "CARDINAL HEALTH", "MCKESSON CORPORATION", "WALMART PHARMACY", "CVS HEALTH" };
            var states = new[] { "CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI" };
            var transactions = new List<Transaction>();

            for (int i = 0; i < 100; i++)
            {
                var randomDays = random.Next(0, 365);
                var transactionDate = DateTime.Now.AddDays(-randomDays);

                transactions.Add(new Transaction
                {
                    DateTransactionJulian = transactionDate.ToString("yyyy-MM-dd"),
                    NameAlpha = companies[random.Next(companies.Length)],
                    State = states[random.Next(states.Length)],
                    Orig_Inv_Ttl_Prod_Value = Math.Round(random.NextDouble() * 5000 + 100, 2)
                });
            }

            return transactions;
        }

        private object PrepareJsonPayload(List<Transaction> transactions, int topN = 5, int forecastMonths = 6, bool forceRetrain = false)
        {
            return new
            {
                data = transactions,
                top_n = topN,
                forecast_months = forecastMonths,
                force_retrain = forceRetrain
            };
        }

        private async Task<object> CallFlaskApi(object payload)
        {
            try
            {
                var json = JsonSerializer.Serialize(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync($"{_flaskApiUrl}/process-data", content);

                if (response.IsSuccessStatusCode)
                {
                    var responseContent = await response.Content.ReadAsStringAsync();
                    return JsonSerializer.Deserialize<object>(responseContent);
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    Console.WriteLine($"Flask API error: {response.StatusCode} - {errorContent}");
                    return null;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error calling Flask API: {ex.Message}");
                return null;
            }
        }
    }

    // Data models
    public class Transaction
    {
        public string DateTransactionJulian { get; set; }
        public string NameAlpha { get; set; }
        public string State { get; set; }
        public double Orig_Inv_Ttl_Prod_Value { get; set; }
    }

    public class RetrainRequest
    {
        public int TopN { get; set; } = 5;
        public int ForecastMonths { get; set; } = 6;
    }
}

// Program.cs configuration
/*
public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add services
        builder.Services.AddControllers();
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

        var app = builder.Build();

        // Configure pipeline
        app.UseCors("AllowReactApp");
        app.UseRouting();
        app.MapControllers();

        app.Run();
    }
}
*/

// React Integration Example (JavaScript/TypeScript)
/*
// React component for fetching forecasts
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
            
            // Extract company forecasts data
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
*/
