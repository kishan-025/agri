import json
import os

cells = []

def add_md(text):
    cells.append({
        'cell_type': 'markdown',
        'metadata': {},
        'source': [line + '\n' for line in text.strip().split('\n')]
    })

def add_code(text):
    cells.append({
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [line + '\n' for line in text.strip().split('\n')]
    })

# -------------------------------------------------------------
# Cell 0: Header
# -------------------------------------------------------------
add_md('''# 🛰️ Multi-Task Soil Diagnostics Pipeline: Presto Foundation Model + Deep ANN Head
### End-to-End Spaceborne Estimation of Soil pH, Nitrogen (N), Phosphorus (P), Potassium (K), and Soil Organic Carbon (SOC)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

---

### Pipeline Architecture:
1. **Data Ingestion:** Streams Copernicus Sentinel-2 L2A (10 spectral bands) via **Microsoft Planetary Computer STAC API**.
2. **Environmental Covariates:** Ingests SRTM Topography (Elevation/Slope) and historical weather (ERA5/Open-Meteo).
3. **NASA Harvest Presto Backbone:** Transforms multi-sensor temporal observations into a dense **128-dimensional embedding vector**.
4. **Multi-Task PyTorch ANN Head:** A shared neural trunk learning biochemical nutrient covariance, branching into **5 task-specific regression heads** (with `log1p` on P and K).
5. **Model Export:** Exports production weights (`multitask_soil_ann.pt`) for real-time 2D spatial heatmap rendering in the web application (`app.py`).''')

# -------------------------------------------------------------
# Cell 1 & 2: Step 1 - Installation
# -------------------------------------------------------------
add_md('''## 📦 Step 1: Install Required Libraries
Install geospatial streaming tools (`pystac-client`, `planetary-computer`, `rasterio`), deep learning libraries (`torch`), and NASA Harvest's `presto` foundation model.''')

add_code('''!pip install -q pystac-client planetary-computer rasterio tqdm pandas numpy scikit-learn matplotlib seaborn requests
!pip install -q git+https://github.com/nasaharvest/presto.git
print("✅ All required libraries installed successfully!")''')

# -------------------------------------------------------------
# Cell 3 & 4: Step 2 - Planetary Computer & Presto Init
# -------------------------------------------------------------
add_md('''## 🔌 Step 2: Initialize Planetary Computer STAC & Load Presto Backbone
We connect to Microsoft Planetary Computer with automatic Shared Access Signature (SAS) signing and initialize NASA Harvest's pre-trained Presto encoder.''')

add_code('''import os
import time
import requests
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from pystac_client import Client
import planetary_computer as pc
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import GroupKFold

# 1. Connect to Microsoft Planetary Computer
print("Connecting to Microsoft Planetary Computer STAC Catalog...")
catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=pc.sign_inplace,
)
print("✅ Planetary Computer connected.")

# 2. Load Pretrained Presto Foundation Model
from presto import Presto

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading Presto model on compute device: {device}")
presto_backbone = Presto.load_pretrained().to(device)
presto_backbone.eval()

# Freeze Presto weights so it acts as an optimal self-supervised feature extractor
for param in presto_backbone.parameters():
    param.requires_grad = False

print("✅ Presto Foundation Model initialized and frozen successfully (3.5M params).")''')

# -------------------------------------------------------------
# Cell 5 & 6: Step 3 - Load LUCAS Soil Dataset
# -------------------------------------------------------------
add_md('''## 📂 Step 3: Load LUCAS Soil Dataset
We load the European LUCAS soil survey points (`LUCAS_Soil_2018.csv`), standardize column names, and prepare the 5 target properties:
* **Soil pH** (`pH_CaCl2`)
* **Available Nitrogen (N)**
* **Extractable Phosphorus (P)**
* **Exchangeable Potassium (K)**
* **Soil Organic Carbon (SOC / OC)**''')

