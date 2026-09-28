import os
import io
import json
import base64
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from shapely.geometry import Polygon, mapping
import rasterio
from rasterio.mask import mask
import rioxarray
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
# Load Pretrained Models & Feature Contract at Startup
# -------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

models: Dict[str, xgb.XGBRegressor] = {}
feature_names: List[str] = []
evaluation_metrics: Dict[str, Any] = {}

@app.on_event("startup")
def load_artifacts():
    global models, feature_names, evaluation_metrics
    targets = ["pH", "Nitrogen", "Phosphorus", "Potassium"]
    
    for t in targets:
        model_path = os.path.join(MODEL_DIR, f"xgboost_{t}.json")
        if os.path.exists(model_path):
            m = xgb.XGBRegressor()
            m.load_model(model_path)
            models[t] = m
            print(f"[OK] Loaded model: {t} from {model_path}")
        else:
            print(f"[WARN] Warning: Model not found at {model_path}")
            
    # Load feature names
    feat_path = os.path.join(MODEL_DIR, "feature_names.json")
    if os.path.exists(feat_path):
        with open(feat_path, "r", encoding="utf-8") as f:
            feature_names = json.load(f)
            print(f"[OK] Loaded feature blueprint: {len(feature_names)} features")
            
    # Load evaluation metrics
    metrics_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            evaluation_metrics = json.load(f)
            print("[OK] Loaded spatial CV evaluation metrics")

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
    cmap.set_bad(color='none')  # Outside polygon is transparent!
    
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
    # Ensure polygon is closed (5 points)
    poly_coords = coords + [coords[0]]
    farm_poly = Polygon(poly_coords)
    
    min_lon, min_lat, max_lon, max_lat = farm_poly.bounds
    farm_bbox = [min_lon, min_lat, max_lon, max_lat]
    
    # 2. Connect to Planetary Computer STAC
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace
    )
    
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=farm_bbox,
        query={"eo:cloud_cover": {"lt": 20}},
        sortby=[{"field": "properties.datetime", "direction": "desc"}],
        max_items=5
    )
    
    items = list(search.items())
    if not items:
        # Fallback to broader cloud threshold if area is cloudy
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=farm_bbox,
            sortby=[{"field": "properties.datetime", "direction": "desc"}],
            max_items=1
        )
        items = list(search.items())
        
    if not items:
        raise HTTPException(status_code=404, detail="No Sentinel-2 imagery found for this geographic region.")
    
    selected_scene = items[0]
    scene_date = selected_scene.datetime.strftime("%Y-%m-%d")
    cloud_cover = float(selected_scene.properties.get("eo:cloud_cover", 0.0))
    
    # 3. Stream and polygon-mask Sentinel-2 bands
    geo_json_geom = [mapping(farm_poly)]
    
    bands_10m = ["B02", "B03", "B04", "B08"]
    bands_20m = ["B05", "B06", "B07", "B8A", "B11", "B12"]
    
    band_arrays: Dict[str, np.ndarray] = {}
    
    try:
        # Extract 10m bands clipped to polygon
        reference_shape = None
        for b in bands_10m:
            url = selected_scene.assets[b].href
            da = rioxarray.open_rasterio(url).rio.clip(geo_json_geom, crs="EPSG:4326", drop=True)
            arr = da.values[0].astype(float) / 10000.0  # Convert DN to surface reflectance
            band_arrays[b] = arr
            if reference_shape is None:
                reference_shape = arr.shape
                
        # Extract 20m bands and resample to 10m grid
        for b in bands_20m:
            url = selected_scene.assets[b].href
            da = rioxarray.open_rasterio(url).rio.clip(geo_json_geom, crs="EPSG:4326", drop=True)
            arr_20m = da.values[0].astype(float) / 10000.0
            
            # Zoom/resample to match 10m grid shape
            zoom_factor = (reference_shape[0] / arr_20m.shape[0], reference_shape[1] / arr_20m.shape[1])
            arr_resampled = zoom(arr_20m, zoom_factor, order=1)
            # Ensure exact shape match
            band_arrays[b] = arr_resampled[:reference_shape[0], :reference_shape[1]]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Satellite streaming error: {str(e)}")

    # 4. Compute the 7 Diagnostic Spectral Indices
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
    bsi = ((b11 + b4) - (b8 + b2)) / ((b11 + b4) + (b8 + b2) + eps)
    clay_ratio = b11 / (b12 + eps)
    ferric_iron = b4 / (b2 + eps)
    carbonate_index = b12 / (b11 + eps)
    ndre = (b8 - b5) / (b8 + b5 + eps)
    soil_brightness = np.sqrt((b4**2 + b3**2 + b8**2) / 3.0)
    elev = np.zeros_like(b4)  # 0.0 elevation placeholder
    
    # 5. Mask Valid Pixels Inside the Quadrilateral
    # Pixels outside the polygon are NaN from rioxarray.clip
    valid_mask = ~np.isnan(b4)
    
    if np.sum(valid_mask) == 0:
        raise HTTPException(status_code=400, detail="The chosen quadrilateral is too small to contain a 10m satellite pixel.")
        
    # Build feature columns dictionary in exact trained order
    features_dict = {
        "B02": b2, "B03": b3, "B04": b4, "B05": b5, "B06": b6,
        "B07": b7, "B08": b8, "B8A": b8a, "B11": b11, "B12": b12,
        "NDVI": ndvi, "BSI": bsi, "Clay_Ratio": clay_ratio,
        "Ferric_Iron": ferric_iron, "Carbonate_Index": carbonate_index,
        "NDRE": ndre, "Soil_Brightness": soil_brightness, "Elev": elev
    }
    
    # Stack valid pixel features (N_valid, 18)
    feature_matrix = np.column_stack([features_dict[col][valid_mask] for col in feature_names])
    
    # 6. Run XGBoost Inference for all 4 Nutrients
    nutrients_2d: Dict[str, np.ndarray] = {}
    metrics_summary: Dict[str, Any] = {}
    
    for t, model in models.items():
        preds = model.predict(feature_matrix)
        
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
        
    # 7. Generate Base64 Transparent Heatmaps
    heatmaps_b64 = {
        "pH": render_heatmap_base64(
            nutrients_2d["pH"], "RdYlBu", vmin=5.0, vmax=8.5, 
            title=f"Soil pH (Avg: {metrics_summary['pH']['mean']})", unit="pH"
        ),
        "Nitrogen": render_heatmap_base64(
            nutrients_2d["Nitrogen"], "YlGn", vmin=0.0, vmax=max(50.0, metrics_summary['Nitrogen']['max']),
            title=f"Available Nitrogen (N) (Avg: {metrics_summary['Nitrogen']['mean']})", unit="mg/kg"
        ),
        "Phosphorus": render_heatmap_base64(
            nutrients_2d["Phosphorus"], "YlOrRd", vmin=0.0, vmax=max(30.0, metrics_summary['Phosphorus']['max']),
            title=f"Extractable Phosphorus (P) (Avg: {metrics_summary['Phosphorus']['mean']})", unit="mg/kg"
        ),
        "Potassium": render_heatmap_base64(
            nutrients_2d["Potassium"], "plasma", vmin=0.0, vmax=max(150.0, metrics_summary['Potassium']['max']),
            title=f"Exchangeable Potassium (K) (Avg: {metrics_summary['Potassium']['mean']})", unit="mg/kg"
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
        "metrics": metrics_summary,
        "heatmaps": heatmaps_b64
    }

if __name__ == "__main__":
    import uvicorn
    # Assigned Port 7000 as requested!
    uvicorn.run(app, host="0.0.0.0", port=7000)
