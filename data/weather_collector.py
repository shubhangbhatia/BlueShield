import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json

class OpenWeatherCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
        
    def get_current_weather(self, lat=40.7128, lon=-74.0060):
        """Get current weather data for coastal location"""
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code}")
    
    def get_forecast_data(self, lat=40.7128, lon=-74.0060):
        """Get 5-day forecast data"""
        url = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code}")
    
    def get_historical_weather(self, lat=40.7128, lon=-74.0060, days_back=5):
        """Get historical weather data (max 5 days back for OpenWeather API)"""
        historical_data = []
        days_back = min(days_back, 5)  # OpenWeather API limit

        for i in range(days_back):
            target_date = datetime.now() - timedelta(days=i+1)  # API does not allow today
            timestamp = int(target_date.timestamp())
            url = f"{self.onecall_url}/timemachine"
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'metric'
            }
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    historical_data.append(data)
                    time.sleep(1)  # Be gentle with rate limits
                else:
                    print(f"Failed to get data for {target_date.date()} (status {response.status_code}): {response.text}")
            except Exception as e:
                print(f"Error getting historical data: {e}")
        return historical_data
    
    def extract_flood_risk_features(self, weather_data):
        """Extract features relevant to flood risk from weather data"""
        if isinstance(weather_data, list):
            # Handle forecast data (list of weather items)
            features = []
            for item in weather_data:
                if 'main' in item:
                    feature = self._extract_single_feature(item)
                    features.append(feature)
            return np.array(features)
        else:
            # Handle single weather data point
            return np.array([self._extract_single_feature(weather_data)])
    
    def _extract_single_feature(self, weather_item):
        """Extract single feature from weather data"""
        try:
            # Extract relevant features for coastal flood prediction
            pressure = weather_item.get('main', {}).get('pressure', 1013.25)
            wind_speed = weather_item.get('wind', {}).get('speed', 0)
            wind_deg = weather_item.get('wind', {}).get('deg', 0)
            humidity = weather_item.get('main', {}).get('humidity', 50)
            temp = weather_item.get('main', {}).get('temp', 15)
            
            # Calculate wind pressure component (affects storm surge)
            wind_pressure = wind_speed * np.sin(np.radians(wind_deg))
            
            # Create composite flood risk score
            # Lower pressure + high wind speed + high humidity = higher flood risk
            pressure_factor = (1013.25 - pressure) / 20  # Normalized pressure deviation
            wind_factor = wind_speed / 10  # Normalized wind speed
            humidity_factor = humidity / 100  # Normalized humidity
            
            flood_risk_score = pressure_factor + wind_factor + humidity_factor + (temp / 50)
            
            return max(0, flood_risk_score * 3 + 5)  # Scale to reasonable water level range
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return 5.0  # Default safe value

# Example coastal locations
COASTAL_LOCATIONS = {
    "new_york": {"lat": 40.7128, "lon": -74.0060, "name": "New York City"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
    "boston": {"lat": 42.3601, "lon": -71.0589, "name": "Boston, MA"},
    "san_francisco": {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco, CA"},
    "charleston": {"lat": 32.7765, "lon": -79.9311, "name": "Charleston, SC"}
}
