import pandas as pd

def preprocess_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df = df.fillna(method='ffill')

    return df

data = preprocess_csv("sample.csv")
print(data.head())
