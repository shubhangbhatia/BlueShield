import React, { useEffect, useState } from 'react';
import './App.css'; // We'll create this for styling

function App() {
  const [features, setFeatures] = useState(Array(50).fill(0));
  const [forecast, setForecast] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);

  // Generate more realistic sensor data simulation
  const generateRealisticData = () => {
    const baseLevel = 5.0;
    const newFeatures = Array(50).fill(0).map((_, i) => {
      const trend = Math.sin(i * 0.1) * 2; // Sinusoidal trend
      const noise = (Math.random() - 0.5) * 1.5; // Random noise
      const timeEffect = i * 0.05; // Gradual increase over time
      return Math.max(0, baseLevel + trend + noise + timeEffect);
    });
    setFeatures(newFeatures);
  };

  // Fetch prediction from API
  async function fetchPrediction() {
    setLoading(true);
    setError(null);
    
    try {
      const inputData = { features };
      
      const response = await fetch('http://localhost:8000/predict/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("API response:", data);
      
      setForecast(data.forecast);
      setAnomaly(data.anomaly);
      setAlert(data.alert);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Prediction API error:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  // Auto-refresh effect
  useEffect(() => {
    if (isAutoRefresh) {
      fetchPrediction();
      const interval = setInterval(() => {
        generateRealisticData(); // Update sensor data
        fetchPrediction();
      }, 15000); // Every 15 seconds
      
      return () => clearInterval(interval);
    }
  }, [isAutoRefresh, features]);

  // Manual refresh
  const handleManualRefresh = () => {
    generateRealisticData();
    fetchPrediction();
  };

  // Risk level determination
  const getRiskLevel = () => {
    if (alert) return 'high';
    if (forecast > 8) return 'medium';
    return 'low';
  };

  const getRiskColor = () => {
    const level = getRiskLevel();
    switch(level) {
      case 'high': return '#dc3545';
      case 'medium': return '#ffc107';
      default: return '#28a745';
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🌊 BlueShied</h1>
        <div className="header-controls">
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
            Auto-refresh (15s)
          </label>
        </div>
      </header>

      <div className="dashboard-content">
        {/* Status Cards */}
        <div className="status-cards">
          <div className="card forecast-card">
            <div className="card-header">
              <h3>📊 Water Level Forecast</h3>
            </div>
            <div className="card-content">
              <div className="main-value">
                {loading ? (
                  <div className="loading-spinner">Loading...</div>
                ) : forecast !== null ? (
                  <span className="forecast-value">
                    {forecast.toFixed(2)} m
                  </span>
                ) : (
                  <span className="no-data">No data</span>
                )}
              </div>
              <div className="card-footer">
                Next 1-hour prediction
              </div>
            </div>
          </div>

          <div className="card anomaly-card">
            <div className="card-header">
              <h3>⚠️ Anomaly Detection</h3>
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
                Current sensor reading
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
                  className={`risk-level risk-${getRiskLevel()}`}
                  style={{ color: getRiskColor() }}
                >
                  {getRiskLevel().toUpperCase()}
                </span>
              </div>
              <div className="card-footer">
                Overall assessment
              </div>
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

        {/* Current Sensor Data Preview */}
        <div className="sensor-preview">
          <h3>📡 Recent Sensor Readings</h3>
          <div className="sensor-data">
            <div className="sensor-summary">
              <div>
                <strong>Latest Reading:</strong> {features[features.length - 1]?.toFixed(2)} m
              </div>
              <div>
                <strong>Average (Last 10):</strong> {
                  features.slice(-10).reduce((a, b) => a + b, 0) / 10
                }.toFixed(2)
              </div>
              <div>
                <strong>Min/Max:</strong> {Math.min(...features).toFixed(2)} / {Math.max(...features).toFixed(2)} m
              </div>
            </div>
          </div>
        </div>

        {/* Status Footer */}
        <footer className="dashboard-footer">
          <div className="status-info">
            <span>
              🟢 API Connected | 
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
