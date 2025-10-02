"""
Machine Learning model for soil property prediction using Random Forest.
Predicts soil characteristics based on location (lat, lon) and environmental features.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputRegressor


class SoilMLPredictor:
    """
    Random Forest-based soil property predictor.

    Predicts multiple soil properties simultaneously using location and
    environmental features derived from remote sensing and climate data.
    """

    def __init__(self, model_dir: str = "./data/models"):
        """
        Initialize soil ML predictor.

        Args:
            model_dir: Directory to save/load trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Target variables to predict
        self.target_variables = [
            'pH', 'BulkDensity', 'N', 'P', 'K', 'Ca', 'Mg', 'S',
            'Fe', 'Mn', 'Zn', 'Cu', 'B', 'soc20', 'snd20', 'cec20'
        ]

        # Feature columns (environmental predictors)
        self.feature_columns = [
            'lat', 'lon',                    # Location
            'bio1',                           # Annual mean temperature
            'bio12',                          # Annual precipitation
            'bio15',                          # Precipitation seasonality
            'bio7',                           # Temperature annual range
            'mdem',                           # Elevation
            'slope',                          # Slope
            'lstd', 'lstn',                  # Land surface temp (day/night)
            'alb',                            # Albedo
        ]

        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_metrics = {}

    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare features and targets from raw data.

        Args:
            df: Raw soil dataframe

        Returns:
            Tuple of (features, targets) DataFrames
        """
        # Select only rows with complete data for key variables
        required_cols = self.feature_columns + self.target_variables
        df_clean = df[required_cols].dropna()

        print(f"Data preparation: {len(df)} → {len(df_clean)} samples after removing NaN")

        # Separate features and targets
        X = df_clean[self.feature_columns].copy()
        y = df_clean[self.target_variables].copy()

        # Add derived features
        X['lat_abs'] = np.abs(X['lat'])  # Distance from equator
        X['temp_range_norm'] = X['bio7'] / (X['bio1'] + 273.15)  # Normalized temp range
        X['precip_per_degree'] = X['bio12'] / (X['bio1'] + 273.15)  # Precipitation efficiency
        X['elevation_lat_interaction'] = X['mdem'] * X['lat_abs']  # Elevation-latitude interaction

        return X, y

    def train_models(
        self,
        data_path: str,
        test_size: float = 0.2,
        n_estimators: int = 100,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train Random Forest models for all soil properties.

        Args:
            data_path: Path to training data CSV
            test_size: Fraction of data for testing
            n_estimators: Number of trees in random forest
            random_state: Random seed for reproducibility

        Returns:
            Dictionary with training metrics
        """
        print("="*60)
        print("Training Soil Property Prediction Models")
        print("="*60)

        # Load data
        print(f"\nLoading data from {data_path}...")
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} samples with {len(df.columns)} columns")

        # Prepare data
        X, y = self.prepare_data(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        print(f"\nTrain set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        print(f"Features: {len(X.columns)}")
        print(f"Target variables: {len(self.target_variables)}")

        # Train separate model for each target variable
        print("\nTraining models...")

        for target in self.target_variables:
            print(f"\n  Training model for: {target}")

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train Random Forest
            rf_model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=20,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features='sqrt',
                random_state=random_state,
                n_jobs=-1,
                verbose=0
            )

            rf_model.fit(X_train_scaled, y_train[target])

            # Evaluate
            train_score = rf_model.score(X_train_scaled, y_train[target])
            test_score = rf_model.score(X_test_scaled, y_test[target])

            # Cross-validation
            cv_scores = cross_val_score(
                rf_model, X_train_scaled, y_train[target],
                cv=5, scoring='r2', n_jobs=-1
            )

            print(f"    Train R²: {train_score:.3f}")
            print(f"    Test R²: {test_score:.3f}")
            print(f"    CV R² (5-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

            # Store model and scaler
            self.models[target] = rf_model
            self.scalers[target] = scaler

            # Store feature importance
            self.feature_importance[target] = dict(
                zip(X.columns, rf_model.feature_importances_)
            )

            # Store metrics
            self.model_metrics[target] = {
                'train_r2': train_score,
                'test_r2': test_score,
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std()
            }

        # Save models
        self.save_models()

        print("\n" + "="*60)
        print("Training Complete!")
        print("="*60)

        # Summary
        avg_test_r2 = np.mean([m['test_r2'] for m in self.model_metrics.values()])
        print(f"\nAverage Test R²: {avg_test_r2:.3f}")
        print(f"Models saved to: {self.model_dir}")

        return self.model_metrics

    def predict(
        self,
        lat: float,
        lon: float,
        bio1: Optional[float] = None,
        bio12: Optional[float] = None,
        mdem: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Predict soil properties for a given location.

        Args:
            lat: Latitude
            lon: Longitude
            bio1: Annual mean temperature (optional, estimated if not provided)
            bio12: Annual precipitation (optional, estimated if not provided)
            mdem: Elevation (optional, estimated if not provided)

        Returns:
            Dictionary with predicted soil properties
        """
        if not self.models:
            # Try to load models
            if not self.load_models():
                raise ValueError("No trained models available. Run train_models() first.")

        # Estimate missing environmental features
        features = self._prepare_prediction_features(lat, lon, bio1, bio12, mdem)

        # Create feature DataFrame
        feature_names = self.feature_columns + [
            'lat_abs', 'temp_range_norm', 'precip_per_degree', 'elevation_lat_interaction'
        ]
        X = pd.DataFrame([features], columns=feature_names)

        # Predict each soil property
        predictions = {}

        for target in self.target_variables:
            # Scale features
            X_scaled = self.scalers[target].transform(X)

            # Predict
            pred = self.models[target].predict(X_scaled)[0]

            # Ensure reasonable ranges
            pred = self._constrain_prediction(target, pred)

            predictions[target] = float(pred)

        # Determine soil texture from sand content
        texture = self._get_soil_texture(predictions['snd20'])

        return {
            'location': {'lat': lat, 'lon': lon},
            'pH': round(predictions['pH'], 2),
            'texture': texture,
            'organic_carbon_pct': round(predictions['soc20'], 2),
            'sand_pct': round(predictions['snd20'], 1),
            'bulk_density': round(predictions['BulkDensity'], 2),
            'cec': round(predictions['cec20'], 1),
            'nutrients': {
                'nitrogen_pct': round(predictions['N'], 3),
                'phosphorus_ppm': round(predictions['P'], 1),
                'potassium_ppm': round(predictions['K'], 1),
                'calcium_ppm': round(predictions['Ca'], 1),
                'magnesium_ppm': round(predictions['Mg'], 1),
                'sulfur_ppm': round(predictions['S'], 2),
            },
            'micronutrients': {
                'iron_ppm': round(predictions['Fe'], 1),
                'manganese_ppm': round(predictions['Mn'], 1),
                'zinc_ppm': round(predictions['Zn'], 2),
                'copper_ppm': round(predictions['Cu'], 2),
                'boron_ppm': round(predictions['B'], 2),
            },
            'prediction_method': 'Random Forest ML Model',
            'confidence': 'medium'  # Could be improved with prediction intervals
        }

    def _fetch_environmental_data(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Fetch real environmental data from APIs.

        Uses Open-Meteo for climate data and Open-Elevation for elevation.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with environmental features
        """
        env_data = {}

        try:
            # Fetch elevation from Open-Elevation API
            elev_url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            elev_response = requests.get(elev_url, timeout=10)

            if elev_response.status_code == 200:
                elev_data = elev_response.json()
                env_data['mdem'] = float(elev_data['results'][0]['elevation'])
            else:
                env_data['mdem'] = None

        except Exception as e:
            print(f"  Warning: Could not fetch elevation: {e}")
            env_data['mdem'] = None

        try:
            # Fetch climate data from Open-Meteo (use historical averages)
            climate_url = "https://archive-api.open-meteo.com/v1/archive"
            from datetime import datetime, timedelta

            # Get last year's data for climate
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)

            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_mean,precipitation_sum,temperature_2m_max,temperature_2m_min',
                'timezone': 'auto'
            }

            climate_response = requests.get(climate_url, params=params, timeout=15)

            if climate_response.status_code == 200:
                climate_data = climate_response.json()
                daily = climate_data['daily']

                # Calculate annual means
                temps = [t for t in daily['temperature_2m_mean'] if t is not None]
                temps_max = [t for t in daily['temperature_2m_max'] if t is not None]
                temps_min = [t for t in daily['temperature_2m_min'] if t is not None]
                precip = [p for p in daily['precipitation_sum'] if p is not None]

                if temps:
                    bio1 = np.mean(temps) + 273.15  # Convert to Kelvin
                    env_data['bio1'] = bio1

                    # Temperature range (max - min)
                    if temps_max and temps_min:
                        env_data['bio7'] = np.mean(temps_max) - np.mean(temps_min)
                    else:
                        env_data['bio7'] = bio1 * 0.3

                    # Land surface temperature estimates
                    env_data['lstd'] = bio1 + 5
                    env_data['lstn'] = bio1 - 5
                else:
                    env_data['bio1'] = None
                    env_data['bio7'] = None
                    env_data['lstd'] = None
                    env_data['lstn'] = None

                if precip:
                    env_data['bio12'] = sum(precip)  # Annual precipitation

                    # Precipitation seasonality (coefficient of variation)
                    if len(precip) > 0:
                        monthly_precip = [sum(precip[i:i+30]) for i in range(0, len(precip), 30)]
                        if len(monthly_precip) > 1:
                            env_data['bio15'] = (np.std(monthly_precip) / np.mean(monthly_precip)) * 100 if np.mean(monthly_precip) > 0 else 50
                        else:
                            env_data['bio15'] = 50
                    else:
                        env_data['bio15'] = 50
                else:
                    env_data['bio12'] = None
                    env_data['bio15'] = 50

            else:
                env_data['bio1'] = None
                env_data['bio12'] = None
                env_data['bio7'] = None
                env_data['bio15'] = 50
                env_data['lstd'] = None
                env_data['lstn'] = None

        except Exception as e:
            print(f"  Warning: Could not fetch climate data: {e}")
            env_data['bio1'] = None
            env_data['bio12'] = None
            env_data['bio7'] = None
            env_data['bio15'] = 50
            env_data['lstd'] = None
            env_data['lstn'] = None

        return env_data

    def _prepare_prediction_features(
        self,
        lat: float,
        lon: float,
        bio1: Optional[float],
        bio12: Optional[float],
        mdem: Optional[float]
    ) -> List[float]:
        """
        Prepare features for prediction, fetching real data from APIs.

        Args:
            lat: Latitude
            lon: Longitude
            bio1: Annual mean temperature (Kelvin) - fetched if None
            bio12: Annual precipitation (mm) - fetched if None
            mdem: Elevation (m) - fetched if None

        Returns:
            List of feature values
        """
        # Fetch real environmental data if needed
        if bio1 is None or bio12 is None or mdem is None:
            print(f"  Fetching environmental data for ({lat:.3f}, {lon:.3f})...")
            env_data = self._fetch_environmental_data(lat, lon)

            if bio1 is None:
                bio1 = env_data.get('bio1')
            if bio12 is None:
                bio12 = env_data.get('bio12')
            if mdem is None:
                mdem = env_data.get('mdem')

            bio7 = env_data.get('bio7')
            bio15 = env_data.get('bio15', 50)
            lstd = env_data.get('lstd')
            lstn = env_data.get('lstn')
        else:
            bio7 = None
            bio15 = 50
            lstd = None
            lstn = None

        # Fallback to estimates if API fetch failed
        if bio1 is None:
            # Simple model: temperature decreases with latitude
            lat_abs = abs(lat)
            bio1 = 300 - (lat_abs / 90) * 50  # Rough approximation

        if bio12 is None:
            # Simple model: higher precipitation near equator
            lat_abs = abs(lat)
            if lat_abs < 30:
                bio12 = 1500 - lat_abs * 10
            else:
                bio12 = 800 - (lat_abs - 30) * 8
            bio12 = max(bio12, 200)

        if mdem is None:
            # Default elevation based on latitude (very rough)
            mdem = 500

        if bio7 is None:
            bio7 = bio1 * 0.3

        if lstd is None:
            lstd = bio1 + 5

        if lstn is None:
            lstn = bio1 - 5

        # Other derived features
        alb = 180  # Albedo (moderate default)
        slope = 3  # Slope (moderate default)

        # Derived features
        lat_abs = abs(lat)
        temp_range_norm = bio7 / (bio1 + 0.001)
        precip_per_degree = bio12 / (bio1 + 0.001)
        elevation_lat_interaction = mdem * lat_abs

        return [
            lat, lon, bio1, bio12, bio15, bio7, mdem, slope,
            lstd, lstn, alb, lat_abs, temp_range_norm,
            precip_per_degree, elevation_lat_interaction
        ]

    def _constrain_prediction(self, target: str, value: float) -> float:
        """Constrain predictions to reasonable ranges."""
        constraints = {
            'pH': (3.0, 9.5),
            'BulkDensity': (0.8, 2.0),
            'N': (0.01, 2.0),  # %
            'P': (1.0, 500.0),  # ppm
            'K': (10.0, 5000.0),  # ppm
            'Ca': (100.0, 10000.0),  # ppm
            'Mg': (10.0, 3000.0),  # ppm
            'S': (1.0, 100.0),  # ppm
            'Fe': (5.0, 500.0),  # ppm
            'Mn': (5.0, 500.0),  # ppm
            'Zn': (0.1, 50.0),  # ppm
            'Cu': (0.1, 20.0),  # ppm
            'B': (0.1, 5.0),  # ppm
            'soc20': (0.1, 20.0),  # % organic carbon
            'snd20': (0.0, 100.0),  # % sand
            'cec20': (1.0, 50.0),  # cmol/kg
        }

        if target in constraints:
            min_val, max_val = constraints[target]
            return np.clip(value, min_val, max_val)

        return value

    def _get_soil_texture(self, sand_pct: float) -> str:
        """Determine soil texture from sand percentage."""
        if sand_pct >= 85:
            return "sand"
        elif sand_pct >= 70:
            return "sandy loam"
        elif sand_pct >= 50:
            return "loam"
        elif sand_pct >= 35:
            return "clay loam"
        elif sand_pct >= 20:
            return "clay"
        else:
            return "heavy clay"

    def save_models(self):
        """Save trained models and scalers to disk."""
        model_path = self.model_dir / 'soil_rf_models.pkl'
        scaler_path = self.model_dir / 'soil_scalers.pkl'
        metrics_path = self.model_dir / 'model_metrics.pkl'

        with open(model_path, 'wb') as f:
            pickle.dump(self.models, f)

        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scalers, f)

        with open(metrics_path, 'wb') as f:
            pickle.dump(self.model_metrics, f)

        print(f"\n✓ Models saved to {model_path}")
        print(f"✓ Scalers saved to {scaler_path}")
        print(f"✓ Metrics saved to {metrics_path}")

    def load_models(self) -> bool:
        """
        Load trained models from disk.

        Returns:
            True if models loaded successfully, False otherwise
        """
        model_path = self.model_dir / 'soil_rf_models.pkl'
        scaler_path = self.model_dir / 'soil_scalers.pkl'
        metrics_path = self.model_dir / 'model_metrics.pkl'

        if not all([model_path.exists(), scaler_path.exists()]):
            return False

        try:
            with open(model_path, 'rb') as f:
                self.models = pickle.load(f)

            with open(scaler_path, 'rb') as f:
                self.scalers = pickle.load(f)

            if metrics_path.exists():
                with open(metrics_path, 'rb') as f:
                    self.model_metrics = pickle.load(f)

            print(f"✓ Loaded {len(self.models)} trained models from {model_path}")
            return True

        except Exception as e:
            print(f"Error loading models: {e}")
            return False

    def get_feature_importance(self, target: str, top_n: int = 10) -> Dict[str, float]:
        """
        Get top N most important features for a target variable.

        Args:
            target: Target variable name
            top_n: Number of top features to return

        Returns:
            Dictionary of {feature: importance}
        """
        if target not in self.feature_importance:
            return {}

        importance = self.feature_importance[target]
        sorted_importance = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return dict(sorted_importance[:top_n])
