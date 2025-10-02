"""
Soil data service for querying soil characteristics by location.
Uses the soil data CSV files in data/soil_data/
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any, Tuple, List
import pandas as pd
import numpy as np
from scipy.spatial import KDTree

from .crops import normalize_crop
from .soil_xgboost_model import SoilXGBoostPredictor


class SoilDataService:
    """Service for querying soil characteristics by geographic location."""

    EAST_AFRICA_BOUNDS = {
        'lat_min': -12.0,
        'lat_max': 8.0,
        'lon_min': 28.0,
        'lon_max': 42.0,
    }

    def __init__(
        self,
        data_dir: str = "./data/soil_data",
        soil_predictor: Optional[SoilXGBoostPredictor] = None
    ):
        """
        Initialize soil data service.

        Args:
            data_dir: Directory containing soil data CSV files
        """
        self.data_dir = Path(data_dir)
        self.soil_data = None
        self.kdtree = None
        self.soil_predictor = soil_predictor
        self.load_soil_data()

    def load_soil_data(self):
        """Load soil data from CSV file and build spatial index."""
        train_path = self.data_dir / "Train.csv"

        if not train_path.exists():
            print(f"Warning: Soil data not found at {train_path}")
            self.soil_data = None
            return

        try:
            print(f"Loading soil data from {train_path}...")
            # Load only necessary columns to save memory
            cols_to_load = [
                'lat', 'lon', 'pH', 'BulkDensity', 'N', 'P', 'K', 'Ca', 'Mg',
                'S', 'Fe', 'Mn', 'Zn', 'Cu', 'B', 'soc20', 'snd20', 'cec20',
                'bio12', 'bio1'  # Precipitation and temperature
            ]

            # Read CSV
            df = pd.read_csv(train_path, usecols=cols_to_load)

            # Filter to East Africa bounds (approx: lat -12 to 8, lon 28 to 42)
            east_africa_mask = (
                (df['lat'] >= -12.0) & (df['lat'] <= 8.0) &
                (df['lon'] >= 28.0) & (df['lon'] <= 42.0)
            )
            df = df[east_africa_mask]

            if df.empty:
                print("Warning: No soil records found within East Africa bounds."
                      " Field dataset will be skipped; falling back to model estimates only.")
                self.soil_data = None
                self.kdtree = None
                return

            # Remove rows with missing critical values
            df = df.dropna(subset=['lat', 'lon', 'pH'])

            print(f"Loaded {len(df)} soil data points")

            # Store the dataframe
            self.soil_data = df

            # Build KDTree for efficient nearest neighbor search
            coords = df[['lat', 'lon']].values
            self.kdtree = KDTree(coords)

            print("Soil data loaded and spatial index built successfully")

        except Exception as e:
            print(f"Error loading soil data: {e}")
            self.soil_data = None
            self.kdtree = None

    def get_nearest_soil_data(
        self,
        lat: float,
        lon: float,
        k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get soil characteristics for nearest location using k-nearest neighbors.

        Args:
            lat: Latitude
            lon: Longitude
            k: Number of nearest neighbors to average

        Returns:
            Dictionary with soil characteristics, or None if data unavailable
        """
        self._ensure_east_africa(lat, lon)

        if self.soil_data is None or self.kdtree is None:
            print("Soil data not available")
            return None

        try:
            # Find k nearest neighbors
            query_point = np.array([[lat, lon]])
            distances, indices = self.kdtree.query(query_point, k=k)

            # Get nearest soil samples
            nearest_samples = self.soil_data.iloc[indices[0]]

            # Calculate weighted average (inverse distance weighting)
            # Add small epsilon to avoid division by zero
            weights = 1 / (distances[0] + 0.0001)
            weights = weights / weights.sum()

            # Calculate weighted averages for numeric columns
            soil_params = {}

            numeric_cols = ['pH', 'BulkDensity', 'N', 'P', 'K', 'Ca', 'Mg',
                          'S', 'Fe', 'Mn', 'Zn', 'Cu', 'B', 'soc20', 'snd20', 'cec20']

            for col in numeric_cols:
                if col in nearest_samples.columns:
                    values = nearest_samples[col].values
                    # Handle NaN values
                    valid_mask = ~np.isnan(values)
                    if valid_mask.any():
                        weighted_val = np.average(values[valid_mask], weights=weights[valid_mask] / weights[valid_mask].sum())
                        soil_params[col] = float(weighted_val)
                    else:
                        soil_params[col] = None

            # Determine soil texture based on sand content (snd20)
            texture = self._get_soil_texture(soil_params.get('snd20'))

            # Calculate distance to nearest point
            nearest_distance_km = distances[0][0] * 111  # Rough conversion to km

            return self._format_observed_profile(
                lat=lat,
                lon=lon,
                soil_params=soil_params,
                texture=texture,
                k=k,
                distances=distances
            )

        except Exception as e:
            print(f"Error querying soil data: {e}")
            return None

    def get_enriched_soil_profile(
        self,
        lat: float,
        lon: float,
        crop: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """Combine observed data, ML predictions, and crop targets."""
        crop = normalize_crop(crop)

        observed = self.get_nearest_soil_data(lat, lon, k=k)
        model_prediction = None
        if self.soil_predictor is not None:
            try:
                model_prediction = self._normalize_model_profile(
                    self.soil_predictor.predict(lat, lon)
                )
            except Exception as exc:
                print(f"Warning: Soil model prediction failed: {exc}")

        blended = self._blend_profiles(observed, model_prediction)
        crop_targets = self._get_crop_targets(crop)
        crop_alignment = self._evaluate_crop_alignment(blended, crop_targets)

        return {
            'observed': observed,
            'model_estimate': model_prediction,
            'blended': blended,
            'crop_targets': crop_targets,
            'crop_alignment': crop_alignment
        }

    def _get_soil_texture(self, sand_pct: Optional[float]) -> str:
        """
        Determine soil texture from sand percentage.

        Args:
            sand_pct: Sand percentage (0-100)

        Returns:
            Soil texture classification
        """
        if sand_pct is None:
            return "loam"

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

    def get_soil_recommendation(
        self,
        soil_data: Dict[str, Any],
        crop: str
    ) -> str:
        """
        Generate soil management recommendation based on soil data and crop.

        Args:
            soil_data: Soil data dictionary from get_nearest_soil_data
            crop: Crop type

        Returns:
            Recommendation string
        """
        if not soil_data:
            return "Soil data unavailable. Conduct soil test for specific recommendations."

        ph = soil_data.get('pH', 6.5)
        texture = soil_data.get('texture', 'loam')
        organic_carbon = soil_data.get('organic_carbon_pct', 2.0)
        nutrients = soil_data.get('nutrients', {})
        nitrogen = nutrients.get('nitrogen_pct', 0.15)
        phosphorus = nutrients.get('phosphorus_ppm', 20)

        crop = normalize_crop(crop)

        # pH recommendations
        ph_targets = {
            'maize': (5.5, 7.5),
            'beans': (6.0, 7.5),
            'wheat': (5.5, 7.5),
            'rice': (5.0, 7.0),
            'tomato': (5.5, 6.8),
            'potato': (5.2, 6.5),
            'sorghum': (5.5, 7.5),
            'cassava': (5.5, 6.5),
            'sweet potato': (5.5, 6.5),
            'banana': (5.5, 6.5),
            'groundnut': (5.5, 6.5),
            'soybean': (6.0, 6.8),
            'cowpea': (5.5, 6.5),
            'pigeon pea': (5.0, 6.5),
            'millet': (5.5, 7.0),
            'sunflower': (6.0, 7.5),
            'onion': (6.0, 7.0),
            'cabbage': (6.0, 7.5),
            'carrot': (6.0, 6.8),
            'chili': (6.0, 6.8),
        }

        optimal_ph_range = ph_targets.get(crop, (6.0, 7.0))

        # Generate recommendation
        recommendations = []

        # pH recommendation
        if ph < optimal_ph_range[0]:
            recommendations.append(f"Soil is acidic (pH {ph}). Apply lime at 2-3 tons/ha to raise pH for optimal {crop} growth.")
        elif ph > optimal_ph_range[1]:
            recommendations.append(f"Soil is alkaline (pH {ph}). Add sulfur or organic matter to lower pH for {crop}.")
        else:
            recommendations.append(f"Soil pH ({ph}) is optimal for {crop}.")

        # Organic matter recommendation
        if organic_carbon < 1.5:
            recommendations.append(f"Low organic matter ({organic_carbon}%). Apply compost or manure at 5-10 tons/ha to improve soil health.")
        elif organic_carbon < 2.5:
            recommendations.append(f"Moderate organic matter ({organic_carbon}%). Maintain with crop residues and cover crops.")
        else:
            recommendations.append(f"Good organic matter level ({organic_carbon}%). Continue current practices.")

        # Nitrogen recommendation
        legumes = {
            'beans', 'peas', 'soybean', 'groundnut', 'cowpea', 'pigeon pea'
        }

        if crop in legumes:
            if nitrogen < 0.1:
                recommendations.append(f"Legume crop detected. Inoculate seeds and apply a small starter dose (20-30 kg/ha) of nitrogen for {crop} to support early growth.")
            else:
                recommendations.append(f"Nitrogen levels suit {crop}. Focus on rhizobium inoculation and phosphorus to sustain nodulation.")
        else:
            if nitrogen < 0.1:
                recommendations.append(f"Low nitrogen. Apply 100-150 kg/ha of nitrogen fertilizer for {crop}, split into 2-3 applications.")
            elif nitrogen < 0.2:
                recommendations.append(f"Moderate nitrogen. Apply 50-100 kg/ha nitrogen fertilizer for {crop}.")

        # Phosphorus recommendation
        if phosphorus < 15:
            recommendations.append(f"Low phosphorus ({phosphorus} ppm). Apply phosphate fertilizer (DAP or TSP) at 40-60 kg P2O5/ha.")

        # Return top 3 recommendations
        return " ".join(recommendations[:3])

    def is_available(self) -> bool:
        """Check if soil data is available."""
        return self.soil_data is not None and self.kdtree is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded soil data."""
        if not self.is_available():
            return {'available': False}

        return {
            'available': True,
            'num_samples': len(self.soil_data),
            'lat_range': (float(self.soil_data['lat'].min()), float(self.soil_data['lat'].max())),
            'lon_range': (float(self.soil_data['lon'].min()), float(self.soil_data['lon'].max())),
            'coverage': 'Global' if len(self.soil_data) > 1000 else 'Regional'
        }

    # ------------------------
    # Internal helpers
    # ------------------------

    def _format_observed_profile(
        self,
        lat: float,
        lon: float,
        soil_params: Dict[str, Optional[float]],
        texture: str,
        k: int,
        distances: np.ndarray
    ) -> Dict[str, Any]:
        nearest_distance_km = distances[0][0] * 111
        profile = {
            'location': {'lat': lat, 'lon': lon},
            'nearest_distance_km': round(nearest_distance_km, 1),
            'num_samples_averaged': k,
            'pH': round(soil_params.get('pH', 6.5), 2) if soil_params.get('pH') else 6.5,
            'texture': texture,
            'organic_carbon_pct': round(soil_params.get('soc20', 2.0), 2) if soil_params.get('soc20') else 2.0,
            'sand_pct': round(soil_params.get('snd20', 40.0), 1) if soil_params.get('snd20') else 40.0,
            'bulk_density': round(soil_params.get('BulkDensity', 1.4), 2) if soil_params.get('BulkDensity') else 1.4,
            'cec': round(soil_params.get('cec20', 15.0), 1) if soil_params.get('cec20') else 15.0,
            'nutrients': {
                'nitrogen_pct': round(soil_params.get('N', 0.15), 3) if soil_params.get('N') else 0.15,
                'phosphorus_ppm': round(soil_params.get('P', 20.0), 1) if soil_params.get('P') else 20.0,
                'potassium_ppm': round(soil_params.get('K', 150.0), 1) if soil_params.get('K') else 150.0,
                'calcium_ppm': round(soil_params.get('Ca', 2000.0), 1) if soil_params.get('Ca') else 2000.0,
                'magnesium_ppm': round(soil_params.get('Mg', 300.0), 1) if soil_params.get('Mg') else 300.0,
                'sulfur_ppm': round(soil_params.get('S', 10.0), 2) if soil_params.get('S') else 10.0,
            },
            'micronutrients': {
                'iron_ppm': round(soil_params.get('Fe', 50.0), 1) if soil_params.get('Fe') else 50.0,
                'manganese_ppm': round(soil_params.get('Mn', 30.0), 1) if soil_params.get('Mn') else 30.0,
                'zinc_ppm': round(soil_params.get('Zn', 1.5), 2) if soil_params.get('Zn') else 1.5,
                'copper_ppm': round(soil_params.get('Cu', 2.0), 2) if soil_params.get('Cu') else 2.0,
                'boron_ppm': round(soil_params.get('B', 0.5), 2) if soil_params.get('B') else 0.5,
            },
            'data_quality': {
                'samples_used': k,
                'max_distance_km': round(distances[0][-1] * 111, 1),
                'confidence': 'high' if nearest_distance_km < 50 else 'medium' if nearest_distance_km < 100 else 'low'
            },
            'source': 'field_dataset'
        }
        return profile

    def _normalize_model_profile(self, model_profile: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            key: model_profile.get(key)
            for key in ['pH', 'texture', 'organic_carbon_pct', 'sand_pct', 'bulk_density', 'cec']
        }
        normalized['nutrients'] = model_profile.get('nutrients', {}).copy()
        normalized['micronutrients'] = model_profile.get('micronutrients', {}).copy()
        normalized['location'] = model_profile.get('location', {})
        normalized['data_quality'] = {
            'confidence': model_profile.get('confidence', 'medium'),
            'source': model_profile.get('prediction_method', 'XGBoost ML Model')
        }
        normalized['source'] = 'ml_prediction'
        return normalized

    def _blend_profiles(
        self,
        observed: Optional[Dict[str, Any]],
        model: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if not observed and not model:
            return None

        if observed and not model:
            return observed
        if model and not observed:
            return model

        # Both available – compute weighted blend
        obs_conf = observed.get('data_quality', {}).get('confidence', 'medium')
        conf_weights = {'high': 0.65, 'medium': 0.5, 'low': 0.35}
        w_obs = conf_weights.get(obs_conf, 0.5)
        w_model = 1 - w_obs

        blended = {}
        for key in ['pH', 'organic_carbon_pct', 'sand_pct', 'bulk_density', 'cec']:
            obs_val = observed.get(key)
            model_val = model.get(key)
            blended[key] = self._weighted_value(obs_val, model_val, w_obs, w_model)

        # Determine texture from blended sand percentage
        blended['texture'] = self._get_soil_texture(blended.get('sand_pct'))
        blended['nutrients'] = self._blend_nested_metrics(
            observed.get('nutrients', {}),
            model.get('nutrients', {}),
            w_obs,
            w_model
        )
        blended['micronutrients'] = self._blend_nested_metrics(
            observed.get('micronutrients', {}),
            model.get('micronutrients', {}),
            w_obs,
            w_model
        )
        blended['source'] = 'blended_dataset_model'
        blended['data_quality'] = {
            'observed_confidence': observed.get('data_quality', {}).get('confidence'),
            'model_confidence': model.get('data_quality', {}).get('confidence'),
            'blend_weights': {'observed': round(w_obs, 2), 'model': round(w_model, 2)}
        }
        blended['location'] = observed.get('location') or model.get('location')
        return blended

    def _blend_nested_metrics(
        self,
        observed_metrics: Dict[str, Optional[float]],
        model_metrics: Dict[str, Optional[float]],
        w_obs: float,
        w_model: float
    ) -> Dict[str, Optional[float]]:
        keys = set(observed_metrics.keys()) | set(model_metrics.keys())
        blended = {}
        for key in keys:
            blended[key] = self._weighted_value(
                observed_metrics.get(key),
                model_metrics.get(key),
                w_obs,
                w_model
            )
        return blended

    def _weighted_value(
        self,
        observed_val: Optional[float],
        model_val: Optional[float],
        w_obs: float,
        w_model: float
    ) -> Optional[float]:
        if observed_val is None and model_val is None:
            return None
        if observed_val is None:
            return model_val
        if model_val is None:
            return observed_val
        return round((observed_val * w_obs) + (model_val * w_model), 3)

    def _get_crop_targets(self, crop: str) -> Dict[str, Tuple[float, float]]:
        targets: Dict[str, Tuple[float, float]] = {
            'maize': {
                'pH': (5.8, 7.0),
                'organic_carbon_pct': (1.5, 2.5),
                'nitrogen_pct': (0.12, 0.18),
                'phosphorus_ppm': (20, 40),
                'potassium_ppm': (150, 250)
            },
            'beans': {
                'pH': (6.0, 7.5),
                'organic_carbon_pct': (1.8, 3.0),
                'nitrogen_pct': (0.10, 0.16),
                'phosphorus_ppm': (25, 45),
                'potassium_ppm': (140, 220)
            },
            'groundnut': {
                'pH': (5.5, 6.5),
                'organic_carbon_pct': (1.0, 2.0),
                'nitrogen_pct': (0.08, 0.14),
                'phosphorus_ppm': (15, 35),
                'potassium_ppm': (120, 200)
            },
            'soybean': {
                'pH': (6.0, 6.8),
                'organic_carbon_pct': (1.5, 3.0),
                'nitrogen_pct': (0.10, 0.15),
                'phosphorus_ppm': (25, 40),
                'potassium_ppm': (140, 220)
            },
            'cassava': {
                'pH': (5.5, 6.5),
                'organic_carbon_pct': (1.0, 2.0),
                'nitrogen_pct': (0.08, 0.12),
                'phosphorus_ppm': (15, 30),
                'potassium_ppm': (150, 250)
            },
            'tomato': {
                'pH': (6.0, 6.8),
                'organic_carbon_pct': (1.5, 2.5),
                'nitrogen_pct': (0.12, 0.18),
                'phosphorus_ppm': (30, 50),
                'potassium_ppm': (200, 320)
            },
            'cabbage': {
                'pH': (6.0, 7.5),
                'organic_carbon_pct': (2.0, 3.5),
                'nitrogen_pct': (0.20, 0.30),
                'phosphorus_ppm': (25, 45),
                'potassium_ppm': (180, 300)
            },
            'onion': {
                'pH': (6.0, 7.0),
                'organic_carbon_pct': (1.8, 3.0),
                'nitrogen_pct': (0.12, 0.18),
                'phosphorus_ppm': (20, 40),
                'potassium_ppm': (150, 240)
            },
            'banana': {
                'pH': (5.5, 6.5),
                'organic_carbon_pct': (2.0, 3.5),
                'nitrogen_pct': (0.18, 0.28),
                'phosphorus_ppm': (20, 35),
                'potassium_ppm': (250, 400)
            }
        }

        default_targets = {
            'pH': (6.0, 7.0),
            'organic_carbon_pct': (1.5, 2.5),
            'nitrogen_pct': (0.1, 0.2),
            'phosphorus_ppm': (20, 40),
            'potassium_ppm': (150, 250)
        }

        return targets.get(crop, default_targets)

    def _evaluate_crop_alignment(
        self,
        soil_profile: Optional[Dict[str, Any]],
        crop_targets: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        if not soil_profile:
            return {'status': 'no_soil_data'}

        result: Dict[str, Any] = {}
        for metric, target_range in crop_targets.items():
            current = self._get_metric_value(soil_profile, metric)
            status = self._compare_to_target(current, target_range)
            result[metric] = {
                'current': current,
                'target_range': target_range,
                'status': status
            }
        return result

    def _ensure_east_africa(self, lat: float, lon: float):
        bounds = self.EAST_AFRICA_BOUNDS
        if not (
            bounds['lat_min'] <= lat <= bounds['lat_max'] and
            bounds['lon_min'] <= lon <= bounds['lon_max']
        ):
            raise ValueError(
                "The location is not found within East Africa. Kindly input a location within East Africa."
            )

    def _get_metric_value(self, soil_profile: Dict[str, Any], metric: str) -> Optional[float]:
        if metric == 'pH':
            return soil_profile.get('pH')
        if metric == 'organic_carbon_pct':
            return soil_profile.get('organic_carbon_pct')
        if metric == 'nitrogen_pct':
            return soil_profile.get('nutrients', {}).get('nitrogen_pct')
        if metric == 'phosphorus_ppm':
            return soil_profile.get('nutrients', {}).get('phosphorus_ppm')
        if metric == 'potassium_ppm':
            return soil_profile.get('nutrients', {}).get('potassium_ppm')
        return None

    def _compare_to_target(
        self,
        current: Optional[float],
        target_range: Tuple[float, float]
    ) -> str:
        if current is None:
            return 'unknown'
        low, high = target_range
        if current < low:
            return 'low'
        if current > high:
            return 'high'
        return 'optimal'
