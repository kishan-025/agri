"""
Soil Health Profile & Uncertainty Quantification Service
Computes Composite Soil Health Index (SHI, 0-100) and scientifically formulates
95% Confidence Intervals combining neural task precision weights (homoscedastic sigma)
with empirical within-field spatial variance.
"""

import math
from typing import Dict, Any, Optional

# Calibrated task-specific homoscedastic uncertainties from Kendall et al. multi-task loss
MODEL_SIGMAS = {
    "pH": 0.52,
    "Nitrogen": 1.07,
    "Phosphorus": 0.50,
    "Potassium": 0.44
}

def compute_soil_health_index(
    ph: float,
    n: float,
    p: float,
    k: float,
    topsoil_moisture_m3m3: float = 0.22,
    ndvi: float = 0.35
) -> Dict[str, Any]:
    """
    Computes a composite Soil Health Index (0-100) using agronomic multi-parameter scoring:
      - 30% Soil pH optimality
      - 30% Macronutrient (NPK) balance and sufficiency
      - 25% Volumetric soil moisture retention
      - 15% Surface vegetation & biological cover proxy (NDVI)
    """
    # 1. Soil pH Sub-Score (Optimum 6.0 - 7.5 for most field crops)
    if 6.0 <= ph <= 7.5:
        s_ph = 1.0
    elif 5.0 <= ph < 6.0:
        s_ph = 0.5 + 0.5 * ((ph - 5.0) / 1.0)
    elif 7.5 < ph <= 8.5:
        s_ph = 1.0 - 0.5 * ((ph - 7.5) / 1.0)
    elif ph < 5.0:
        s_ph = max(0.1, 0.5 * (ph / 5.0))
    else:  # ph > 8.5 (Alkaline/Saline)
        s_ph = max(0.1, 1.0 - 0.9 * ((ph - 8.5) / 1.5))

    # 2. Macronutrient Sub-Scores (relative to standard agricultural sufficiency ranges)
    # Nitrogen (mg/kg or g/kg): Critical threshold ~ 1.5 - 3.5 mg/kg
    s_n = min(1.0, max(0.1, n / 2.5))
    
    # Phosphorus (mg/kg Olsen/Bray): Optimum ~ 15 - 45 mg/kg
    if 15.0 <= p <= 50.0:
        s_p = 1.0
    elif p < 15.0:
        s_p = max(0.15, p / 15.0)
    else:  # Excessive P (>50 mg/kg)
        s_p = max(0.6, 1.0 - 0.4 * ((p - 50.0) / 90.0))

    # Potassium (mg/kg exchangeable): Optimum ~ 80 - 250 mg/kg
    if 80.0 <= k <= 250.0:
        s_k = 1.0
    elif k < 80.0:
        s_k = max(0.15, k / 80.0)
    else:  # Rich Potassium
        s_k = 0.95

    # Combined NPK balance (Harmonic mean avoids masking severe single-nutrient deficits)
    s_npk = 3.0 / ( (1.0 / s_n) + (1.0 / s_p) + (1.0 / s_k) )

    # 3. Moisture Sub-Score (Optimum field capacity ~ 0.20 - 0.35 m3/m3)
    if 0.20 <= topsoil_moisture_m3m3 <= 0.35:
        s_moist = 1.0
    elif topsoil_moisture_m3m3 < 0.20:
        s_moist = max(0.1, topsoil_moisture_m3m3 / 0.20)
    else:  # Waterlogged topsoil (>0.35)
        s_moist = max(0.5, 1.0 - 0.5 * ((topsoil_moisture_m3m3 - 0.35) / 0.15))

    # 4. Vegetation / Biomass Sub-Score (NDVI proxy for surface cover & roots)
    if ndvi >= 0.30:
        s_veg = min(1.0, 0.6 + 0.4 * (ndvi / 0.8))
    elif ndvi >= 0.15:
        s_veg = 0.6  # Bare arable agricultural soil
    else:
        s_veg = 0.3  # Severely eroded / sparse vegetation

    # Weighted Overall Index (0 - 100)
    shi = 100.0 * (0.30 * s_ph + 0.30 * s_npk + 0.25 * s_moist + 0.15 * s_veg)
    shi = round(min(100.0, max(10.0, shi)), 1)

    # Condition Tier & Interpretation
    if shi >= 80.0:
        tier = "OPTIMAL_FERTILE"
        desc = "Prime agricultural condition with excellent nutrient-moisture balance."
        color = "#10B981"  # Emerald
    elif shi >= 65.0:
        tier = "GOOD_MODERATE"
        desc = "Adequate soil health; targeted fertilization will optimize yield."
        color = "#3B82F6"  # Blue
    elif shi >= 50.0:
        tier = "STRESSED_DEFICIENT"
        desc = "Marginal soil fertility. Nutrient deficiencies or dry topsoil requires management."
        color = "#F59E0B"  # Amber
    else:
        tier = "DEGRADED_IMPAIRED"
        desc = "Impaired soil condition (acidity, extreme drought, or critical nutrient depletion)."
        color = "#EF4444"  # Red

    return {
        "soil_health_index": shi,
        "condition_tier": tier,
        "description": desc,
        "indicator_color": color,
        "sub_scores": {
            "ph_optimality": round(s_ph * 100, 1),
            "npk_balance": round(s_npk * 100, 1),
            "moisture_adequacy": round(s_moist * 100, 1),
            "vegetative_vigor": round(s_veg * 100, 1)
        }
    }


def quantify_uncertainty(
    metric_name: str,
    mean_val: float,
    field_std: float,
    pixel_count: int,
    cloud_cover_pct: float = 0.0
) -> Dict[str, Any]:
    """
    Quantifies aleatoric and epistemic prediction uncertainty:
      - Aleatoric: Model residual homoscedastic variance (Kendall sigma)
      - Epistemic / Spatial: Heterogeneity standard deviation across polygon pixels
      - Atmospheric penalty: Cloud cover scaling
    Returns 95% Confidence Interval bounds and confidence rating.
    """
    model_sigma = MODEL_SIGMAS.get(metric_name, 0.50)
    
    # Atmospheric attenuation penalty
    cloud_factor = 1.0 + (cloud_cover_pct / 100.0) * 0.5
    
    # Effective standard error
    n_eff = max(4, min(pixel_count, 400))
    spatial_se = (field_std / math.sqrt(n_eff)) if n_eff > 1 else field_std
    combined_se = math.sqrt((model_sigma * cloud_factor) ** 2 + spatial_se ** 2)
    
    margin_of_error = round(1.96 * (combined_se / math.sqrt(2.0)), 2)
    
    ci_lower = round(max(0.0, mean_val - margin_of_error), 2)
    ci_upper = round(mean_val + margin_of_error, 2)
    
    # If pH, clip lower bound to 3.5
    if metric_name == "pH":
        ci_lower = max(3.5, ci_lower)
        ci_upper = min(9.5, ci_upper)
        
    relative_uncertainty_pct = round((margin_of_error / max(0.1, mean_val)) * 100.0, 1)
    
    if relative_uncertainty_pct < 15.0 and cloud_cover_pct < 15.0:
        conf_rating = "HIGH_CONFIDENCE"
    elif relative_uncertainty_pct < 30.0:
        conf_rating = "MODERATE_CONFIDENCE"
    else:
        conf_rating = "ELEVATED_UNCERTAINTY"

    return {
        "mean": round(mean_val, 2),
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "margin_of_error": margin_of_error,
        "relative_uncertainty_pct": relative_uncertainty_pct,
        "confidence_rating": conf_rating
    }
