"""
Rainfall forecasting service using Facebook Prophet and Open-Meteo API.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import requests
from prophet import Prophet

from .crops import normalize_crop


class RainfallForecastService:
    """Service for fetching historical rainfall data and forecasting using Prophet."""

    def __init__(self):
        """Initialize the rainfall forecast service."""
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"

    def fetch_historical_rainfall(
        self,
        lat: float,
        lon: float,
        days_back: int = 365
    ) -> pd.DataFrame:
        """
        Fetch historical rainfall data from Open-Meteo API.

        Args:
            lat: Latitude
            lon: Longitude
            days_back: Number of days of historical data to fetch

        Returns:
            DataFrame with columns ['ds', 'y'] for Prophet
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'daily': 'precipitation_sum,temperature_2m_mean',
            'timezone': 'auto'
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'daily' not in data:
                raise ValueError("No daily data in API response")

            # Create DataFrame
            df = pd.DataFrame({
                'ds': pd.to_datetime(data['daily']['time']),
                'y': data['daily']['precipitation_sum'],  # Precipitation in mm
                'temperature': data['daily']['temperature_2m_mean']
            })

            # Handle missing values
            df['y'] = df['y'].fillna(0)
            df['temperature'] = df['temperature'].fillna(df['temperature'].mean())

            return df

        except requests.RequestException as e:
            print(f"Error fetching rainfall data: {e}")
            raise
        except KeyError as e:
            print(f"Error parsing API response: {e}")
            raise

    def train_and_forecast(
        self,
        historical_data: pd.DataFrame,
        forecast_days: int = 14
    ) -> pd.DataFrame:
        """
        Train Prophet model and generate forecast.

        Args:
            historical_data: DataFrame with columns ['ds', 'y']
            forecast_days: Number of days to forecast

        Returns:
            DataFrame with forecast including yhat, yhat_lower, yhat_upper
        """
        # Initialize Prophet with sensible parameters for rainfall
        model = Prophet(
            seasonality_mode='multiplicative',
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,  # Less flexible to avoid overfitting
            seasonality_prior_scale=10.0,
            interval_width=0.8
        )

        # Add temperature as additional regressor if available
        if 'temperature' in historical_data.columns:
            model.add_regressor('temperature')

        # Fit the model
        model.fit(historical_data)

        # Create future dataframe
        future = model.make_future_dataframe(periods=forecast_days)

        # Add temperature values for future dates (use recent average)
        if 'temperature' in historical_data.columns:
            recent_temp_mean = historical_data['temperature'].tail(30).mean()
            future = future.merge(
                historical_data[['ds', 'temperature']],
                on='ds',
                how='left'
            )
            future['temperature'] = future['temperature'].fillna(recent_temp_mean)

        # Generate forecast
        forecast = model.predict(future)

        # Ensure no negative rainfall predictions
        forecast['yhat'] = forecast['yhat'].clip(lower=0)
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
        forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)

        return forecast

    def get_rainfall_forecast(
        self,
        lat: float,
        lon: float,
        days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Get rainfall forecast for a location.

        Args:
            lat: Latitude
            lon: Longitude
            days_ahead: Number of days to forecast

        Returns:
            Dictionary with forecast summary and details
        """
        try:
            # Fetch historical data (1 year)
            print(f"Fetching historical rainfall data for ({lat}, {lon})...")
            historical_data = self.fetch_historical_rainfall(lat, lon, days_back=365)

            if len(historical_data) < 30:
                raise ValueError("Insufficient historical data for forecasting")

            # Train and forecast
            print(f"Training Prophet model and forecasting {days_ahead} days...")
            forecast = self.train_and_forecast(historical_data, forecast_days=days_ahead)

            # Get forecast for future dates only
            future_forecast = forecast[forecast['ds'] > historical_data['ds'].max()]

            # Calculate summary statistics
            total_rainfall = future_forecast['yhat'].sum()
            avg_daily_rainfall = future_forecast['yhat'].mean()
            max_daily_rainfall = future_forecast['yhat'].max()
            rainy_days = (future_forecast['yhat'] > 1.0).sum()  # Days with >1mm rain

            # Get next 7 days and next 14 days separately
            next_7_days = future_forecast.head(7)
            next_14_days = future_forecast.head(14)

            # Recent rainfall (last 30 days average)
            recent_rainfall = historical_data['y'].tail(30).mean()

            return {
                'location': {'lat': lat, 'lon': lon},
                'forecast_period_days': days_ahead,
                'next_7_days': {
                    'total_rainfall_mm': round(next_7_days['yhat'].sum(), 1),
                    'avg_daily_mm': round(next_7_days['yhat'].mean(), 1),
                    'rainy_days': int((next_7_days['yhat'] > 1.0).sum())
                },
                'next_14_days': {
                    'total_rainfall_mm': round(next_14_days['yhat'].sum(), 1),
                    'avg_daily_mm': round(next_14_days['yhat'].mean(), 1),
                    'rainy_days': int((next_14_days['yhat'] > 1.0).sum()),
                    'max_daily_mm': round(next_14_days['yhat'].max(), 1)
                },
                'recent_conditions': {
                    'last_30_days_avg_mm': round(recent_rainfall, 1),
                    'last_7_days_total_mm': round(historical_data['y'].tail(7).sum(), 1)
                },
                'daily_forecast': [
                    {
                        'date': row['ds'].strftime('%Y-%m-%d'),
                        'rainfall_mm': round(row['yhat'], 1),
                        'rainfall_lower': round(row['yhat_lower'], 1),
                        'rainfall_upper': round(row['yhat_upper'], 1)
                    }
                    for _, row in future_forecast.iterrows()
                ],
                'model_info': {
                    'historical_days': len(historical_data),
                    'model': 'Facebook Prophet',
                    'data_source': 'Open-Meteo Historical Weather API'
                }
            }

        except Exception as e:
            print(f"Error generating rainfall forecast: {e}")
            raise

    def get_rainfall_recommendation(
        self,
        forecast: Dict[str, Any],
        crop: str
    ) -> str:
        """
        Generate recommendation based on rainfall forecast and crop type.

        Args:
            forecast: Forecast dictionary from get_rainfall_forecast
            crop: Crop type

        Returns:
            Recommendation string
        """
        next_14 = forecast['next_14_days']
        total_rainfall = next_14['total_rainfall_mm']
        rainy_days = next_14['rainy_days']

        crop = normalize_crop(crop)

        # Define crop water requirements (mm for 2 weeks)
        crop_water_needs = {
            'maize': {'min': 50, 'optimal': 100, 'max': 150},
            'beans': {'min': 40, 'optimal': 80, 'max': 120},
            'tomato': {'min': 60, 'optimal': 100, 'max': 140},
            'rice': {'min': 100, 'optimal': 150, 'max': 200},
            'wheat': {'min': 40, 'optimal': 70, 'max': 100},
            'potato': {'min': 50, 'optimal': 90, 'max': 130},
            'sorghum': {'min': 40, 'optimal': 80, 'max': 120},
            'cassava': {'min': 45, 'optimal': 85, 'max': 130},
            'sweet potato': {'min': 50, 'optimal': 90, 'max': 130},
            'banana': {'min': 70, 'optimal': 130, 'max': 180},
            'groundnut': {'min': 45, 'optimal': 75, 'max': 110},
            'soybean': {'min': 55, 'optimal': 90, 'max': 130},
            'cowpea': {'min': 40, 'optimal': 75, 'max': 110},
            'pigeon pea': {'min': 45, 'optimal': 85, 'max': 120},
            'millet': {'min': 35, 'optimal': 70, 'max': 110},
            'sunflower': {'min': 40, 'optimal': 90, 'max': 130},
            'onion': {'min': 45, 'optimal': 85, 'max': 120},
            'cabbage': {'min': 60, 'optimal': 110, 'max': 150},
            'carrot': {'min': 45, 'optimal': 80, 'max': 120},
            'chili': {'min': 50, 'optimal': 90, 'max': 130},
        }

        # Get water needs for crop (default if not found)
        water_needs = crop_water_needs.get(crop, {'min': 50, 'optimal': 100, 'max': 150})

        # Generate recommendation
        if total_rainfall < water_needs['min']:
            return f"Low rainfall expected ({total_rainfall}mm). Irrigation strongly recommended for {crop}. Consider drip irrigation or mulching to conserve moisture."
        elif total_rainfall < water_needs['optimal']:
            return f"Moderate rainfall expected ({total_rainfall}mm). Supplemental irrigation may be needed for optimal {crop} growth. Monitor soil moisture closely."
        elif total_rainfall <= water_needs['max']:
            return f"Good rainfall expected ({total_rainfall}mm over {rainy_days} days). Excellent conditions for {crop} growth. Ensure proper drainage systems are in place."
        else:
            return f"Heavy rainfall expected ({total_rainfall}mm). Risk of waterlogging for {crop}. Ensure adequate drainage, consider raised beds, and monitor for fungal diseases."

    def get_simple_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get simplified forecast for quick responses (7-day outlook).

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Simplified forecast dictionary
        """
        params = {
            'latitude': lat,
            'longitude': lon,
            'daily': 'precipitation_sum,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
            'timezone': 'auto',
            'forecast_days': 7
        }

        try:
            response = requests.get(self.forecast_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            daily = data['daily']

            return {
                'total_rainfall_mm': round(sum(daily['precipitation_sum']), 1),
                'avg_temp_c': round(np.mean(daily['temperature_2m_max']), 1),
                'avg_precipitation_probability': round(np.mean(daily['precipitation_probability_max']), 0)
            }

        except Exception as e:
            print(f"Error fetching simple forecast: {e}")
            # Return default values if API fails
            return {
                'total_rainfall_mm': 35.0,
                'avg_temp_c': 24.0,
                'avg_precipitation_probability': 50.0
            }