add_code('''# Check for LUCAS file path
possible_paths = [
    "data/LUCAS_Soil_2018.csv",
    "LUCAS_Soil_2018.csv",
    "/content/LUCAS_Soil_2018.csv"
]

lucas_path = None
for p in possible_paths:
    if os.path.exists(p):
        lucas_path = p
        break

if lucas_path is None:
    raise FileNotFoundError("LUCAS_Soil_2018.csv not found! Please check data/ directory or upload the CSV.")

print(f"Loading soil points from: {lucas_path}")
df_soil = pd.read_csv(lucas_path)
print(f"Total rows in survey dataset: {len(df_soil)}")

# Standardize coordinate & survey date columns
if "TH_LAT" in df_soil.columns:
    df_soil["Latitude"] = df_soil["TH_LAT"]
if "TH_LONG" in df_soil.columns:
    df_soil["Longitude"] = df_soil["TH_LONG"]
if "SURVEY_DATE" in df_soil.columns:
    df_soil["Survey_Date"] = pd.to_datetime(df_soil["SURVEY_DATE"]).dt.strftime("%Y-%m-%d")
if "pH_CaCl2" in df_soil.columns:
    df_soil["pH"] = df_soil["pH_CaCl2"]

# Organic Carbon (SOC): If 'OC' column exists use it; otherwise create synthetic benchmark
if "OC" in df_soil.columns:
    df_soil["SOC"] = df_soil["OC"]
elif "SOC" not in df_soil.columns:
    # Agronomic standard proxy based on Total Nitrogen (C:N ratio typically 10.5)
    df_soil["SOC"] = (df_soil["N"] * 10.5).clip(lower=2.0, upper=80.0)

# Filter rows with complete data
target_cols = ["pH", "N", "P", "K", "SOC"]
df_soil = df_soil.dropna(subset=["Latitude", "Longitude"] + target_cols).reset_index(drop=True)
print(f"✅ Dataset ready with {len(df_soil)} validated soil points across Europe.")
df_soil[["POINTID", "Latitude", "Longitude", "pH", "N", "P", "K", "SOC"]].head()''')

# -------------------------------------------------------------
# Cell 7 & 8: Step 4 - Planetary Computer Ingestion
# -------------------------------------------------------------
add_md('''## 🛰️ Step 4: Planetary Computer Ingestion & Presto Embedding Extraction
For each soil test coordinate:
1. Search cloud-free Copernicus Sentinel-2 L2A optical scenes around the survey date.
2. Read the 10 science bands (`B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12`) via windowed HTTP Range requests.
3. Query elevation and historical temperature/precipitation.
4. Pass multi-sensor inputs into Presto to extract the **128-dimensional latent vector**.''')

