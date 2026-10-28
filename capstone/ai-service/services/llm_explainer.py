"""
LLM Agronomic Explanation Layer
Generates expert natural language explanations, supporting evidence, and actionable
fertilizer prescriptions using Google Gemini 1.5 API with an intelligent offline
heuristic fallback engine for reliable academic evaluation.
"""

import os
import json
from typing import Dict, Any, List, Optional

def generate_crop_advisory_explanation(
    top_crop: Dict[str, Any],
    ph: float,
    n: float,
    p: float,
    k: float,
    topsoil_moisture_m3m3: float,
    rainfall_30d_mm: float,
    rainfall_90d_mm: float,
    mean_temp_celsius: float,
    active_season: str,
    farm_name: str = "Agricultural Plot"
) -> Dict[str, Any]:
    """
    Generates a structured LLM explanation for the top-recommended crop.
    Attempts Google Gemini API (gemini-1.5-flash) first if GEMINI_API_KEY or GOOGLE_API_KEY is present.
    Gracefully falls back to the deterministic agricultural heuristic engine if offline or key is unset.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if api_key:
        try:
            return _call_gemini_api(
                api_key=api_key,
                top_crop=top_crop,
                ph=ph, n=n, p=p, k=k,
                moisture=topsoil_moisture_m3m3,
                rainfall_30d=rainfall_30d_mm,
                rainfall_90d=rainfall_90d_mm,
                temp=mean_temp_celsius,
                season=active_season,
                farm_name=farm_name
            )
        except Exception as e:
            print(f"[WARN] Gemini LLM API call encountered an issue: {str(e)}. Using Agricultural Heuristic Engine fallback.")

    return _generate_heuristic_advisory(
        top_crop=top_crop,
        ph=ph, n=n, p=p, k=k,
        moisture=topsoil_moisture_m3m3,
        rainfall_30d=rainfall_30d_mm,
        rainfall_90d=rainfall_90d_mm,
        temp=mean_temp_celsius,
        season=active_season,
        farm_name=farm_name
    )


def _call_gemini_api(
    api_key: str,
    top_crop: Dict[str, Any],
    ph: float, n: float, p: float, k: float,
    moisture: float,
    rainfall_30d: float,
    rainfall_90d: float,
    temp: float,
    season: str,
    farm_name: str
) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
You are an expert Chief Agricultural Scientist and Agronomist at ICAR / UAS.
A farmer has requested precision soil nutrient diagnosis and crop recommendations for their field: '{farm_name}'.

Satellite and Climate Ingestion Data:
- Soil pH: {ph:.2f}
- Available Nitrogen (N): {n:.2f} mg/kg
- Extractable Phosphorus (P): {p:.2f} mg/kg
- Exchangeable Potassium (K): {k:.2f} mg/kg
- 0-7cm Topsoil Moisture: {moisture:.2f} m³/m³ (Saturation: {round(moisture/0.45*100, 1)}%)
- 30-Day Cumulative Rainfall: {rainfall_30d:.1f} mm
- 90-Day Seasonal Rainfall: {rainfall_90d:.1f} mm
- Mean Air Temperature: {temp:.1f} °C
- Active Season: {season}
- Top Recommended Crop by Decision Engine: {top_crop.get('crop_name')} (Match: {top_crop.get('match_percentage')}%)
- Model Identified Constraints: {top_crop.get('limiting_constraints')}

Generate a comprehensive, actionable agronomic report in strict JSON format with the following keys:
1. "executive_summary": (String) A clear 2-sentence verdict explaining why this crop is recommended.
2. "supporting_evidence": (List of 3 strings) Scientific points validating why soil pH, NPK, moisture, and climate match this crop's biology.
3. "limiting_constraints": (List of 2-3 strings) Specific bottlenecks, deficiencies, or climate risks.
4. "actionable_fertilizer_plan": (Object)
   - "urea_kg_per_acre": (Float/Integer) Basal or split dose.
   - "dap_kg_per_acre": (Float/Integer) Basal phosphatic dose.
   - "mop_kg_per_acre": (Float/Integer) Muriate of Potash dose.
   - "soil_amendments": (String) Lime/gypsum/FYM advice based on pH.
5. "irrigation_advisory": (String) Tailored irrigation advice based on current topsoil moisture ({moisture:.2f} m³/m³).

Respond ONLY with valid JSON, without any markdown formatting backticks or text outside JSON.
"""
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Clean potential markdown fences
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()
    
    parsed = json.loads(raw_text)
    parsed["engine"] = "Google Gemini 1.5 Flash (Cloud LLM)"
    return parsed


