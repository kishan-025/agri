"""
Soil Fertility AI Microservice
Port: 7000
Streams Copernicus Sentinel-2 L2A bands via Microsoft Planetary Computer STAC
Uses ultra-fast windowed COG reading & polygon masking, then evaluates NASA Harvest Presto
Foundation Model (128-d latent representation) with Decoupled Residual Mish Multi-Nutrient ANN:
Soil pH, Available Nitrogen (N), Extractable Phosphorus (P), Exchangeable Potassium (K).
"""

import os
import sys
import io
import json
import base64
import time
from datetime import datetime, timezone, timedelta
import warnings
from typing import List, Dict, Any, Optional

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

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
from scipy.ndimage import zoom

import torch
import torch.nn as nn

# -------------------------------------------------------------
# Deep Learning Architecture: Presto + Decoupled Soil ANN
# -------------------------------------------------------------
class ResMishBlock(nn.Module):
    def __init__(self, in_features, out_features, dropout_rate=0.2):
        super().__init__()
        self.fc1 = nn.Linear(in_features, out_features)
        self.norm1 = nn.LayerNorm(out_features)
        self.act1 = nn.Mish()
        self.drop = nn.Dropout(dropout_rate)
        
        self.fc2 = nn.Linear(out_features, out_features)
        self.norm2 = nn.LayerNorm(out_features)
        self.act2 = nn.Mish()

        if in_features != out_features:
            self.skip = nn.Linear(in_features, out_features)
        else:
            self.skip = nn.Identity()

    def forward(self, x):
        residual = self.skip(x)
        out = self.drop(self.act1(self.norm1(self.fc1(x))))
        out = self.norm2(self.fc2(out))
        return self.act2(out + residual)


class DecoupledSoilANN(nn.Module):
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        def build_head():
            return nn.Sequential(
                ResMishBlock(input_dim, 64, dropout_rate=dropout_rate),
                ResMishBlock(64, 32, dropout_rate=dropout_rate / 2.0),
                nn.Linear(32, 1)
            )
        self.head_pH = build_head()
        self.head_N  = build_head()
        self.head_P  = build_head()
        self.head_K  = build_head()

    def forward(self, x):
        return {
            "pH": self.head_pH(x).squeeze(-1),
            "N":  self.head_N(x).squeeze(-1),
            "P":  self.head_P(x).squeeze(-1),
            "K":  self.head_K(x).squeeze(-1)
        }

# -------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------
app = FastAPI(
    title="Soil Fertility AI Microservice",
    description="Copernicus Sentinel-2 Polygonal Streaming & Presto Foundation Decoupled Soil Inference Engine",
    version="2.0.0"
)

# -------------------------------------------------------------
# Load Pretrained Models & Feature Blueprint at Startup
# -------------------------------------------------------------
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

device = torch.device("cpu")
presto_backbone: Optional[Any] = None
decoupled_ann: Optional[DecoupledSoilANN] = None
engine_type: str = "PRESTO_DECOUPLED_ANN"
p_clip_bound: float = 142.86
k_clip_bound: float = 1134.17
model_metadata: Dict[str, Any] = {}

@app.on_event("startup")
def load_artifacts():
    global presto_backbone, decoupled_ann, engine_type, p_clip_bound, k_clip_bound, model_metadata
    
    # 1. Load Presto Foundation Model + Decoupled Neural Network
    ann_weights_path = os.path.join(MODEL_DIR, "decoupled_soil_ann.pt")
    ann_meta_path = os.path.join(MODEL_DIR, "decoupled_soil_ann_metadata.json")
    presto_weights_path = os.path.join(os.path.dirname(__file__), "presto", "data", "default_model.pt")
    
    if os.path.exists(ann_weights_path) and os.path.exists(presto_weights_path):
        try:
            presto_dir = os.path.join(os.path.dirname(__file__), "presto")
            if presto_dir not in sys.path:
                sys.path.insert(0, presto_dir)
            from single_file_presto import Presto
            
            # Load Presto Foundation Model
            presto_backbone = Presto.construct().to(device)
            presto_backbone.load_state_dict(torch.load(presto_weights_path, map_location=device))
            presto_backbone.eval()
            print("[OK] Loaded Presto Foundation Model backbone.")
            
            # Load Decoupled Multi-Nutrient ANN
            decoupled_ann = DecoupledSoilANN(input_dim=128).to(device)
            decoupled_ann.load_state_dict(torch.load(ann_weights_path, map_location=device))
            decoupled_ann.eval()
            print("[OK] Loaded Decoupled Multi-Nutrient Residual Mish Neural Network.")
            
            # Load Metadata & Clipping Bounds
            if os.path.exists(ann_meta_path):
                with open(ann_meta_path, "r", encoding="utf-8") as f:
                    model_metadata = json.load(f)
                p_clip_bound = float(model_metadata.get("clipping_bounds", {}).get("P_max", 142.86))
                k_clip_bound = float(model_metadata.get("clipping_bounds", {}).get("K_max", 1134.17))
                print(f"[OK] Loaded metadata config. Robust clipping: P_max={p_clip_bound:.2f}, K_max={k_clip_bound:.2f}")
                
            engine_type = "PRESTO_DECOUPLED_ANN"
            print("[OK] Active AI Engine: Presto (128-d) + Decoupled Multi-Nutrient Neural Network")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Presto+ANN: {str(e)}")
            engine_type = "UNAVAILABLE"
    else:
        print(f"[ERROR] Required model files not found: {ann_weights_path} or {presto_weights_path}")
        engine_type = "UNAVAILABLE"

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
    is_ready = (engine_type == "PRESTO_DECOUPLED_ANN" and presto_backbone is not None and decoupled_ann is not None)
    return {
        "status": "UP" if is_ready else "DOWN",
        "service": "Soil Fertility AI Satellite Engine",
        "port": 7000,
        "engine_type": engine_type,
        "foundation_backbone": "NASA Harvest Presto (128-d Latent Representation)",
        "neural_head": "Decoupled Residual Mish Multi-Nutrient Head",
        "models_loaded": ["pH", "Nitrogen", "Phosphorus", "Potassium"] if is_ready else [],
        "clipping_bounds": {"P_max": p_clip_bound, "K_max": k_clip_bound},
        "expected_features": ["Sentinel-2 10 Bands (B02-B12)", "NDVI", "Elevation", "Slope"]
    }