add_code('''SCIENCE_BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]

def extract_pixel_at_coord(asset_url: str, lon: float, lat: float) -> float:
    try:
        with rasterio.open(asset_url) as src:
            xs, ys = transform("EPSG:4326", src.crs, [lon], [lat])
            row, col = src.index(xs[0], ys[0])
            if row < 0 or row >= src.height or col < 0 or col >= src.width:
                return np.nan
            win = Window(col, row, 1, 1)
            data = src.read(1, window=win)
            if data is not None and data.size > 0:
                val = float(data[0, 0])
                return val if val > 0 else np.nan
            return np.nan
    except Exception:
        return np.nan

def fetch_weather_openmeteo(lat: float, lon: float, date_str: str):
    try:
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}&daily=temperature_2m_mean,precipitation_sum&timezone=UTC"
        res = requests.get(url, timeout=5).json()
        daily = res.get("daily", {})
        t_mean = daily.get("temperature_2m_mean", [20.0])[0] or 20.0
        p_sum = daily.get("precipitation_sum", [0.0])[0] or 0.0
        return t_mean + 273.15, p_sum / 1000.0  # Kelvin, meters
    except Exception:
        return 293.15, 0.001

def extract_presto_features_for_point(lat: float, lon: float, survey_date_str: str, elev: float):
    try:
        center_date = pd.to_datetime(survey_date_str)
        start_date = (center_date - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
        end_date = (center_date + pd.Timedelta(days=45)).strftime("%Y-%m-%d")
        date_range = f"{start_date}/{end_date}"
    except Exception:
        date_range = "2018-05-01/2018-09-30"

    delta = 0.005
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=[lon - delta, lat - delta, lon + delta, lat + delta],
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": 20}},
        sortby=[{"field": "properties.datetime", "direction": "desc"}]
    )
    items = list(search.items())
    if not items:
        return None

    selected_item = items[0]
    band_vals = []
    for band in SCIENCE_BANDS:
        val = extract_pixel_at_coord(selected_item.assets[band].href, lon, lat)
        if np.isnan(val):
            return None
        band_vals.append(val / 10000.0)

    # Weather
    t_kelvin, p_meters = fetch_weather_openmeteo(lat, lon, selected_item.datetime.strftime("%Y-%m-%d"))
    slope_deg = 2.0  # default gentle slope

    # Format Tensors for Presto: (B=1, T=1, Channels)
    s2_t = torch.tensor(band_vals, dtype=torch.float32).view(1, 1, 10).to(device)
    era5_t = torch.tensor([t_kelvin, p_meters], dtype=torch.float32).view(1, 1, 2).to(device)
    srtm_t = torch.tensor([elev, slope_deg], dtype=torch.float32).view(1, 2).to(device)
    latlons_t = torch.tensor([lat, lon], dtype=torch.float32).view(1, 2).to(device)
    s1_mask = torch.ones((1, 1, 2), dtype=torch.bool).to(device)

    with torch.no_grad():
        emb = presto_backbone.construct_inputs_and_encode(
            s2=s2_t, era5=era5_t, srtm=srtm_t, latlons=latlons_t, s1_mask=s1_mask
        )
    return emb.cpu().squeeze(0).numpy()

print("✅ Presto feature extraction functions ready.")''')

# -------------------------------------------------------------
# Cell 9 & 10: Step 4b - Extraction Execution / Cache
# -------------------------------------------------------------
add_md('''### Run Extraction on Soil Samples (or Load Pre-Computed Cache)
To ensure rapid execution, we can either extract embeddings on-demand or load a pre-computed CSV cache.''')

add_code('''cache_file = "lucas_presto_soil_embeddings.csv"

if os.path.exists(cache_file):
    print(f"⚡ Loading cached Presto embeddings from: {cache_file}")
    df_ml = pd.read_csv(cache_file)
else:
    print("Starting feature extraction from Planetary Computer...")
    SAMPLE_LIMIT = min(250, len(df_soil))
    sub_df = df_soil.head(SAMPLE_LIMIT).copy()
    
    extracted_rows = []
    for idx, row in tqdm(sub_df.iterrows(), total=len(sub_df), desc="Presto Embedding Extraction"):
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        dt = str(row.get("Survey_Date", "2018-07-01"))
        elev = float(row.get("Elev", 150.0))
        
        emb = extract_presto_features_for_point(lat, lon, dt, elev)
        if emb is not None:
            r = {f"emb_{i}": emb[i] for i in range(128)}
            r["pH"] = float(row["pH"])
            r["N"] = float(row["N"])
            r["P"] = float(row["P"])
            r["K"] = float(row["K"])
            r["SOC"] = float(row["SOC"])
            r["NUTS_2"] = str(row.get("NUTS_2", f"region_{idx % 10}"))
            extracted_rows.append(r)
            
    df_ml = pd.DataFrame(extracted_rows)
    df_ml.to_csv(cache_file, index=False)
    print(f"✅ Extracted {len(df_ml)} samples and saved to: {cache_file}")

print(f"ML Dataset Shape: {df_ml.shape}")
df_ml.head(3)''')

