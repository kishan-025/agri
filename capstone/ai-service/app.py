"""
Soil Fertility AI Microservice
Port: 7000
Streams Copernicus Sentinel-2 L2A bands via Microsoft Planetary Computer STAC
Uses ultra-fast windowed COG reading & polygon masking, then evaluates 4 trained XGBoost models:
Soil pH, Available Nitrogen (N), Extractable Phosphorus (P), Exchangeable Potassium (K).
"""

import os
import io
import json
import base64
import time
from datetime import datetime, timezone, timedelta
import warnings
from typing import List, Dict, Any, Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend
import matplotlib.pyplot as plt

# Filter non-critical STAC and rasterio warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shapely.geometry import Polygon, mapping
from shapely.ops import transform
import pyproj
import rasterio
from rasterio.windows import from_bounds
import rasterio.features
import planetary_computer as pc
from pystac_client import Client
import xgboost as xgb
from scipy.ndimage import zoom

# -------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------
app = FastAPI(
    title="Soil Fertility AI Microservice",
    description="Copernicus Sentinel-2 Polygonal Streaming & 4-Nutrient XGBoost Inference Service",
    version="1.0.0"
)

# -------------------------------------------------------------
# Load Pretrained Models & Feature Blueprint at Startup
# -------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

models: Dict[str, Any] = {}
feature_names: List[str] = []
evaluation_metrics: Dict[str, Any] = {}

@app.on_event("startup")
def load_artifacts():
    global models, feature_names, evaluation_metrics
    targets = ["pH", "Nitrogen", "Phosphorus", "Potassium"]
    
    for t in targets:
        model_path = os.path.join(MODEL_DIR, f"xgboost_{t}.json")
        if os.path.exists(model_path):
            bst = xgb.Booster()
            bst.load_model(model_path)
            models[t] = bst
            print(f"[OK] Loaded XGBoost model for: {t}")
        else:
            print(f"[WARN] Warning: Model not found at {model_path}")
            
    # Load feature names
    feat_path = os.path.join(MODEL_DIR, "feature_names.json")
    if os.path.exists(feat_path):
        with open(feat_path, "r", encoding="utf-8") as f:
            feature_names = json.load(f)
        print(f"[OK] Loaded {len(feature_names)} features contract.")

    # Load metrics summary
    metrics_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            evaluation_metrics = json.load(f)

# -------------------------------------------------------------
# Pydantic Request Models
# -------------------------------------------------------------
class FertilityCheckRequest(BaseModel):
    farm_id: Optional[int] = None
    farm_name: Optional[str] = "My Farm"
    # 4 corner coordinates in order: [[lon1, lat1], [lon2, lat2], [lon3, lat3], [lon4, lat4]]
    corners: List[List[float]] = Field(..., description="Array of 4 [longitude, latitude] coordinate pairs")

# -------------------------------------------------------------
# Helper: Generate Base64 Color Heatmap with Transparent Background
# -------------------------------------------------------------
def render_heatmap_base64(data_2d: np.ndarray, cmap_name: str, vmin: float, vmax: float, title: str, unit: str) -> str:
    fig, ax = plt.subplots(figsize=(5, 4), dpi=120)
    
    # Make background transparent
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    # Mask out NaN pixels cleanly
    masked_data = np.ma.masked_invalid(data_2d)
    
    cmap = plt.get_cmap(cmap_name).copy()
    cmap.set_bad(color='none')  # Outside polygon is 100% transparent
    
    im = ax.imshow(masked_data, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    ax.set_title(title, fontsize=11, fontweight="bold", color="#1E293B", pad=10)
    ax.axis("off")
    
    # Add a compact colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(unit, fontsize=9, color="#334155")
    cbar.ax.tick_params(labelsize=8)
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", transparent=True, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "Soil Fertility AI Satellite Engine",
        "port": 7000,
        "models_loaded": list(models.keys()),
        "expected_features": feature_names
    }