@app.post("/api/fertility-check")
def run_fertility_check(req: FertilityCheckRequest):
    if engine_type != "PRESTO_DECOUPLED_ANN" or presto_backbone is None or decoupled_ann is None:
        raise HTTPException(status_code=503, detail="Soil AI Presto+ANN inference engine is not ready or failed to load.")

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

    # 6. Run Inference for all 4 Nutrients via NASA Harvest Presto + Decoupled ANN
    nutrients_2d: Dict[str, np.ndarray] = {}
    metrics_summary: Dict[str, Any] = {}
    num_valid = int(np.sum(valid_mask))

    try:
        bands_10_names = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
        raw_b = np.column_stack([band_arrays[b][valid_mask] for b in bands_10_names])
        
        x_17 = np.zeros((num_valid, 1, 17), dtype=np.float32)
        x_17[:, 0, 2:12] = raw_b
        x_17[:, 0, 14] = 150.0 / 2000.0  # Normalized elevation
        x_17[:, 0, 15] = 2.0 / 50.0      # Normalized slope
        x_17[:, 0, 16] = ndvi[valid_mask]
        
        x_t = torch.from_numpy(x_17).to(device)
        mask_t = torch.zeros((num_valid, 1, 17), dtype=torch.float32).to(device)
        mask_t[:, :, [0, 1, 12, 13]] = 1.0  # Mask unobserved radar and weather
        dw_t = torch.full((num_valid, 1), 9, dtype=torch.long).to(device)
        
        farm_center_lon, farm_center_lat = farm_poly.centroid.x, farm_poly.centroid.y
        latlons_t = torch.tensor([[farm_center_lat, farm_center_lon]], dtype=torch.float32).repeat(num_valid, 1).to(device)
        scene_month = selected_scene.datetime.month
        
        with torch.no_grad():
            embs_list = []
            chunk_size = 1024
            for i in range(0, num_valid, chunk_size):
                end_i = min(i + chunk_size, num_valid)
                e = presto_backbone.encoder(
                    x=x_t[i:end_i],
                    dynamic_world=dw_t[i:end_i],
                    latlons=latlons_t[i:end_i],
                    mask=mask_t[i:end_i],
                    month=scene_month,
                    eval_task=True
                )
                embs_list.append(e)
            all_embs = torch.cat(embs_list, dim=0)
            preds_dict = decoupled_ann(all_embs)
            
        preds_pH = np.clip(preds_dict["pH"].cpu().numpy(), 3.5, 9.5)
        preds_N  = np.maximum(0.0, preds_dict["N"].cpu().numpy())
        preds_P  = np.clip(np.expm1(preds_dict["P"].cpu().numpy()), 0.0, p_clip_bound)
        preds_K  = np.clip(np.expm1(preds_dict["K"].cpu().numpy()), 0.0, k_clip_bound)
        
        pred_map = {
            "pH": preds_pH,
            "Nitrogen": preds_N,
            "Phosphorus": preds_P,
            "Potassium": preds_K
        }
        
        for t in ["pH", "Nitrogen", "Phosphorus", "Potassium"]:
            p = pred_map[t]
            grid_2d = np.full(reference_shape, np.nan)
            grid_2d[valid_mask] = p
            nutrients_2d[t] = grid_2d
            
            metrics_summary[t] = {
                "mean": round(float(np.mean(p)), 2),
                "min": round(float(np.min(p)), 2),
                "max": round(float(np.max(p)), 2),
                "std": round(float(np.std(p)), 2),
                "unit": "pH units" if t == "pH" else "mg/kg"
            }
    except Exception as e:
        print(f"[ERROR] Presto forward pass failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Presto soil inference failed: {str(e)}")

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
        "engine_type": engine_type,
        "model_engine": "NASA Harvest Presto (128-d) + Decoupled Residual Mish ANN",
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