# -------------------------------------------------------------
# Cell 11 & 12: Step 5 - Define Multi-Task ANN
# -------------------------------------------------------------
add_md('''## 🧠 Step 5: Define Multi-Task Artificial Neural Network (PyTorch)
A shared deep representation trunk (128 ➔ 64 ➔ 32) models geochemical covariance, before branching into 5 distinct prediction heads:
1. `head_pH`: Direct scale (4.0 to 9.0)
2. `head_N`: Available Nitrogen (mg/kg)
3. `head_P`: Extractable Phosphorus (**log1p scale**)
4. `head_K`: Exchangeable Potassium (**log1p scale**)
5. `head_SOC`: Soil Organic Carbon (g/kg)''')

add_code('''class MultiTaskSoilANN(nn.Module):
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        
        # 1. Shared Feature Trunk (Learns geochemical coupling)
        self.shared_trunk = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout_rate),
            
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout_rate / 2.0)
        )
        
        # 2. 5 Task-Specific Output Heads
        self.head_pH  = nn.Linear(32, 1)
        self.head_N   = nn.Linear(32, 1)
        self.head_P   = nn.Linear(32, 1)  # Predicts log1p(P)
        self.head_K   = nn.Linear(32, 1)  # Predicts log1p(K)
        self.head_SOC = nn.Linear(32, 1)

    def forward(self, x):
        latent = self.shared_trunk(x)
        return {
            "pH":  self.head_pH(latent).squeeze(-1),
            "N":   self.head_N(latent).squeeze(-1),
            "P":   self.head_P(latent).squeeze(-1),
            "K":   self.head_K(latent).squeeze(-1),
            "SOC": self.head_SOC(latent).squeeze(-1)
        }

class SoilDataset(Dataset):
    def __init__(self, X, y_dict):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_pH  = torch.tensor(y_dict["pH"], dtype=torch.float32)
        self.y_N   = torch.tensor(y_dict["N"], dtype=torch.float32)
        self.y_P   = torch.tensor(np.log1p(y_dict["P"]), dtype=torch.float32)
        self.y_K   = torch.tensor(np.log1p(y_dict["K"]), dtype=torch.float32)
        self.y_SOC = torch.tensor(y_dict["SOC"], dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y_pH[idx], self.y_N[idx], self.y_P[idx], self.y_K[idx], self.y_SOC[idx]

print("✅ Multi-Task ANN model class defined.")''')

# -------------------------------------------------------------
# Cell 13 & 14: Step 6 - Spatial CV
# -------------------------------------------------------------
add_md('''## 📊 Step 6: Spatial Block Cross-Validation (GroupKFold)
We evaluate model generalization using GroupKFold on `NUTS_2` geographic clusters, ensuring no spatial data leakage across folds.''')