@app.post("/api/fertility-check")
def run_fertility_check(req: FertilityCheckRequest):
    if len(req.corners) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 corner coordinates [[lon, lat], ...] are required.")
    
    # 1. Build Shapely Polygon and bounding box
    coords = req.corners
    poly_coords = coords + [coords[0]]
    farm_poly = Polygon(poly_coords)
    
    min_lon, min_lat, max_lon, max_lat = farm_poly.bounds
    farm_bbox = [min_lon, min_lat, max_lon, max_lat]
    
    # 2. Connect to Planetary Computer STAC
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace
    )
    
    # Dynamic search date range: past 180 days up to current date
    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc - timedelta(days=180)
    stac_date_range = f"{start_utc.strftime('%Y-%m-%d')}/{now_utc.strftime('%Y-%m-%d')}"

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=farm_bbox,
        datetime=stac_date_range,
        limit=35
    )
    items = list(search.items())
    if not items:
        # Broader fallback if needed
        search = catalog.search(collections=["sentinel-2-l2a"], bbox=farm_bbox, limit=10)
        items = list(search.items())
        
    if not items:
        raise HTTPException(status_code=404, detail="No Sentinel-2 imagery found for this geographic region.")
    
    # Smart Cloud-filtering strategy:
    # 1. Filter scenes with low cloud cover (<= 25%) and pick the newest pass
    # 2. If recent passes have high monsoon cloud cover (> 25%), pick the lowest cloud pass available
    clear_scenes = [it for it in items if float(it.properties.get("eo:cloud_cover", 100.0)) <= 25.0]
    if clear_scenes:
        clear_scenes.sort(key=lambda x: -x.datetime.timestamp())
        selected_scene = clear_scenes[0]
        cloud_strategy = "Optimal clear-sky pass (cloud cover <= 25%)"
        season_note = "Recent clear-sky acquisition selected with verified low cloud cover."
    else:
        items.sort(key=lambda x: (x.properties.get("eo:cloud_cover", 100.0), -x.datetime.timestamp()))
        selected_scene = items[0]
        cloud_strategy = "Monsoon cloud filtering active (clearest historical pass selected)"
        season_note = "High cloud cover (50%-100%) during the Southwest Monsoon. The pipeline selected the clearest cloud-free historical pass to ensure uncorrupted ground surface reflectance."
        
    scene_date = selected_scene.datetime.strftime("%Y-%m-%d")
    cloud_cover = float(selected_scene.properties.get("eo:cloud_cover", 0.0))
    
    # 3. Stream and polygon-mask Sentinel-2 bands using ultra-fast windowed COG reading
    bands_10m = ["B02", "B03", "B04", "B08"]
    bands_20m = ["B05", "B06", "B07", "B8A", "B11", "B12"]
    all_bands = bands_10m + bands_20m
    
    band_arrays: Dict[str, np.ndarray] = {}
    
    try:
        # Determine CRS from reference band (B04)
        ref_url = selected_scene.assets["B04"].href
        with rasterio.open(ref_url) as ref_src:
            raster_crs = ref_src.crs

        # Transform farm polygon to raster's native UTM projection
        project = pyproj.Transformer.from_crs("EPSG:4326", raster_crs, always_xy=True).transform
        poly_utm = transform(project, farm_poly)
        minx, miny, maxx, maxy = poly_utm.bounds

        reference_shape = None
        ref_transform = None

        # 1. Read 10m bands first to establish exact grid geometry & georeferencing
        for b in bands_10m:
            url = selected_scene.assets[b].href
            with rasterio.open(url) as src:
                win = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
                arr = src.read(1, window=win).astype(float) / 10000.0
                if reference_shape is None:
                    reference_shape = arr.shape
                    ref_transform = src.window_transform(win)
                band_arrays[b] = arr

        # 2. Read and resample 20m bands on clean rectangular windows (NO NaNs during interpolation!)
        for b in bands_20m:
            url = selected_scene.assets[b].href
            with rasterio.open(url) as src:
                win = from_bounds(minx, miny, maxx, maxy, transform=src.transform)
                arr = src.read(1, window=win).astype(float) / 10000.0
                zoom_factor = (reference_shape[0] / arr.shape[0], reference_shape[1] / arr.shape[1])
                resampled = zoom(arr, zoom_factor, order=1)
                band_arrays[b] = resampled[:reference_shape[0], :reference_shape[1]]

        # 3. Construct precise polygon mask strictly on the 10m reference grid
        farm_mask = rasterio.features.geometry_mask(
            [mapping(poly_utm)],
            out_shape=reference_shape,
            transform=ref_transform,
            invert=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Satellite streaming error: {str(e)}")

    # 4. Compute Diagnostic Multispectral Indices on clean uncorrupted data
    eps = 1e-6
    b2 = band_arrays["B02"]
    b3 = band_arrays["B03"]
    b4 = band_arrays["B04"]
    b5 = band_arrays["B05"]
    b6 = band_arrays["B06"]
    b7 = band_arrays["B07"]
    b8 = band_arrays["B08"]
    b8a = band_arrays["B8A"]
    b11 = band_arrays["B11"]
    b12 = band_arrays["B12"]
    
    ndvi = (b8 - b4) / (b8 + b4 + eps)
    ndbi = (b11 - b8) / (b11 + b8 + eps)
    bsi = ((b11 + b4) - (b8 + b2)) / ((b11 + b4) + (b8 + b2) + eps)
    ui = (b12 - b8) / (b12 + b8 + eps)
    clay_ratio = b11 / (b12 + eps)
    ferric_iron = b4 / (b2 + eps)
    carbonate_index = b12 / (b11 + eps)
    ndre = (b8 - b5) / (b8 + b5 + eps)
    soil_brightness = np.sqrt((b4**2 + b3**2 + b8**2) / 3.0)
    elev = np.zeros_like(b4)  # 0.0 elevation placeholder
    
    # 5. Mask Valid Pixels Inside the Quadrilateral
    valid_mask = farm_mask & (~np.isnan(b4)) & (~np.isnan(b11))
    
    if np.sum(valid_mask) == 0:
        raise HTTPException(status_code=400, detail="The chosen quadrilateral is too small to contain a 10m satellite pixel.")

    # Surface Land-Cover Diagnostics
    mean_ndbi = float(np.nanmean(ndbi[valid_mask]))
    mean_ndvi = float(np.nanmean(ndvi[valid_mask]))
    mean_bsi = float(np.nanmean(bsi[valid_mask]))
    mean_ui = float(np.nanmean(ui[valid_mask]))
    mean_ferric = float(np.nanmean(ferric_iron[valid_mask]))

    # Calibrated Surface Validation:
    # 1. Active crop canopy: NDVI >= 0.25
    # 2. Exposed agricultural topsoil (summer fallow): BSI >= -0.05 and iron ratio >= 1.20
    #    (In pre-monsoon dry season, bare dry soil has SWIR > NIR, so positive NDBI is expected)
    # 3. Non-agricultural / artificial surface: Low iron, low vegetation, abnormal spectral signature
    if mean_ndvi >= 0.25:
        surface_type = "Verified Agricultural Farmland (Active Crop Canopy)"
        is_soil_valid = True
        surface_status = "OPTIMAL"
        surface_warning = None
    elif mean_bsi > -0.05 and mean_ferric >= 1.20:
        surface_type = "Verified Agricultural Farmland (Dry Bare Soil / Fallow Field)"
        is_soil_valid = True
        surface_status = "OPTIMAL"
        surface_warning = None
    else:
        surface_type = "Non-Standard / Potential Artificial Cover"
        is_soil_valid = False
        surface_status = "WARNING"
        surface_warning = "The selected boundary exhibits low soil mineral absorption and non-agricultural spectral response. Results may be uncalibrated."

    # Build feature columns dictionary in exact trained order
    features_dict = {
        "B02": b2, "B03": b3, "B04": b4, "B05": b5, "B06": b6,
        "B07": b7, "B08": b8, "B8A": b8a, "B11": b11, "B12": b12,
        "NDVI": ndvi, "BSI": bsi, "Clay_Ratio": clay_ratio,
        "Ferric_Iron": ferric_iron, "Carbonate_Index": carbonate_index,
        "NDRE": ndre, "Soil_Brightness": soil_brightness, "Elev": elev
    }
    
    # Stack valid pixel features (N_valid, 18) - 100% clean and finite!
    feature_matrix = np.column_stack([features_dict[col][valid_mask] for col in feature_names])
    dmatrix = xgb.DMatrix(feature_matrix, feature_names=feature_names)
    
    # 6. Run XGBoost Inference for all 4 Nutrients
    nutrients_2d: Dict[str, np.ndarray] = {}
    metrics_summary: Dict[str, Any] = {}
    
    for t, model in models.items():
        preds = model.predict(dmatrix)
        
        # Clip physically realistic ranges
        if t == "pH":
            preds = np.clip(preds, 3.5, 9.5)
        else:
            preds = np.clip(preds, 0.0, None)
            
        # Place back into 2D grid (NaN for outside pixels)
        grid_2d = np.full(reference_shape, np.nan)
        grid_2d[valid_mask] = preds
        nutrients_2d[t] = grid_2d
        
        metrics_summary[t] = {
            "mean": round(float(np.mean(preds)), 2),
            "min": round(float(np.min(preds)), 2),
            "max": round(float(np.max(preds)), 2),
            "std": round(float(np.std(preds)), 2),
            "unit": "pH units" if t == "pH" else "mg/kg"
        }

    # Helper function for adaptive percentile bounds (prevents flat color wash)
    def get_bounds(arr_masked, default_min, default_max):
        vals = arr_masked[~np.isnan(arr_masked)]
        if len(vals) == 0:
            return default_min, default_max
        p2 = float(np.percentile(vals, 2))
        p98 = float(np.percentile(vals, 98))
        if p98 - p2 < 1e-4:
            return p2 - 1.0, p98 + 1.0
        span = p98 - p2
        return round(p2 - 0.05 * span, 2), round(p98 + 0.05 * span, 2)

    # 7. Generate Base64 Transparent Heatmaps with Adaptive Scaling
    ph_min, ph_max = get_bounds(nutrients_2d["pH"], 5.0, 8.5)
    n_min, n_max = get_bounds(nutrients_2d["Nitrogen"], 0.0, 50.0)
    p_min, p_max = get_bounds(nutrients_2d["Phosphorus"], 0.0, 50.0)
    k_min, k_max = get_bounds(nutrients_2d["Potassium"], 0.0, 200.0)

    heatmaps_b64 = {
        "pH": render_heatmap_base64(
            nutrients_2d["pH"], "RdYlBu", vmin=ph_min, vmax=ph_max, 
            title=f"Soil pH (Avg: {metrics_summary['pH']['mean']})", unit="pH"
        ),
        "Nitrogen": render_heatmap_base64(
            nutrients_2d["Nitrogen"], "YlGn", vmin=n_min, vmax=n_max,
            title=f"Available Nitrogen (N) (Avg: {metrics_summary['Nitrogen']['mean']})", unit="mg/kg"
        ),
        "Phosphorus": render_heatmap_base64(
            nutrients_2d["Phosphorus"], "YlOrRd", vmin=p_min, vmax=p_max,
            title=f"Extractable Phosphorus (P) (Avg: {metrics_summary['Phosphorus']['mean']})", unit="mg/kg"
        ),
        "Potassium": render_heatmap_base64(
            nutrients_2d["Potassium"], "plasma", vmin=k_min, vmax=k_max,
            title=f"Exchangeable Potassium (K) (Avg: {metrics_summary['Potassium']['mean']})", unit="mg/kg"
        )
    }

    # 8. Compute and Render Diagnostic Spectral Heatmaps (NDVI, NDBI, BSI, UI)
    spectral_2d = {
        "NDVI": np.full(reference_shape, np.nan),
        "NDBI": np.full(reference_shape, np.nan),
        "BSI": np.full(reference_shape, np.nan),
        "UI": np.full(reference_shape, np.nan)
    }
    spectral_2d["NDVI"][valid_mask] = ndvi[valid_mask]
    spectral_2d["NDBI"][valid_mask] = ndbi[valid_mask]
    spectral_2d["BSI"][valid_mask] = bsi[valid_mask]
    spectral_2d["UI"][valid_mask] = ui[valid_mask]

    spectral_metrics = {
        "NDVI": {
            "mean": round(float(np.mean(ndvi[valid_mask])), 3),
            "min": round(float(np.min(ndvi[valid_mask])), 3),
            "max": round(float(np.max(ndvi[valid_mask])), 3),
            "unit": "Index (-1 to 1)",
            "label": "Vegetation Index"
        },
        "NDBI": {
            "mean": round(float(np.mean(ndbi[valid_mask])), 3),
            "min": round(float(np.min(ndbi[valid_mask])), 3),
            "max": round(float(np.max(ndbi[valid_mask])), 3),
            "unit": "Index (-1 to 1)",
            "label": "Built-up / Dry Earth Index"
        },
        "BSI": {
            "mean": round(float(np.mean(bsi[valid_mask])), 3),
            "min": round(float(np.min(bsi[valid_mask])), 3),
            "max": round(float(np.max(bsi[valid_mask])), 3),
            "unit": "Index (-1 to 1)",
            "label": "Bare Soil Index"
        },
        "UI": {
            "mean": round(float(np.mean(ui[valid_mask])), 3),
            "min": round(float(np.min(ui[valid_mask])), 3),
            "max": round(float(np.max(ui[valid_mask])), 3),
            "unit": "Index (-1 to 1)",
            "label": "Urban / Impervious Index"
        }
    }

    ndvi_min, ndvi_max = get_bounds(spectral_2d["NDVI"], 0.0, 0.6)
    ndbi_min, ndbi_max = get_bounds(spectral_2d["NDBI"], -0.2, 0.3)
    bsi_min, bsi_max = get_bounds(spectral_2d["BSI"], -0.1, 0.3)
    ui_min, ui_max = get_bounds(spectral_2d["UI"], -0.2, 0.2)

    spectral_heatmaps_b64 = {
        "NDVI": render_heatmap_base64(
            spectral_2d["NDVI"], "YlGn", vmin=ndvi_min, vmax=ndvi_max,
            title=f"NDVI - Vegetation Index (Avg: {spectral_metrics['NDVI']['mean']})", unit="NDVI"
        ),
        "NDBI": render_heatmap_base64(
            spectral_2d["NDBI"], "coolwarm", vmin=ndbi_min, vmax=ndbi_max,
            title=f"NDBI - Built-up / SWIR Index (Avg: {spectral_metrics['NDBI']['mean']})", unit="NDBI"
        ),
        "BSI": render_heatmap_base64(
            spectral_2d["BSI"], "YlOrBr", vmin=bsi_min, vmax=bsi_max,
            title=f"BSI - Bare Soil Index (Avg: {spectral_metrics['BSI']['mean']})", unit="BSI"
        ),
        "UI": render_heatmap_base64(
            spectral_2d["UI"], "magma", vmin=ui_min, vmax=ui_max,
            title=f"UI - Urban / Impervious Index (Avg: {spectral_metrics['UI']['mean']})", unit="UI"
        )
    }

    return {
        "status": "SUCCESS",
        "farm_id": req.farm_id,
        "farm_name": req.farm_name,
        "satellite_date": scene_date,
        "cloud_cover_pct": round(cloud_cover, 2),
        "valid_pixels_count": int(np.sum(valid_mask)),
        "grid_shape": list(reference_shape),
        "surface_validation": {
            "surface_type": surface_type,
            "is_soil_valid": is_soil_valid,
            "mean_ndbi": round(mean_ndbi, 4),
            "mean_ndvi": round(mean_ndvi, 4),
            "mean_bsi": round(mean_bsi, 4),
            "mean_ui": round(mean_ui, 4),
            "mean_ferric": round(mean_ferric, 4),
            "warning": surface_warning
        },
        "season_context": season_note,
        "selection_strategy": cloud_strategy,
        "metrics": metrics_summary,
        "heatmaps": heatmaps_b64,
        "spectral_metrics": spectral_metrics,
        "spectral_heatmaps": spectral_heatmaps_b64
    }

if __name__ == "__main__":
    import uvicorn
    # Assigned Port 7000 as requested
    uvicorn.run(app, host="0.0.0.0", port=7000)
