import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import pickle
from typing import List
import logging
from datetime import datetime
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Now import from data directory
from data.weather_collector import OpenWeatherCollector, COASTAL_LOCATIONS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blueshield_api")

app = FastAPI(title="BlueShield Coastal Early Warning API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(project_root, ".env"))
except ImportError:
    pass  # dotenv not installed, skip

# Load models at startup (adjust path to go up to project root)
try:
    models_path = os.path.join(project_root, "models")
    lstm_model = tf.keras.models.load_model(os.path.join(models_path, "lstm_model"))
    with open(os.path.join(models_path, "iso_forest.pkl"), "rb") as f:
        iso_forest = pickle.load(f)
    logger.info("✅ Models loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading models: {e}")
    lstm_model = None
    iso_forest = None

# Initialize weather collector
API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
weather_collector = OpenWeatherCollector(API_KEY) if API_KEY != "YOUR_API_KEY_HERE" else None

class InputData(BaseModel):
    features: List[float]

FORECAST_THRESHOLD = 8.0
EXPECTED_TIME_STEPS = 40  # Change from 50 to 40

@app.get("/")
def root():
    return {"message": "🌊 BlueShield Coastal Early Warning API is running!"}

@app.get("/locations")
def get_locations():
    """Get available coastal monitoring locations"""
    return COASTAL_LOCATIONS

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": lstm_model is not None and iso_forest is not None,
        "weather_api_configured": weather_collector is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict/")
async def predict(input_data: InputData):
    if lstm_model is None or iso_forest is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    x = np.array(input_data.features)
    if x.shape[0] != EXPECTED_TIME_STEPS:
        raise HTTPException(status_code=400, detail=f"Input features length must be {EXPECTED_TIME_STEPS}")

    try:
        # Prepare input for LSTM: (1, time_steps, 1)
        x_lstm = x.reshape(1, -1, 1)
        forecast = lstm_model.predict(x_lstm)[0][0]

        # Anomaly prediction uses only the last feature value
        x_iso = np.array([[x[-1]]])  # shape (1,1)
        anomaly = iso_forest.predict(x_iso)[0]

        alert = None
        risk_level = "LOW"
        
        if anomaly == -1:
            alert = "🚨 ANOMALY DETECTED - Unusual patterns in data!"
            risk_level = "HIGH"
        elif forecast > FORECAST_THRESHOLD:
            alert = "⚠️ FLOOD RISK ALERT - High water levels predicted!"
            risk_level = "HIGH"
        elif forecast > 6.5:
            risk_level = "MEDIUM"

        logger.info(f"Prediction: forecast={forecast}, anomaly={anomaly}, alert={alert}")

        return {
            "forecast": float(forecast),
            "anomaly": int(anomaly),
            "risk_level": risk_level,
            "alert": alert,
            "data_source": "Input Features",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

@app.get("/weather/{location}")
def get_weather(location: str = "new_york"):
    if weather_collector is None:
        raise HTTPException(status_code=500, detail="Weather API not configured")
    if location not in COASTAL_LOCATIONS:
        raise HTTPException(status_code=404, detail="Unknown location")
    loc = COASTAL_LOCATIONS[location]
    try:
        data = weather_collector.get_current_weather(lat=loc["lat"], lon=loc["lon"])
        return data
    except Exception as e:
        logger.error(f"Weather fetch error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Weather fetch error: {str(e)}")

@app.post("/predict-live/{location}")
def predict_live(location: str):
    if lstm_model is None or iso_forest is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    if weather_collector is None:
        raise HTTPException(status_code=500, detail="Weather API not configured")
    if location not in COASTAL_LOCATIONS:
        raise HTTPException(status_code=404, detail="Unknown location")
    loc = COASTAL_LOCATIONS[location]
    try:
        forecast_data = weather_collector.get_forecast_data(lat=loc["lat"], lon=loc["lon"])
        features = []
        for item in forecast_data.get('list', []):
            features.append(weather_collector._extract_single_feature(item))
        features = features[-EXPECTED_TIME_STEPS:]
        logger.info(f"Collected {len(features)} features for location {location}")
        if len(features) < EXPECTED_TIME_STEPS:
            logger.error("Not enough forecast data for prediction")
            raise HTTPException(status_code=400, detail="Not enough forecast data for prediction")
        x = np.array(features)
        x_lstm = x.reshape(1, -1, 1)
        forecast = lstm_model.predict(x_lstm)[0][0]
        x_iso = np.array([[x[-1]]])
        anomaly = iso_forest.predict(x_iso)[0]
        alert = None
        risk_level = "LOW"
        if anomaly == -1:
            alert = "🚨 ANOMALY DETECTED - Unusual patterns in data!"
            risk_level = "HIGH"
        elif forecast > FORECAST_THRESHOLD:
            alert = "⚠️ FLOOD RISK ALERT - High water levels predicted!"
            risk_level = "HIGH"
        elif forecast > 6.5:
            risk_level = "MEDIUM"

        # Calculate average, min, and max
        avg_feature = float(np.mean(features))
        min_feature = float(np.min(features))
        max_feature = float(np.max(features))

        return {
            "forecast": float(forecast),
            "anomaly": int(anomaly),
            "risk_level": risk_level,
            "alert": alert,
            "data_source": "OpenWeather Forecast API",
            "timestamp": datetime.now().isoformat(),
            "average_feature": avg_feature,
            "min_feature": min_feature,
            "max_feature": max_feature
        }
    except Exception as e:
        logger.error(f"Live prediction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Live prediction error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
