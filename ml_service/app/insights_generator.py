"""
Insights generation service combining rainfall forecasts and soil data.
"""

from typing import Dict, List, Any, Optional
from .rainfall_forecast import RainfallForecastService
from .soil_xgboost_model import SoilXGBoostPredictor
from .soil_service import SoilDataService
from .crops import normalize_crop


class InsightsGenerator:
    """Generate agricultural insights based on ML forecasts and soil data."""

    def __init__(
        self,
        rainfall_service: Optional[RainfallForecastService] = None,
        soil_predictor: Optional[SoilXGBoostPredictor] = None,
        soil_data_service: Optional[SoilDataService] = None
    ):
        """
        Initialize insights generator.

        Args:
            rainfall_service: Rainfall forecast service instance
            soil_predictor: XGBoost soil predictor instance
        """
        self.rainfall_service = rainfall_service or RainfallForecastService()
        self.soil_predictor = soil_predictor or SoilXGBoostPredictor()
        self.soil_data_service = soil_data_service or SoilDataService(soil_predictor=self.soil_predictor)

    def generate_insights(
        self,
        lat: float,
        lon: float,
        crop: str,
        use_full_forecast: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive agricultural insights.

        Args:
            lat: Latitude
            lon: Longitude
            crop: Crop type
            use_full_forecast: If True, use Prophet for 14-day forecast (slower).
                             If False, use simple 7-day API forecast (faster).

        Returns:
            Dictionary with forecast, soil data, and actionable tips
        """
        print(f"Generating insights for {crop} at ({lat}, {lon})...")

        # Get rainfall forecast
        if use_full_forecast:
            try:
                rainfall_forecast = self.rainfall_service.get_rainfall_forecast(lat, lon, days_ahead=14)
                forecast_summary = {
                    'next_7_days': rainfall_forecast['next_7_days'],
                    'next_14_days': rainfall_forecast['next_14_days'],
                    'recent_conditions': rainfall_forecast['recent_conditions'],
                    'model': 'Prophet ML Model'
                }
            except Exception as e:
                print(f"Error with Prophet forecast, falling back to simple: {e}")
                forecast_summary = self._get_simple_forecast_summary(lat, lon)
        else:
            forecast_summary = self._get_simple_forecast_summary(lat, lon)

        # Get soil predictions using XGBoost ML model
        soil_profile = self.soil_data_service.get_enriched_soil_profile(lat, lon, crop)
        soil_data = (
            soil_profile.get('blended')
            or soil_profile.get('model_estimate')
            or soil_profile.get('observed')
        )

        if soil_data:
            print(
                f"  ✓ Soil profile source={soil_data.get('source')}, "
                f"pH={soil_data.get('pH')}, texture={soil_data.get('texture')}"
            )
        else:
            print("Warning: No soil profile available, using defaults")
            soil_data = self._get_default_soil_data()
            soil_profile['blended'] = soil_data

        # Generate actionable tips
        canonical_crop = normalize_crop(crop)

        tips = self._generate_tips(forecast_summary, soil_data, canonical_crop)

        return {
            'forecast': forecast_summary,
            'soil': self._build_soil_response(soil_data, soil_profile),
            'tips': tips,
            'crop': canonical_crop,
            'location': {'lat': lat, 'lon': lon}
        }

    def _get_simple_forecast_summary(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get simplified forecast summary (faster)."""
        try:
            simple = self.rainfall_service.get_simple_forecast(lat, lon)
            return {
                'next_7_days': {
                    'total_rainfall_mm': simple['total_rainfall_mm'],
                    'avg_temp_c': simple['avg_temp_c'],
                    'precipitation_probability': simple['avg_precipitation_probability']
                },
                'model': 'Open-Meteo 7-day Forecast API'
            }
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return {
                'next_7_days': {
                    'total_rainfall_mm': 35.0,
                    'avg_temp_c': 24.0,
                    'precipitation_probability': 50.0
                },
                'model': 'Default (API unavailable)'
            }

    def _get_default_soil_data(self) -> Dict[str, Any]:
        """Get default soil data when actual data unavailable."""
        return {
            'location': {'lat': None, 'lon': None},
            'pH': 6.5,
            'texture': 'loam',
            'organic_carbon_pct': 2.0,
            'sand_pct': 40.0,
            'bulk_density': 1.4,
            'cec': 15.0,
            'nutrients': {
                'nitrogen_pct': 0.15,
                'phosphorus_ppm': 20.0,
                'potassium_ppm': 150.0,
            },
            'data_quality': {
                'confidence': 'low',
                'note': 'Default values - actual soil test recommended'
            }
        }

    def _build_soil_response(
        self,
        summary: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        summary_safe = summary or {}
        nutrients = summary_safe.get('nutrients', {}) or {}

        recommended_metrics = {
            'pH': summary_safe.get('pH') or summary_safe.get('ph'),
            'texture': summary_safe.get('texture'),
            'organic_carbon_pct': summary_safe.get('organic_carbon_pct'),
            'sand_pct': summary_safe.get('sand_pct'),
            'bulk_density': summary_safe.get('bulk_density'),
            'cec': summary_safe.get('cec'),
        }

        macronutrients = {
            'nitrogen_pct': nutrients.get('nitrogen_pct'),
            'phosphorus_ppm': nutrients.get('phosphorus_ppm'),
            'potassium_ppm': nutrients.get('potassium_ppm'),
        }

        response: Dict[str, Any] = {
            'summary': recommended_metrics,
            'macronutrients': macronutrients,
            'source': summary_safe.get('source'),
            'data_quality': summary_safe.get('data_quality'),
        }

        if profile:
            response['profiles'] = {
                'observed': profile.get('observed'),
                'model_estimate': profile.get('model_estimate'),
                'blended': profile.get('blended'),
                'crop_alignment': profile.get('crop_alignment'),
            }

        return response

    def _generate_tips(
        self,
        forecast: Dict[str, Any],
        soil_data: Dict[str, Any],
        crop: str
    ) -> List[str]:
        """
        Generate actionable farming tips based on forecast and soil data.

        Args:
            forecast: Rainfall forecast data
            soil_data: Soil characteristics data
            crop: Crop type

        Returns:
            List of actionable tip strings (max 5)
        """
        tips = []
        crop = normalize_crop(crop)

        # Extract forecast data
        if 'next_7_days' in forecast:
            rainfall_7d = forecast['next_7_days'].get('total_rainfall_mm', 35)
            if 'avg_temp_c' in forecast['next_7_days']:
                avg_temp = forecast['next_7_days']['avg_temp_c']
            else:
                avg_temp = 24
        else:
            rainfall_7d = 35
            avg_temp = 24

        # Extract soil data
        ph = soil_data.get('pH', 6.5)
        texture = soil_data.get('texture', 'loam')
        organic_carbon = soil_data.get('organic_carbon_pct', 2.0)
        nutrients = soil_data.get('nutrients', {})
        nitrogen = nutrients.get('nitrogen_pct', 0.15)
        phosphorus = nutrients.get('phosphorus_ppm', 20)

        # Tip 1: Rainfall-based irrigation advice
        tips.append(self._get_rainfall_tip(rainfall_7d, crop))

        # Tip 2: Soil pH management
        tips.append(self._get_ph_tip(ph, crop))

        # Tip 3: Nutrient management
        tips.append(self._get_nutrient_tip(nitrogen, phosphorus, crop))

        # Tip 4: Temperature-based advice
        tips.append(self._get_temperature_tip(avg_temp, crop, rainfall_7d))

        # Tip 5: Crop-specific best practice
        tips.append(self._get_crop_specific_tip(crop, texture, organic_carbon))

        return tips

    def _get_rainfall_tip(self, rainfall_mm: float, crop: str) -> str:
        """Generate rainfall-based tip."""
        if rainfall_mm < 15:
            return f"Very low rainfall expected ({rainfall_mm}mm). Arrange irrigation system immediately. {crop.capitalize()} needs consistent moisture - consider drip irrigation or mulching heavily."
        elif rainfall_mm < 30:
            return f"Low rainfall expected ({rainfall_mm}mm). Plan for supplemental irrigation. Check soil moisture daily and water when top 5cm is dry."
        elif rainfall_mm < 60:
            return f"Moderate rainfall expected ({rainfall_mm}mm). Good conditions for {crop} growth. Monitor soil moisture and irrigate only if needed."
        elif rainfall_mm < 100:
            return f"Good rainfall expected ({rainfall_mm}mm). Excellent for {crop} growth. Ensure proper drainage to prevent waterlogging."
        else:
            return f"Heavy rainfall expected ({rainfall_mm}mm). High waterlogging risk. Check drainage systems, consider raised beds, and monitor for fungal diseases."

    def _get_ph_tip(self, ph: float, crop: str) -> str:
        """Generate pH management tip."""
        crop_ph_optimal = {
            'maize': (5.8, 7.0),
            'beans': (6.0, 7.5),
            'tomato': (6.0, 6.8),
            'potato': (5.2, 6.5),
            'rice': (5.5, 6.5),
            'wheat': (6.0, 7.5),
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

        optimal = crop_ph_optimal.get(crop, (6.0, 7.0))

        if ph < optimal[0] - 0.5:
            lime_rate = int((optimal[0] - ph) * 2000)  # Rough calculation
            return f"Soil very acidic (pH {ph}). Apply agricultural lime at {lime_rate}-{lime_rate+1000} kg/ha to improve {crop} yields by 20-30%."
        elif ph < optimal[0]:
            return f"Soil slightly acidic (pH {ph}). Apply 1-2 tons/ha of lime before planting {crop} for optimal nutrient availability."
        elif ph > optimal[1] + 0.5:
            return f"Soil alkaline (pH {ph}). Add sulfur (200-300 kg/ha) or incorporate organic matter to lower pH for {crop}."
        elif ph > optimal[1]:
            return f"Soil slightly alkaline (pH {ph}). Add compost or well-rotted manure to gradually lower pH for {crop}."
        else:
            return f"Soil pH ({ph}) is optimal for {crop}. Maintain by adding organic matter and avoiding excessive lime application."

    def _get_nutrient_tip(self, nitrogen_pct: float, phosphorus_ppm: float, crop: str) -> str:
        """Generate nutrient management tip."""
        crop_n_needs = {
            'maize': 120,
            'tomato': 150,
            'potato': 100,
            'wheat': 80,
            'rice': 100,
            'beans': 40,  # Legume - fixes nitrogen
            'sorghum': 80,
            'cassava': 60,
            'sweet potato': 60,
            'banana': 200,
            'groundnut': 30,
            'soybean': 25,
            'cowpea': 25,
            'pigeon pea': 30,
            'millet': 60,
            'sunflower': 90,
            'onion': 90,
            'cabbage': 140,
            'carrot': 100,
            'chili': 120,
        }

        n_requirement = crop_n_needs.get(crop, 100)

        legumes = {
            'beans', 'peas', 'soybean', 'groundnut', 'cowpea', 'pigeon pea', 'pigeonpea'
        }

        if crop in legumes:
            return f"For {crop} (legume), apply DAP at planting (20-30 kg/ha) for phosphorus. Minimal nitrogen needed as plants fix atmospheric nitrogen."
        elif nitrogen_pct < 0.1:
            return f"Very low soil nitrogen. Apply {n_requirement} kg/ha N for {crop}: 1/3 at planting (as DAP), 1/3 at 4 weeks, 1/3 at 8 weeks (as CAN or Urea)."
        elif nitrogen_pct < 0.15:
            n_reduced = int(n_requirement * 0.7)
            return f"Low nitrogen. Apply {n_reduced} kg/ha N for {crop} in split applications: at planting, 4 weeks, and flowering stage."
        elif phosphorus_ppm < 15:
            return f"Low phosphorus ({phosphorus_ppm} ppm). Apply 40-60 kg/ha P2O5 (DAP or TSP) at planting to boost {crop} root development and early growth."
        else:
            return f"Adequate nitrogen and phosphorus. Apply balanced NPK (e.g., 23:23:0 or 17:17:17) at 100-150 kg/ha at planting for {crop}."

    def _get_temperature_tip(self, temp_c: float, crop: str, rainfall_mm: float) -> str:
        """Generate temperature-based tip."""
        if temp_c > 32 and rainfall_mm < 30:
            return f"High temperature ({temp_c}°C) and low rainfall increase heat stress risk for {crop}. Irrigate in early morning or evening, and consider shade nets for seedlings."
        elif temp_c > 30:
            return f"Warm conditions ({temp_c}°C). Good for {crop} growth but ensure adequate soil moisture. Mulch to reduce soil temperature and conserve water."
        elif temp_c < 15:
            return f"Cool temperature ({temp_c}°C) may slow {crop} growth. Delay planting if possible, or use plastic mulch to warm soil and protect young plants."
        elif temp_c < 18:
            return f"Moderate temperature ({temp_c}°C). Good for {crop} establishment. Ensure seedlings are well-protected from cold nights with row covers if needed."
        else:
            return f"Optimal temperature ({temp_c}°C) for {crop} growth. Continue with normal planting and management practices."

    def _get_crop_specific_tip(self, crop: str, texture: str, organic_carbon_pct: float) -> str:
        """Generate crop-specific best practice tip."""
        crop_tips = {
            'maize': {
                'spacing': 'Plant maize at 75cm x 25cm spacing (1 seed per hole) for optimal yield. Thin to 1 plant per stand after germination.',
                'fertilizer': 'Side-dress with nitrogen fertilizer when maize reaches knee height (4-5 weeks) for strong stalk development.',
                'pest': 'Scout for fall armyworm from 2 weeks after germination. Apply Bt-based pesticides early morning or evening if found.',
            },
            'beans': {
                'spacing': 'Plant beans at 50cm x 10cm spacing. Ensure good soil contact but avoid planting too deep (2-3cm maximum).',
                'fertilizer': 'Inoculate bean seeds with rhizobium before planting for better nitrogen fixation and higher yields.',
                'pest': 'Monitor for aphids and bean fly. Spray neem-based pesticides if pest pressure exceeds 10% plant infestation.',
            },
            'tomato': {
                'spacing': 'Transplant tomato seedlings at 60cm x 45cm spacing. Stake or cage plants within 2 weeks for support.',
                'fertilizer': 'Apply foliar fertilizer (e.g., CAN solution 2%) every 2 weeks from flowering for better fruit set.',
                'pest': 'Prevent late blight: spray copper-based fungicide every 10-14 days during wet periods. Remove infected leaves immediately.',
            },
            'potato': {
                'spacing': 'Plant potato seed tubers at 75cm x 30cm spacing, 10cm deep. Use certified disease-free seeds.',
                'fertilizer': 'Earth up (hill) potato plants at 3-4 weeks to prevent tuber greening and improve yields by 20-30%.',
                'pest': 'Control potato blight: spray Mancozeb or copper fungicide every 7-10 days during rainy periods.',
            },
            'rice': {
                'spacing': 'Transplant rice seedlings at 20cm x 20cm spacing in puddled soil. Maintain 5-10cm water depth for first 2 months.',
                'fertilizer': 'Apply nitrogen in 3 splits: 50% at basal, 25% at tillering (21 days), 25% at panicle initiation (42 days).',
                'pest': 'Control rice blast disease: drain water for 3-4 days at tillering stage and apply Tricyclazole if symptoms appear.',
            },
            'wheat': {
                'spacing': 'Drill wheat seeds at 20cm row spacing, 5cm depth. Use seed rate of 100-125 kg/ha for optimal stand.',
                'fertilizer': 'Apply full phosphorus and potassium at sowing. Split nitrogen: 50% at sowing, 50% at crown root initiation (21 days).',
                'pest': 'Monitor for rust diseases. Apply Propiconazole fungicide at early detection to prevent yield losses up to 40%.',
            },
            'sorghum': {
                'spacing': 'Plant sorghum at 75cm x 15cm spacing. Use seed rate of 8-10 kg/ha for grain varieties.',
                'fertilizer': 'Apply DAP (50 kg/ha) at planting and top-dress with CAN (50 kg/ha) at 4-6 weeks after germination.',
                'pest': 'Control sorghum midge by planting early or using resistant varieties. Spray Cypermethrin if midge population is high during flowering.',
            },
            'cassava': {
                'spacing': 'Plant cassava cuttings at 1m x 1m spacing (10,000 plants/ha). Use disease-free stem cuttings of 20-25cm length.',
                'fertilizer': 'Apply manure or compost (5-10 tons/ha) at planting. Cassava responds well to potassium fertilizer (50-100 kg/ha K2O).',
                'pest': 'Monitor for cassava mosaic disease (CMD) and cassava brown streak disease (CBSD). Remove and destroy infected plants immediately.',
            },
            'sweet potato': {
                'spacing': 'Plant sweet potato vines at 1m x 30cm spacing on ridges. Use 3-node vine cuttings for best establishment.',
                'fertilizer': 'Apply 5-10 tons/ha of manure before planting. Sweet potato needs potassium (60-80 kg/ha K2O) for good tuber formation.',
                'pest': 'Control sweet potato weevil by using clean planting material and crop rotation. Harvest on time to reduce weevil damage.',
            },
            'banana': {
                'spacing': 'Plant banana suckers at 3m x 3m spacing (1,111 plants/ha). Use tissue culture or healthy sword suckers.',
                'fertilizer': 'Apply 20-30 kg manure per plant annually. Supplement with NPK fertilizer (200g N, 100g P2O5, 300g K2O per plant per year).',
                'pest': 'Control banana weevil and nematodes using clean planting material and crop rotation. Remove diseased plants to prevent Panama disease spread.',
            },
            'groundnut': {
                'spacing': 'Plant groundnut seeds at 45cm x 15cm spacing (30-40 plants/m²) for Spanish types; use 60cm rows for Virginia types.',
                'fertilizer': 'Treat seed with rhizobium inoculant and apply gypsum (250 kg/ha) at flowering for stronger pod fill.',
                'pest': 'Scout for early and late leaf spot. Spray Mancozeb or Chlorothalonil at first symptoms and remove volunteer plants.',
            },
            'soybean': {
                'spacing': 'Plant soybean at 45cm x 10cm spacing with 3-4 cm planting depth for optimal stand density.',
                'fertilizer': 'Apply inoculated seed plus 20-30 kg/ha phosphorus (TSP or DAP) at planting to boost nodulation and flowering.',
                'pest': 'Monitor for soybean rust and African bollworm. Apply systemic fungicide or Bt products promptly when lesions or caterpillars appear.',
            },
            'cowpea': {
                'spacing': 'Sow cowpea at 60cm x 20cm spacing for grain varieties; thin to one healthy plant per stand.',
                'fertilizer': 'Incorporate 5 tons/ha manure before planting and apply 20 kg/ha P2O5 to stimulate early root growth.',
                'pest': 'Use pheromone traps against pod borer and spray neem-based biopesticides when infestation exceeds 5%.',
            },
            'pigeon pea': {
                'spacing': 'Plant pigeon pea at 1.5m x 0.6m spacing; inter-crop with short-duration cereals during the first season.',
                'fertilizer': 'Apply farmyard manure (5 tons/ha) at planting and 20 kg/ha P2O5; crop fixes its own nitrogen.',
                'pest': 'Control pod borer with timely Bacillus thuringiensis sprays and harvest promptly to avoid storage beetles.',
            },
            'millet': {
                'spacing': 'Drill millet at 60cm x 10cm spacing after first effective rains; maintain plant population around 150,000/ha.',
                'fertilizer': 'Apply 40 kg/ha nitrogen and 20 kg/ha phosphorus in two splits (at planting and tillering).',
                'pest': 'Manage stem borer using push-pull or neem sprays; weed at 2 and 5 weeks to avoid competition.',
            },
            'sunflower': {
                'spacing': 'Sow sunflower at 75cm x 30cm spacing, thinning to one vigorous plant per hill after emergence.',
                'fertilizer': 'Side-dress with 40 kg/ha nitrogen at 4 weeks and ensure adequate boron by applying borax (8-10 kg/ha).',
                'pest': 'Scout for head borer and birds near maturity; bag heads or use safe repellents to protect seeds.',
            },
            'onion': {
                'spacing': 'Transplant onions at 30cm x 7-10cm spacing on raised beds with good drainage.',
                'fertilizer': 'Apply 60 kg/ha nitrogen split between 3 and 6 weeks and add potassium for bulb development.',
                'pest': 'Monitor for thrips; use reflective mulch and rotate approved insecticides to prevent resistance.',
            },
            'cabbage': {
                'spacing': 'Transplant cabbage seedlings at 60cm x 45cm spacing; firm soil around base to prevent lodging.',
                'fertilizer': 'Apply 120 kg/ha nitrogen in three splits (transplanting, 4 weeks, 8 weeks) plus 80 kg/ha potassium.',
                'pest': 'Scout twice weekly for diamondback moth; release parasitoids or apply Bt formulations early.',
            },
            'carrot': {
                'spacing': 'Direct seed carrots in rows 30cm apart, thinning to 5-8cm within the row to prevent forked roots.',
                'fertilizer': 'Apply 60 kg/ha nitrogen in two splits and maintain steady moisture to avoid cracking.',
                'pest': 'Use fine mesh netting against carrot fly and practice crop rotation to minimize nematodes.',
            },
            'chili': {
                'spacing': 'Transplant chili peppers at 60cm x 45cm spacing on raised beds for good drainage.',
                'fertilizer': 'Apply basal NPK 17:17:17 (200 kg/ha) and top-dress with calcium ammonium nitrate at flowering.',
                'pest': 'Monitor for thrips and fruit fly; remove infested fruits and use yellow sticky traps with biopesticides.',
            },
        }

        # Get crop-specific tips or default
        crop_info = crop_tips.get(crop, {
            'spacing': f'Follow recommended spacing for {crop} based on variety. Avoid overcrowding for better air circulation.',
            'fertilizer': f'Apply balanced fertilizer based on soil test results for {crop}.',
            'pest': f'Scout regularly for pests and diseases. Use integrated pest management (IPM) for {crop}.',
        })

        # Choose most relevant tip based on soil conditions
        if organic_carbon_pct < 1.5:
            return crop_info.get('fertilizer', '') + " Low organic matter: add 5-10 tons/ha compost to improve soil health."
        elif texture in ['sand', 'sandy loam']:
            return crop_info.get('spacing', '') + " Sandy soil: mulch heavily and irrigate frequently to retain moisture."
        else:
            # Return the most actionable tip (pest management often most urgent)
            return crop_info.get('pest', crop_info.get('spacing', ''))