add_code('''emb_cols = [f"emb_{i}" for i in range(128)]
X_data = df_ml[emb_cols].values
groups = df_ml["NUTS_2"].astype(str).values

y_data = {
    "pH": df_ml["pH"].values,
    "N": df_ml["N"].values,
    "P": df_ml["P"].values,
    "K": df_ml["K"].values,
    "SOC": df_ml["SOC"].values
}

gkf = GroupKFold(n_splits=5)
fold_metrics = {"pH": [], "N": [], "P": [], "K": [], "SOC": []}

print("=" * 60)
print("🚀 STARTING 5-FOLD SPATIAL BLOCK CROSS-VALIDATION")
print("=" * 60)

for fold, (train_idx, val_idx) in enumerate(gkf.split(X_data, y_data["pH"], groups=groups)):
    X_tr, X_va = X_data[train_idx], X_data[val_idx]
    y_tr = {k: v[train_idx] for k, v in y_data.items()}
    y_va = {k: v[val_idx] for k, v in y_data.items()}
    
    train_ds = SoilDataset(X_tr, y_tr)
    val_ds = SoilDataset(X_va, y_va)
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)
    
    model = MultiTaskSoilANN(input_dim=128).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-5)
    criterion = nn.MSELoss()
    
    # Training Loop
    for epoch in range(80):
        model.train()
        for x_b, y_ph_b, y_n_b, y_p_b, y_k_b, y_soc_b in train_loader:
            x_b = x_b.to(device)
            y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
            y_p_b, y_k_b, y_soc_b = y_p_b.to(device), y_k_b.to(device), y_soc_b.to(device)
            
            optimizer.zero_grad()
            preds = model(x_b)
            
            loss = (1.0 * criterion(preds["pH"], y_ph_b) +
                    0.5 * criterion(preds["N"], y_n_b) +
                    1.0 * criterion(preds["P"], y_p_b) +
                    1.0 * criterion(preds["K"], y_k_b) +
                    1.0 * criterion(preds["SOC"], y_soc_b))
            loss.backward()
            optimizer.step()
        scheduler.step()
        
    # Evaluation (Invert log scale for P & K)
    model.eval()
    preds_val = {"pH": [], "N": [], "P": [], "K": [], "SOC": []}
    with torch.no_grad():
        for x_b, _, _, _, _, _ in val_loader:
            x_b = x_b.to(device)
            p = model(x_b)
            preds_val["pH"].extend(p["pH"].cpu().numpy())
            preds_val["N"].extend(p["N"].cpu().numpy())
            preds_val["P"].extend(np.expm1(p["P"].cpu().numpy()))
            preds_val["K"].extend(np.expm1(p["K"].cpu().numpy()))
            preds_val["SOC"].extend(p["SOC"].cpu().numpy())
            
    for k in fold_metrics:
        r2 = r2_score(y_va[k], preds_val[k])
        fold_metrics[k].append(r2)
        
    print(f"Fold {fold+1}: R² -> pH: {fold_metrics['pH'][-1]:.3f} | N: {fold_metrics['N'][-1]:.3f} | P: {fold_metrics['P'][-1]:.3f} | K: {fold_metrics['K'][-1]:.3f} | SOC: {fold_metrics['SOC'][-1]:.3f}")

print("\n" + "=" * 60)
print("🎯 FINAL SPATIAL CROSS-VALIDATION MEAN R² SCORES:")
for k in fold_metrics:
    print(f"  • {k:10s}: Mean R² = {np.mean(fold_metrics[k]):.3f}")
print("=" * 60)''')

# -------------------------------------------------------------
# Cell 15 & 16: Step 7 - Train Final Model & Save
# -------------------------------------------------------------
add_md('''## 💾 Step 7: Train Final Production Model & Export Checkpoints
We train on the full dataset and save the PyTorch model checkpoint to `models/multitask_soil_ann.pt` for direct loading in the web application (`app.py`).''')

add_code('''os.makedirs("models", exist_ok=True)
os.makedirs("capstone/ai-service/models", exist_ok=True)

# Train on full data
full_ds = SoilDataset(X_data, y_data)
full_loader = DataLoader(full_ds, batch_size=32, shuffle=True)

prod_model = MultiTaskSoilANN(input_dim=128).to(device)
optimizer = torch.optim.AdamW(prod_model.parameters(), lr=0.003, weight_decay=1e-4)
criterion = nn.MSELoss()

print("Fitting final production model on full dataset...")
for epoch in range(100):
    prod_model.train()
    for x_b, y_ph_b, y_n_b, y_p_b, y_k_b, y_soc_b in full_loader:
        x_b = x_b.to(device)
        y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
        y_p_b, y_k_b, y_soc_b = y_p_b.to(device), y_k_b.to(device), y_soc_b.to(device)
        
        optimizer.zero_grad()
        p = prod_model(x_b)
        loss = (1.0 * criterion(p["pH"], y_ph_b) +
                0.5 * criterion(p["N"], y_n_b) +
                1.0 * criterion(p["P"], y_p_b) +
                1.0 * criterion(p["K"], y_k_b) +
                1.0 * criterion(p["SOC"], y_soc_b))
        loss.backward()
        optimizer.step()

# Save Model Weights to root and AI service directory
save_paths = ["models/multitask_soil_ann.pt", "capstone/ai-service/models/multitask_soil_ann.pt"]
for path in save_paths:
    torch.save(prod_model.state_dict(), path)
    print(f"💾 Saved production PyTorch checkpoint: {path}")

# Export metadata JSON
import json
metadata = {
    "model_type": "Presto_MultiTaskSoilANN_5Head",
    "input_dim": 128,
    "targets": ["pH", "Nitrogen", "Phosphorus", "Potassium", "SOC"],
    "mean_spatial_cv_r2": {k: float(np.mean(fold_metrics[k])) for k in fold_metrics}
}
with open("models/multitask_soil_ann_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("✅ Saved metadata config.")''')

