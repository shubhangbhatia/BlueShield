import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

def load_and_preprocess(file_path: str):
    # Load CSV
    df = pd.read_csv(file_path)
    
    # Parse timestamp column if present
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
    # Handle missing values by forward fill then backward fill
    df = df.fillna(method='ffill').fillna(method='bfill')
    
    # Separate features and target (example: water_level as target)
    # Adjust feature columns as per your CSV structure
    feature_cols = [col for col in df.columns if col != 'water_level' and col != 'timestamp']
    target_col = 'water_level'
    
    X = df[feature_cols].values if feature_cols else np.empty((len(df), 0))
    y = df[target_col].values
    
    # Normalize features to [0,1]
    scaler = MinMaxScaler()
    if X.size > 0:
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = X  # No features to scale
    
    # Split into train and test sets (80-20 split)
    test_size = 0.2
    if X.size > 0:
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=test_size, shuffle=False)
    else:
        # If no features, just split target vector to maintain time series order
        split_index = int(len(y)*(1-test_size))
        y_train, y_test = y[:split_index], y[split_index:]
        X_train = X_test = None
    
    return df, X_train, X_test, y_train, y_test

def plot_data(df):
    plt.figure(figsize=(12, 6))
    if 'timestamp' in df.columns:
        plt.plot(df['timestamp'], df['water_level'], label='Water Level')
        plt.xlabel('Time')
    else:
        plt.plot(df['water_level'], label='Water Level')
        plt.xlabel('Index')
    plt.ylabel('Water Level')
    plt.title('Water Level Time Series')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    file_path = "data/sample.csv"  # Adjust path as needed
    df, X_train, X_test, y_train, y_test = load_and_preprocess(file_path)
    
    print("Train data shape:", X_train.shape if X_train is not None else None, y_train.shape)
    print("Test data shape:", X_test.shape if X_test is not None else None, y_test.shape)
    
    # Visualize the time series data
    plot_data(df)
