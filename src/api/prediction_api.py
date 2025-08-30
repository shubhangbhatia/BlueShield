import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import pickle
from typing import List
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coastal_early_warning")

app = FastAPI(title="Coastal Early Warning Prediction API")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust if frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load saved models at startup
lstm_model = tf.keras.models.load_model("models/lstm_model")

with open("models/iso_forest.pkl", "rb") as f:
    iso_forest = pickle.load(f)

class InputData(BaseModel):
    features: List[float]

FORECAST_THRESHOLD = 10.0  # Adjust based on domain knowledge
EXPECTED_TIME_STEPS = 50   # Must match LSTM training time_steps

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        raise

@app.get("/")
def root():
    return {"message": "Coastal Early Warning API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/predict/")
async def predict(input_data: InputData):
    x = np.array(input_data.features)
    if x.shape[0] != EXPECTED_TIME_STEPS:
        raise HTTPException(status_code=400, detail=f"Input features length must be {EXPECTED_TIME_STEPS}")

    try:
        # Prepare input for LSTM: (1, time_steps, 1)
        x_lstm = x.reshape(1, -1, 1)
        forecast = lstm_model.predict(x_lstm)[0][0]

        # Anomaly prediction uses only the last feature value as input for Isolation Forest
        x_iso = np.array([[x[-1]]])
        print(f"x_iso shape: {x_iso.shape}")  # Should print (1, 1)
        anomaly = iso_forest.predict(x_iso)[0]


        alert = None
        if anomaly == -1 or forecast > FORECAST_THRESHOLD:
            alert = "ALERT: Potential flood risk detected."

        logger.info(f"Prediction: forecast={forecast}, anomaly={anomaly}, alert={alert}")

        return {
            "forecast": float(forecast),
            "anomaly": int(anomaly),
            "alert": alert
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
