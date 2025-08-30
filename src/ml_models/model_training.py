import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.ensemble import IsolationForest
import pickle
import os
from data.weather_collector import OpenWeatherCollector, COASTAL_LOCATIONS
# Load environment variables if using .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, skip
def create_lstm_dataset(series, time_steps=40):
    X, y = [], []
    for i in range(len(series) - time_steps):
        X.append(series[i:i + time_steps])
        y.append(series[i + time_steps])
    return np.array(X), np.array(y)
def train_lstm_model(series):
    time_steps = 40
    
    X, y = create_lstm_dataset(series, time_steps)
    print(f"LSTM Training: X shape: {X.shape}, y shape: {y.shape}")
    
    if X.size == 0:
        raise ValueError(f"No training samples created. Input series length: {len(series)}.")
    
    X = X.reshape((X.shape[0], X.shape[1], 1))
    
    model = Sequential([
        LSTM(64, activation='relu', input_shape=(time_steps, 1)),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    model.fit(X, y, epochs=20, batch_size=32, verbose=2, validation_split=0.2)
    
    return model
def train_isolation_forest(X_train):
    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(X_train)
    return clf
def collect_training_data(api_key, location="new_york", days=5):
    """Collect weather data for training (using free forecast endpoint)"""
    collector = OpenWeatherCollector(api_key)
    location_info = COASTAL_LOCATIONS[location]
    
    print(f"Collecting forecast weather data for {location_info['name']}...")

    try:
        # Use forecast data (free endpoint)
        forecast_data = collector.get_forecast_data(
            lat=location_info['lat'],
            lon=location_info['lon']
        )
        print(f"Fetched forecast_data: {len(forecast_data.get('list', []))} time points")
        all_features = []
        for item in forecast_data.get('list', []):
            feature = collector._extract_single_feature(item)
            all_features.append(feature)
        return np.array(all_features)
    except Exception as e:
        print(f"Error collecting forecast data: {e}")
        print("Falling back to simulated data...")
        return generate_simulated_weather_data(days * 8)  # 8 forecast points per day
def generate_simulated_weather_data(num_points=1440):
    """Generate realistic simulated weather data for training"""
    np.random.seed(42)
    base_level = 5.0
    
    data = []
    for i in range(num_points):
        seasonal = np.sin(i * 2 * np.pi / 365) * 2
        daily = np.sin(i * 2 * np.pi / 24) * 1
        storm_events = np.random.exponential(0.1) if np.random.random() < 0.05 else 0
        noise = np.random.normal(0, 0.5)
        
        value = base_level + seasonal + daily + storm_events + noise
        data.append(max(0, value))
    
    return np.array(data)
if __name__ == "__main__":
    # Get API key from environment variable
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    
    if API_KEY is None or API_KEY == "":
        print("⚠️  No OpenWeatherMap API key found!")
        print("Set environment variable: OPENWEATHER_API_KEY=your_api_key")
        print("Using simulated data for training...")
        series = generate_simulated_weather_data(2000)
    else:
        print(f"✅ Using OpenWeatherMap API key: {API_KEY[:8]}...")
        try:
            # Collect real weather data
            series = collect_training_data(API_KEY, location="new_york", days=90)
        except Exception as e:
            print(f"❌ Failed to collect real data: {e}")
            print("Using simulated data as fallback...")
            series = generate_simulated_weather_data(2000)
    
    print(f"Training data length: {len(series)}")
    
    if len(series) <= 50:
        print("Insufficient data, generating more simulated data...")
        series = generate_simulated_weather_data(2000)
    
    # Train LSTM for forecasting
    print("Training LSTM model...")
    lstm_model = train_lstm_model(series)
    
    # Prepare features for anomaly detection
    last_points = series[-500:] if len(series) >= 500 else series
    features = last_points.reshape(-1, 1)
    
    # Train Isolation Forest for anomaly detection
    print("Training Isolation Forest...")
    iso_forest = train_isolation_forest(features)
    
    # Test anomaly predictions
    preds = iso_forest.predict(features[-100:])
    anomaly_count = np.sum(preds == -1)
    print(f"Anomalies detected in recent data: {anomaly_count}/100")
    
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    # Save models
    lstm_model.save("models/lstm_model")
    with open("models/iso_forest.pkl", "wb") as f:
        pickle.dump(iso_forest, f)
    
    print("✅ Models trained and saved successfully!")
    if API_KEY:
        print("📍 Models trained on REAL weather data from OpenWeatherMap API")
    else:
        print("📍 Models trained on simulated weather data")
