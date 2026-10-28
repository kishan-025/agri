"""
Multi-Criteria Crop Ranking & Agronomic Suitability Engine
Applies Fuzzy Trapezoidal Membership Scoring across soil pH, NPK macronutrients,
volumetric topsoil moisture, temperature, and cumulative rainfall.
"""

from typing import List, Dict, Any, Optional
from services.crop_database import CROP_DATABASE

def _fuzzy_trapezoidal_score(val: float, min_val: float, opt_min: float, opt_max: float, max_val: float) -> float:
    """Computes a normalized [0.0, 1.0] continuous membership score."""
    if opt_min <= val <= opt_max:
        return 1.0
    elif min_val < val < opt_min:
        return max(0.1, (val - min_val) / (opt_min - min_val))
    elif opt_max < val < max_val:
        return max(0.1, 1.0 - (val - opt_max) / (max_val - opt_max))
    else:
        return 0.05  # Near lethal / severe stress limit


def rank_crops_for_region(
    ph: float,
    n: float,
    p: float,
    k: float,
    rainfall_seasonal_mm: float,
    mean_temp_celsius: float,
    topsoil_moisture_m3m3: float = 0.22,
    active_season: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Ranks crops from CROP_DATABASE based on multi-parameter agronomic compatibility.
    Returns sorted list of top_k recommendations with breakdown scores and limiting constraints.
    """
    ranked_results = []

    for crop in CROP_DATABASE:
        # 1. Soil Reaction (pH) Fit
        ph_range = crop["ph_range"]
        s_ph = _fuzzy_trapezoidal_score(
            ph, ph_range["min"], ph_range["opt_min"], ph_range["opt_max"], ph_range["max"]
        )

        # 2. Macronutrient Compatibility (N, P, K)
        n_range = crop["nitrogen_ppm"]
        s_n = _fuzzy_trapezoidal_score(
            n, n_range["min"], n_range["opt_min"], n_range["opt_max"], n_range["max"]
        )

        p_range = crop["phosphorus_ppm"]
        s_p = _fuzzy_trapezoidal_score(
            p, p_range["min"], p_range["opt_min"], p_range["opt_max"], p_range["max"]
        )

        k_range = crop["potassium_ppm"]
        s_k = _fuzzy_trapezoidal_score(
            k, k_range["min"], k_range["opt_min"], k_range["opt_max"], k_range["max"]
        )

        s_soil = 0.40 * s_ph + 0.20 * s_n + 0.20 * s_p + 0.20 * s_k

        # 3. Climate Envelope (Rainfall & Temperature)
        rain_range = crop["rainfall_seasonal_mm"]
        s_rain = _fuzzy_trapezoidal_score(
            rainfall_seasonal_mm, rain_range["min"], rain_range["opt_min"], rain_range["opt_max"], rain_range["max"]
        )

        temp_range = crop["temperature_celsius"]
        s_temp = _fuzzy_trapezoidal_score(
            mean_temp_celsius, temp_range["min"], temp_range["opt_min"], temp_range["opt_max"], temp_range["max"]
        )

        s_climate = 0.50 * s_rain + 0.50 * s_temp

        # 4. Volumetric Moisture Fit
        moist_range = crop["soil_moisture_m3m3"]
        s_moist = _fuzzy_trapezoidal_score(
            topsoil_moisture_m3m3, moist_range["min"], moist_range["opt_min"], moist_range["opt_max"], moist_range["max"]
        )

        # 5. Seasonal Alignment
        s_season = 1.0
        if active_season:
            matched_season = False
            for s in crop["suitable_seasons"]:
                if active_season.split()[0].lower() in s.lower():
                    matched_season = True
                    break
            s_season = 1.0 if matched_season else 0.55

        # Hard Agronomic Constraints Checks & Penalty
        constraints = []
        if ph < ph_range["min"]:
            constraints.append(f"Soil is too acidic (pH {ph:.2f}) for optimal root development; agricultural lime advised.")
        elif ph > ph_range["max"]:
            constraints.append(f"Soil is alkaline/saline (pH {ph:.2f}); gypsum or organic manure recommended.")

        if n < n_range["opt_min"]:
            constraints.append(f"Available Nitrogen ({n:.2f} mg/kg) is below optimum; split-dose urea application required.")
        elif n > n_range["opt_max"]:
            constraints.append(f"Available Nitrogen ({n:.2f} mg/kg) is high; minimize synthetic nitrogen to avoid lodging.")

        if p < p_range["opt_min"]:
            constraints.append(f"Extractable Phosphorus ({p:.2f} mg/kg) is low; basal DAP/SSP required.")
        elif p > 60.0:
            constraints.append(f"Phosphorus is elevated ({p:.2f} mg/kg); avoid unnecessary phosphatic application.")

        if k < k_range["opt_min"]:
            constraints.append(f"Exchangeable Potassium ({k:.2f} mg/kg) is below demand; apply MOP (Muriate of Potash).")

        if rainfall_seasonal_mm < rain_range["min"]:
            constraints.append(f"Seasonal rainfall ({rainfall_seasonal_mm:.1f} mm) is deficient; supplemental irrigation mandatory.")

        if topsoil_moisture_m3m3 < moist_range["min"]:
            constraints.append(f"Topsoil moisture ({topsoil_moisture_m3m3:.2f} m³/m³) is dry; pre-sowing irrigation necessary.")

        # Composite Weighted Match Percentage
        raw_match = (
            0.35 * s_soil +
            0.35 * s_climate +
            0.20 * s_moist +
            0.10 * s_season
        ) * 100.0

        match_pct = round(min(98.5, max(15.0, raw_match)), 1)

        ranked_results.append({
            "crop_id": crop["crop_id"],
            "crop_name": crop["crop_name"],
            "scientific_name": crop["scientific_name"],
            "category": crop["category"],
            "match_percentage": match_pct,
            "suitability_level": "HIGHLY_SUITABLE" if match_pct >= 80 else ("MODERATELY_SUITABLE" if match_pct >= 65 else "MARGINAL"),
            "water_requirement": crop["water_requirement"],
            "duration_days": crop["duration_days"],
            "recommended_npk_ratio": crop["recommended_npk_ratio_kg_acre"],
            "economic_importance": crop["economic_importance"],
            "sub_scores": {
                "soil_fit": round(s_soil * 100, 1),
                "climate_fit": round(s_climate * 100, 1),
                "moisture_fit": round(s_moist * 100, 1),
                "season_alignment": round(s_season * 100, 1)
            },
            "limiting_constraints": constraints if constraints else ["Optimal conditions met across major soil and climate indicators."]
        })

    # Sort descending by match percentage
    ranked_results.sort(key=lambda x: x["match_percentage"], reverse=True)

    # Assign rank indices 1 to top_k
    top_ranked = ranked_results[:top_k]
    for i, r in enumerate(top_ranked):
        r["rank"] = i + 1

    return top_ranked
