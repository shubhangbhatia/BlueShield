from fastapi.testclient import TestClient
from src.api.prediction_api import app

client = TestClient(app)

def test_predict_endpoint():
    response = client.post("/predict/", json={"features": [0.1]*50})
    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data
    assert "anomaly" in data
