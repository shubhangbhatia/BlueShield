import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [selectedLocation, setSelectedLocation] = useState("new_york");
  const [locations, setLocations] = useState({});
  const [forecast, setForecast] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [alert, setAlert] = useState(null);
  const [riskLevel, setRiskLevel] = useState("LOW");
  const [currentWeather, setCurrentWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [dataSource, setDataSource] = useState("API");
  const [avgFeature, setAvgFeature] = useState(null);
  const [minFeature, setMinFeature] = useState(null);
  const [maxFeature, setMaxFeature] = useState(null);

  // Fetch available locations
  useEffect(() => {
    fetch('http://localhost:8000/locations')
      .then(res => res.json())
      .then(data => setLocations(data))
      .catch(err => console.error('Error fetching locations:', err));
  }, []);

  // Fetch live weather prediction
  async function fetchLivePrediction() {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/predict-live/${selectedLocation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Live API response:", data);
      
      setForecast(data.forecast);
      setAnomaly(data.anomaly);
      setAlert(data.alert);
      setRiskLevel(data.risk_level);
      setCurrentWeather(data.current_weather);
      setDataSource(data.data_source);
      setLastUpdated(new Date().toLocaleTimeString());
      setAvgFeature(data.average_feature);
      setMinFeature(data.min_feature);
      setMaxFeature(data.max_feature);
      
    } catch (error) {
      console.error('Live prediction error:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  // Auto-refresh effect
  useEffect(() => {
    if (isAutoRefresh) {
      fetchLivePrediction();
      const interval = setInterval(fetchLivePrediction, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isAutoRefresh, selectedLocation]);

  // Manual refresh
  const handleManualRefresh = () => {
    fetchLivePrediction();
  };

  const getRiskColor = () => {
    switch(riskLevel) {
      case 'HIGH': return '#dc3545';
      case 'MEDIUM': return '#ffc107';
      default: return '#28a745';
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🌊 BlueShield - Live Weather Monitoring</h1>
        <div className="header-controls">
          <select 
              value={selectedLocation} 
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="location-selector"
            >
              {Object.keys(locations).length === 0 ? (
                <option>Loading...</option>
              ) : (
                Object.entries(locations).map(([id, location]) => (
                  <option key={id} value={id}>{location.name}</option>
                ))
              )}
        </select>
          <button 
            onClick={handleManualRefresh} 
            disabled={loading}
            className="refresh-btn"
          >
            {loading ? '🔄 Updating...' : '🔄 Refresh'}
          </button>
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={isAutoRefresh}
              onChange={(e) => setIsAutoRefresh(e.target.checked)}
            />
            Auto-refresh (30s)
          </label>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Status Cards */}
        <div className="status-cards">
          <div className="card forecast-card">
            <div className="card-header">
              <h3>📊 Flood Risk Forecast</h3>
            </div>
            <div className="card-content">
              <div className="main-value">
                {loading ? (
                  <div className="loading-spinner">Loading...</div>
                ) : forecast !== null ? (
                  <span className="forecast-value">
                    {forecast.toFixed(2)} 
                  </span>
                ) : (
                  <span className="no-data">No data</span>
                )}
              </div>
              <div className="card-footer">
                Flood risk index (0-10)
              </div>
            </div>
          </div>

          <div className="card anomaly-card">
            <div className="card-header">
              <h3>⚠️ Weather Anomaly</h3>
            </div>
            <div className="card-content">
              <div className="main-value">
                {loading ? (
                  <div className="loading-spinner">Loading...</div>
                ) : anomaly !== null ? (
                  <span className={`anomaly-status ${anomaly === -1 ? 'anomaly-detected' : 'normal'}`}>
                    {anomaly === -1 ? '🚨 DETECTED' : '✅ NORMAL'}
                  </span>
                ) : (
                  <span className="no-data">No data</span>
                )}
              </div>
              <div className="card-footer">
                Weather pattern analysis
              </div>
            </div>
          </div>

          <div className="card risk-card">
            <div className="card-header">
              <h3>🎯 Risk Level</h3>
            </div>
            <div className="card-content">
              <div className="main-value">
                <span 
                  className={`risk-level risk-${riskLevel.toLowerCase()}`}
                  style={{ color: getRiskColor() }}
                >
                  {riskLevel}
                </span>
              </div>
              <div className="card-footer">
                Overall assessment
              </div>
            </div>
          </div>

          <div className="card avg-card">
            <div className="card-header">
              <h3>📈 Average</h3>
            </div>
            <div className="card-content">
              <div>
                {typeof avgFeature === "number" ? avgFeature.toFixed(2) : "No data"}
              </div>
            </div>
            <div className="card-footer">
              Average of latest forecast features
            </div>
          </div>

          <div className="card min-card">
            <div className="card-header">
              <h3>📉 Min</h3>
            </div>
            <div className="card-content">
              <div>
                {typeof minFeature === "number" ? minFeature.toFixed(2) : "No data"}
              </div>
            </div>
            <div className="card-footer">
              Minimum of latest forecast features
            </div>
          </div>

          <div className="card max-card">
            <div className="card-header">
              <h3>📊 Max Feature</h3>
            </div>
            <div className="card-content">
              <div>
                {typeof maxFeature === "number" ? maxFeature.toFixed(2) : "No data"}
              </div>
            </div>
            <div className="card-footer">
              Maximum of latest forecast features
            </div>
          </div>
        </div>

        {/* Alert Banner */}
        {alert && (
          <div className="alert-banner">
            <div className="alert-content">
              <span className="alert-icon">🚨</span>
              <span className="alert-text">{alert}</span>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <div className="error-content">
              <span className="error-icon">❌</span>
              <span className="error-text">Error: {error}</span>
              <button onClick={handleManualRefresh} className="retry-btn">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Current Weather Data */}
        {currentWeather && (
          <div className="weather-preview">
            <h3>🌤️ Current Weather Conditions</h3>
            <div className="weather-data">
              <div className="weather-summary">
                <div>
                  <strong>Conditions:</strong> {currentWeather.description}
                </div>
                <div>
                  <strong>Pressure:</strong> {currentWeather.pressure} hPa
                </div>
                <div>
                  <strong>Wind Speed:</strong> {currentWeather.wind_speed} m/s
                </div>
                <div>
                  <strong>Humidity:</strong> {currentWeather.humidity}%
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Status Footer */}
        <footer className="dashboard-footer">
          <div className="status-info">
            <span>
              🟢 Live Data from {dataSource} | 
              Last Updated: {lastUpdated || 'Never'} |
              {isAutoRefresh ? ' Auto-refresh: ON' : ' Auto-refresh: OFF'}
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
