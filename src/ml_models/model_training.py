import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.ensemble import IsolationForest
import pickle


def create_lstm_dataset(series, time_steps=50):
    X, y = [], []
    for i in range(len(series) - time_steps):
        X.append(series[i:i + time_steps])
        y.append(series[i + time_steps])
    return np.array(X), np.array(y)


def train_lstm_model(series):
    time_steps = 50

    # Create dataset
    X, y = create_lstm_dataset(series, time_steps)
    print(f"Inside train_lstm_model: X shape: {X.shape}, y shape: {y.shape}")

    if X.size == 0:
        raise ValueError(f"No training samples created. Input series length: {len(series)}. Need more data.")

    # Reshape for LSTM input: (samples, timesteps, features)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = Sequential([
        LSTM(64, activation='relu', input_shape=(time_steps, 1)),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=10, batch_size=32, verbose=2)

    return model


def train_isolation_forest(X_train):
    clf = IsolationForest(contamination=0.05, random_state=42)
    clf.fit(X_train)
    return clf


if __name__ == "__main__":
    # Load data
    data = pd.read_csv("data/sample.csv")

    # Show columns and unique metric types for debugging
    print("CSV columns:", data.columns)
    print("Unique metric types:", data['metric_type'].unique())

    # Filter rows where metric_type is sea_level (represents water level)
    water_level_data = data[data['metric_type'] == 'sea_level']['metric_value'].fillna(method='ffill').values
    series = water_level_data

    print("Series length:", len(series))
    if len(series) <= 50:
        raise ValueError("Input series too short for LSTM training (need >50 data points).")

    # Train LSTM for forecasting
    lstm_model = train_lstm_model(series)

    # Prepare features for anomaly detection using last 200 points (or less if shorter)
    last_points = series[-200:] if len(series) >= 200 else series
    features = last_points.reshape(-1, 1)

    # Train Isolation Forest for anomaly detection
    iso_forest = train_isolation_forest(features)

    # Predict anomalies (-1 indicates anomaly)
    preds = iso_forest.predict(features)
    print("Anomaly predictions (last points):", preds)

    # Save LSTM model (TensorFlow SavedModel format)
    lstm_model.save("models/lstm_model")

    # Save Isolation Forest model (using pickle)
    with open("models/iso_forest.pkl", "wb") as f:
        pickle.dump(iso_forest, f)

    print("Models saved successfully.")