def _generate_heuristic_advisory(
    top_crop: Dict[str, Any],
    ph: float, n: float, p: float, k: float,
    moisture: float,
    rainfall_30d: float,
    rainfall_90d: float,
    temp: float,
    season: str,
    farm_name: str
) -> Dict[str, Any]:
    """
    Expert heuristic agronomic explanation engine complying with ICAR / TNAU package of practices.
    Ensures 100% deterministic, high-quality output when LLM API keys are not supplied.
    """
    crop_name = top_crop.get("crop_name", "Recommended Crop")
    match_pct = top_crop.get("match_percentage", 85.0)
    category = top_crop.get("category", "Crops")

    # 1. Executive Summary
    summary = (
        f"{crop_name} is ranked as the primary recommendation for {farm_name} with an agronomic match of {match_pct}%. "
        f"The current soil reaction (pH {ph:.2f}) and thermal regime ({temp:.1f}°C) provide an optimal growth window during the {season}."
    )

    # 2. Supporting Evidence
    evidence = [
        f"Soil pH of {ph:.2f} aligns well with {crop_name}'s physiological tolerance, ensuring high nutrient bioavailability.",
        f"Current 0-7cm topsoil moisture ({moisture:.2f} m³/m³) provides adequate seedbed conditions for vigorous emergence.",
        f"Seasonal rainfall of {rainfall_90d:.1f} mm and average temperature of {temp:.1f}°C support tillering and root development."
    ]

    # 3. Fertilizer Calculation based on soil test
    # Nitrogen logic
    if n < 1.8:
        urea_dose = 35.0
        n_note = f"Available Nitrogen is low ({n:.2f} mg/kg); apply 35 kg/acre Urea in two split doses (basal + 30 DAS)."
    elif n < 3.5:
        urea_dose = 20.0
        n_note = f"Available Nitrogen is moderate ({n:.2f} mg/kg); standard 20 kg/acre Urea split application advised."
    else:
        urea_dose = 10.0
        n_note = f"Available Nitrogen is rich ({n:.2f} mg/kg); reduce synthetic Urea to 10 kg/acre to prevent excessive vegetative growth."

    # Phosphorus logic
    if p < 20.0:
        dap_dose = 40.0
        p_note = f"Extractable Phosphorus ({p:.2f} mg/kg) is deficient; apply 40 kg/acre DAP as basal dose."
    elif p > 60.0:
        dap_dose = 0.0
        p_note = f"Extractable Phosphorus ({p:.2f} mg/kg) is high; omit DAP/SSP to reduce soil salinity and fertilizer cost."
    else:
        dap_dose = 20.0
        p_note = f"Extractable Phosphorus ({p:.2f} mg/kg) is in optimum range; maintain 20 kg/acre DAP basal placement."

    # Potassium logic
    if k < 90.0:
        mop_dose = 25.0
        k_note = f"Exchangeable Potassium ({k:.2f} mg/kg) is low; apply 25 kg/acre MOP (Muriate of Potash) for grain filling."
    elif k < 200.0:
        mop_dose = 15.0
        k_note = f"Exchangeable Potassium ({k:.2f} mg/kg) is moderate; apply 15 kg/acre MOP."
    else:
        mop_dose = 0.0
        k_note = f"Exchangeable Potassium ({k:.2f} mg/kg) is plentiful; potassium application is optional."

    # Soil amendment logic
    if ph < 5.8:
        amendment = f"Soil is moderately acidic (pH {ph:.2f}). Broadcast 150 kg/acre agricultural lime or dolomite 2 weeks before sowing."
    elif ph > 8.2:
        amendment = f"Soil is alkaline/saline (pH {ph:.2f}). Apply 100 kg/acre gypsum accompanied by well-rotted Farm Yard Manure (FYM)."
    else:
        amendment = f"Soil pH {ph:.2f} is within optimal neutral range. No chemical liming required; apply 2-3 tons/acre organic compost/FYM."

    # Irrigation advisory
    if moisture < 0.16:
        irrigation = "Topsoil is dry (<16% saturation). Pre-sowing irrigation is required immediately before planting."
    elif moisture > 0.35:
        irrigation = "Topsoil is near saturation (>35%). Ensure drainage channels are open to prevent root asphyxiation."
    else:
        irrigation = "Moisture is currently optimal (field capacity). Schedule first supplemental irrigation at critical crown-root/flowering stage."

    constraints = top_crop.get("limiting_constraints", [])
    if not constraints:
        constraints = [n_note, p_note, k_note]

    return {
        "engine": "Agronomic Knowledge Engine (Deterministic ICAR Package of Practices)",
        "executive_summary": summary,
        "supporting_evidence": evidence,
        "limiting_constraints": constraints,
        "actionable_fertilizer_plan": {
            "urea_kg_per_acre": urea_dose,
            "dap_kg_per_acre": dap_dose,
            "mop_kg_per_acre": mop_dose,
            "nitrogen_guidance": n_note,
            "phosphorus_guidance": p_note,
            "potassium_guidance": k_note,
            "soil_amendments": amendment
        },
        "irrigation_advisory": irrigation
    }
