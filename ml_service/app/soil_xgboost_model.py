"""
XGBoost model for soil property prediction with hyperparameter tuning.
Superior to Random Forest for complex non-linear relationships.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score


class SoilXGBoostPredictor:
    """
    XGBoost-based soil property predictor with hyperparameter tuning.

    Uses gradient boosting for superior performance on complex soil-climate relationships.
    """

    def __init__(self, model_dir: str = "./data/models"):
        """
        Initialize XGBoost soil predictor.

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

        # Feature columns
        self.feature_columns = [
            'lat', 'lon', 'bio1', 'bio12', 'bio15', 'bio7',
            'mdem', 'slope', 'lstd', 'lstn', 'alb',
        ]

        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_metrics = {}
        self.best_params = {}

    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare features and targets from raw data."""
        df_clean = self._clean_dataframe(df)

        required_cols = self.feature_columns + self.target_variables
        df_clean = df_clean[required_cols].dropna()

        print(f"Data preparation: {len(df)} → {len(df_clean)} samples after cleaning and removing NaN")

        X = df_clean[self.feature_columns].copy()
        y = df_clean[self.target_variables].copy()

        # Add derived features
        X['lat_abs'] = np.abs(X['lat'])
        X['temp_range_norm'] = X['bio7'] / (X['bio1'] + 273.15)
        X['precip_per_degree'] = X['bio12'] / (X['bio1'] + 273.15)
        X['elevation_lat_interaction'] = X['mdem'] * X['lat_abs']

        return X, y

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean raw dataframe to reduce noise/outliers before model training."""
        df = df.copy()

        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if not numeric_cols:
            return df

        # Replace inf/-inf with NaN so they can be dropped by downstream dropna
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

        # Enforce non-negative constraints for nutrient and texture columns
        non_negative_cols = {
            'cec20', 'ecec20', 'hp20', 'ph20', 'slope', 'snd20', 'soc20', 'BulkDensity',
            'N', 'P', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Mn', 'Zn', 'Cu', 'B'
        }
        existing_non_negative = [col for col in non_negative_cols if col in df.columns]
        for col in existing_non_negative:
            mask = df[col] < 0
            if mask.any():
                df.loc[mask, col] = np.nan

        # Clip extreme outliers to the 1st–99th percentile range per column
        clip_quantiles = {}
        for col in numeric_cols:
            q_low, q_high = df[col].quantile([0.01, 0.99])
            if pd.notna(q_low) and pd.notna(q_high) and q_low < q_high:
                clip_quantiles[col] = (q_low, q_high)

        for col, (low, high) in clip_quantiles.items():
            df[col] = df[col].clip(lower=low, upper=high)

        # Drop exact duplicate records to avoid overweighting particular sites
        df = df.drop_duplicates(subset=['lat', 'lon', 'PID'], keep='first', ignore_index=True)

        return df

    def get_hyperparameter_grid(self, target: str) -> Dict:
        """
        Get hyperparameter grid for tuning based on target variable.

        Different parameters for different properties based on their complexity.
        """
        # Base grid for most properties
        base_grid = {
            'max_depth': [4, 6, 8],
            'learning_rate': [0.01, 0.05, 0.1],
            'n_estimators': [100, 200, 300],
            'min_child_weight': [1, 3, 5],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [0.8, 0.9, 1.0],
            'gamma': [0, 0.1, 0.2]
        }

        # Simplified grid for harder-to-predict properties (faster training)
        simple_grid = {
            'max_depth': [4, 6],
            'learning_rate': [0.05, 0.1],
            'n_estimators': [100, 200],
            'min_child_weight': [1, 3],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0],
            'gamma': [0, 0.1]
        }

        # Use simple grid for micronutrients and challenging properties
        if target in ['P', 'S', 'Zn', 'Cu']:
            return simple_grid
        else:
            return base_grid

    def train_models(
        self,
        data_path: str,
        test_size: float = 0.2,
        tune_hyperparams: bool = False,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Train XGBoost models with hyperparameter tuning.

        Args:
            data_path: Path to training data CSV
            test_size: Fraction of data for testing
            tune_hyperparams: Whether to perform grid search (slower but better)
            random_state: Random seed

        Returns:
            Dictionary with training metrics
        """
        print("="*60)
        print("Training XGBoost Soil Property Prediction Models")
        print("="*60)

        # Load data
        print(f"\nLoading data from {data_path}...")
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} samples")

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

        if tune_hyperparams:
            print("\n🔧 Hyperparameter tuning enabled (this will take longer)")
        else:
            print("\n⚡ Using default XGBoost parameters (hyperparameter tuning disabled)")

        print("\nTraining models...")

        for i, target in enumerate(self.target_variables, 1):
            print(f"\n[{i}/{len(self.target_variables)}] Training model for: {target}")

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            if tune_hyperparams:
                # Hyperparameter tuning with GridSearchCV
                print(f"  🔍 Performing grid search...")

                param_grid = self.get_hyperparameter_grid(target)

                # Base XGBoost model
                xgb_model = xgb.XGBRegressor(
                    objective='reg:squarederror',
                    random_state=random_state,
                    n_jobs=-1,
                    tree_method='hist'  # Faster
                )

                # Grid search with 3-fold CV
                grid_search = GridSearchCV(
                    xgb_model,
                    param_grid,
                    cv=3,
                    scoring='r2',
                    n_jobs=-1,
                    verbose=0
                )

                grid_search.fit(X_train_scaled, y_train[target])

                # Best model
                best_model = grid_search.best_estimator_
                self.best_params[target] = grid_search.best_params_

                print(f"  ✓ Best params: max_depth={grid_search.best_params_['max_depth']}, "
                      f"lr={grid_search.best_params_['learning_rate']}, "
                      f"n_est={grid_search.best_params_['n_estimators']}")

            else:
                # Use good default parameters
                best_model = xgb.XGBRegressor(
                    max_depth=6,
                    learning_rate=0.05,
                    n_estimators=200,
                    min_child_weight=3,
                    subsample=0.8,
                    colsample_bytree=0.9,
                    gamma=0.1,
                    objective='reg:squarederror',
                    random_state=random_state,
                    n_jobs=-1,
                    tree_method='hist'
                )

                best_model.fit(X_train_scaled, y_train[target])
                self.best_params[target] = "default"

            # Evaluate
            train_pred = best_model.predict(X_train_scaled)
            test_pred = best_model.predict(X_test_scaled)

            train_r2 = r2_score(y_train[target], train_pred)
            test_r2 = r2_score(y_test[target], test_pred)
            train_mse = mean_squared_error(y_train[target], train_pred)
            test_mse = mean_squared_error(y_test[target], test_pred)
            train_rmse = np.sqrt(train_mse)
            test_rmse = np.sqrt(test_mse)

            # Cross-validation
            cv_scores = cross_val_score(
                best_model, X_train_scaled, y_train[target],
                cv=5, scoring='r2', n_jobs=-1
            )

            print(f"  📊 Train R²: {train_r2:.3f} | Test R²: {test_r2:.3f}")
            print(f"  📊 Train RMSE: {train_rmse:.3f} | Test RMSE: {test_rmse:.3f}")
            print(f"  📊 CV R² (5-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

            # Store model and metrics
            self.models[target] = best_model
            self.scalers[target] = scaler

            # Feature importance
            self.feature_importance[target] = dict(
                zip(X.columns, best_model.feature_importances_)
            )

            # Store metrics
            self.model_metrics[target] = {
                'train_r2': train_r2,
                'test_r2': test_r2,
                'train_mse': train_mse,
                'test_mse': test_mse,
                'train_rmse': train_rmse,
                'test_rmse': test_rmse,
                'cv_r2_mean': cv_scores.mean(),
                'cv_r2_std': cv_scores.std()
            }

        # Save models
        self.save_models()

        print("\n" + "="*60)
        print("Training Complete!")
        print("="*60)

        avg_test_r2 = np.mean([m['test_r2'] for m in self.model_metrics.values()])
        avg_test_rmse = np.mean([m['test_rmse'] for m in self.model_metrics.values()])
        print(f"\nAverage Test R²: {avg_test_r2:.3f}")
        print(f"Average Test RMSE: {avg_test_rmse:.3f}")
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
        """Predict soil properties using XGBoost models."""
        if not self.models:
            if not self.load_models():
                raise ValueError("No trained models available. Run train_models() first.")

        # Prepare features (reuse from RF model)
        features = self._prepare_prediction_features(lat, lon, bio1, bio12, mdem)

        # Feature names
        feature_names = self.feature_columns + [
            'lat_abs', 'temp_range_norm', 'precip_per_degree', 'elevation_lat_interaction'
        ]
        X = pd.DataFrame([features], columns=feature_names)

        # Predict
        predictions = {}

        for target in self.target_variables:
            X_scaled = self.scalers[target].transform(X)
            pred = self.models[target].predict(X_scaled)[0]
            pred = self._constrain_prediction(target, pred)
            predictions[target] = float(pred)

        # Determine texture
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
            'prediction_method': 'XGBoost ML Model',
            'confidence': 'high'
        }

    # Reuse helper methods from Random Forest model
    def _fetch_environmental_data(self, lat: float, lon: float) -> Dict[str, float]:
        """Fetch environmental data from APIs."""
        env_data = {}

        try:
            # Elevation
            elev_url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            elev_response = requests.get(elev_url, timeout=10)
            if elev_response.status_code == 200:
                env_data['mdem'] = float(elev_response.json()['results'][0]['elevation'])
            else:
                env_data['mdem'] = None
        except Exception as e:
            print(f"  Warning: Could not fetch elevation: {e}")
            env_data['mdem'] = None

        try:
            # Climate data
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

            climate_response = requests.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params=params,
                timeout=15
            )

            if climate_response.status_code == 200:
                daily = climate_response.json()['daily']
                temps = [t for t in daily['temperature_2m_mean'] if t is not None]
                temps_max = [t for t in daily['temperature_2m_max'] if t is not None]
                temps_min = [t for t in daily['temperature_2m_min'] if t is not None]
                precip = [p for p in daily['precipitation_sum'] if p is not None]

                if temps:
                    bio1 = np.mean(temps) + 273.15
                    env_data['bio1'] = bio1
                    env_data['bio7'] = np.mean(temps_max) - np.mean(temps_min) if temps_max and temps_min else bio1 * 0.3
                    env_data['lstd'] = bio1 + 5
                    env_data['lstn'] = bio1 - 5
                else:
                    env_data['bio1'] = env_data['bio7'] = env_data['lstd'] = env_data['lstn'] = None

                if precip:
                    env_data['bio12'] = sum(precip)
                    monthly_precip = [sum(precip[i:i+30]) for i in range(0, len(precip), 30)]
                    if len(monthly_precip) > 1 and np.mean(monthly_precip) > 0:
                        env_data['bio15'] = (np.std(monthly_precip) / np.mean(monthly_precip)) * 100
                    else:
                        env_data['bio15'] = 50
                else:
                    env_data['bio12'] = env_data['bio15'] = None
            else:
                env_data.update({'bio1': None, 'bio12': None, 'bio7': None, 'bio15': None, 'lstd': None, 'lstn': None})

        except Exception as e:
            print(f"  Warning: Could not fetch climate data: {e}")
            env_data.update({'bio1': None, 'bio12': None, 'bio7': None, 'bio15': None, 'lstd': None, 'lstn': None})

        return env_data

    def _prepare_prediction_features(
        self,
        lat: float,
        lon: float,
        bio1: Optional[float],
        bio12: Optional[float],
        mdem: Optional[float]
    ) -> List[float]:
        """Prepare features with API fetching."""
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
            bio7 = bio15 = lstd = lstn = None

        # Fallbacks
        if bio1 is None:
            bio1 = 300 - (abs(lat) / 90) * 50
        if bio12 is None:
            bio12 = 1500 - abs(lat) * 10 if abs(lat) < 30 else max(800 - (abs(lat) - 30) * 8, 200)
        if mdem is None:
            mdem = 500
        if bio7 is None:
            bio7 = bio1 * 0.3
        if lstd is None:
            lstd = bio1 + 5
        if lstn is None:
            lstn = bio1 - 5

        alb = 180
        slope = 3
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
            'N': (0.01, 2.0),
            'P': (1.0, 500.0),
            'K': (10.0, 5000.0),
            'Ca': (100.0, 10000.0),
            'Mg': (10.0, 3000.0),
            'S': (1.0, 100.0),
            'Fe': (5.0, 500.0),
            'Mn': (5.0, 500.0),
            'Zn': (0.1, 50.0),
            'Cu': (0.1, 20.0),
            'B': (0.1, 5.0),
            'soc20': (0.1, 20.0),
            'snd20': (0.0, 100.0),
            'cec20': (1.0, 50.0),
        }
        if target in constraints:
            return np.clip(value, *constraints[target])
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
        """Save trained XGBoost models."""
        model_path = self.model_dir / 'soil_xgboost_models.pkl'
        scaler_path = self.model_dir / 'soil_xgboost_scalers.pkl'
        metrics_path = self.model_dir / 'xgboost_metrics.pkl'
        params_path = self.model_dir / 'xgboost_best_params.pkl'

        with open(model_path, 'wb') as f:
            pickle.dump(self.models, f)
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scalers, f)
        with open(metrics_path, 'wb') as f:
            pickle.dump(self.model_metrics, f)
        with open(params_path, 'wb') as f:
            pickle.dump(self.best_params, f)

        print(f"\n✓ XGBoost models saved to {model_path}")

    def load_models(self) -> bool:
        """Load trained XGBoost models."""
        model_path = self.model_dir / 'soil_xgboost_models.pkl'
        scaler_path = self.model_dir / 'soil_xgboost_scalers.pkl'

        if not all([model_path.exists(), scaler_path.exists()]):
            return False

        try:
            with open(model_path, 'rb') as f:
                self.models = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                self.scalers = pickle.load(f)

            metrics_path = self.model_dir / 'xgboost_metrics.pkl'
            if metrics_path.exists():
                with open(metrics_path, 'rb') as f:
                    self.model_metrics = pickle.load(f)

            print(f"✓ Loaded {len(self.models)} XGBoost models")
            return True
        except Exception as e:
            print(f"Error loading XGBoost models: {e}")
            return False