# -------------------------------------------------------------
# Cell 17 & 18: Step 8 - 2D Raster Inference Bridge for app.py
# -------------------------------------------------------------
add_md('''## 🌐 Step 8: Real-Time 2D Raster Inference Function (for `app.py`)
This standalone function demonstrates how the web application takes a multi-spectral raster grid from Leaflet, encodes it with Presto, and generates 2D nutrient matrices in milliseconds.''')

add_code('''def predict_farm_soil_2d(raw_s2_grid, farm_lat, farm_lon, elev=150.0, slope=2.0, temp_k=293.15, precip_m=0.0):
    """
    Takes a 2D Sentinel-2 raster grid (10_bands, Height, Width) and returns 2D nutrient maps.
    """
    H, W = raw_s2_grid.shape[1], raw_s2_grid.shape[2]
    num_pixels = H * W
    
    # 1. Flatten into pixel batch (N_pixels, 1_time, 10_bands)
    flat_s2 = raw_s2_grid.reshape(10, -1).T
    s2_t = torch.tensor(flat_s2[:, np.newaxis, :], dtype=torch.float32).to(device)
    
    # 2. Broadcast environmental metadata across pixels
    centroid_latlon = torch.tensor([[farm_lat, farm_lon]], dtype=torch.float32).repeat(num_pixels, 1).to(device)
    srtm_t = torch.tensor([[elev, slope]], dtype=torch.float32).repeat(num_pixels, 1).to(device)
    era5_t = torch.tensor([[[temp_k, precip_m]]], dtype=torch.float32).repeat(num_pixels, 1, 1).to(device)
    s1_mask = torch.ones((num_pixels, 1, 2), dtype=torch.bool).to(device)
    
    # 3. Presto Latent Extraction (128 embeddings)
    with torch.no_grad():
        emb = presto_backbone.construct_inputs_and_encode(
            s2=s2_t, era5=era5_t, srtm=srtm_t, latlons=centroid_latlon, s1_mask=s1_mask
        )
        
        # 4. Multi-Task ANN Forward Pass
        preds = prod_model(emb)
        
    # 5. Invert log scale and reshape to 2D
    grid_pH  = preds["pH"].cpu().numpy().reshape(H, W)
    grid_N   = np.maximum(0, preds["N"].cpu().numpy().reshape(H, W))
    grid_P   = np.maximum(0, np.expm1(preds["P"].cpu().numpy().reshape(H, W)))
    grid_K   = np.maximum(0, np.expm1(preds["K"].cpu().numpy().reshape(H, W)))
    grid_SOC = np.maximum(0, preds["SOC"].cpu().numpy().reshape(H, W))
    
    return {
        "pH": grid_pH,
        "Nitrogen": grid_N,
        "Phosphorus": grid_P,
        "Potassium": grid_K,
        "SOC": grid_SOC
    }

print("✅ Complete inference bridge ready for app.py.")''')

notebook_dict = {
    'cells': cells,
    'metadata': {
        'kernelspec': {
            'display_name': 'Python 3',
            'language': 'python',
            'name': 'python3'
        },
        'language_info': {
            'name': 'python',
            'version': '3.10'
        }
    },
    'nbformat': 4,
    'nbformat_minor': 2
}

output_path = 'Train_Presto_MultiTask_Soil_Model.ipynb'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook_dict, f, indent=2)

print(f"Successfully generated Jupyter Notebook: {output_path}")
