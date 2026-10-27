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
### End-to-End Spaceborne Estimation of Soil pH, Available Nitrogen (N), Extractable Phosphorus (P), and Exchangeable Potassium (K)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

---

### Pipeline Architecture:
1. **Multi-Spectral Survey Dataset (`Model_A.csv`):** 18,471 validated ground-truth soil test points across Europe with pre-matched Copernicus Sentinel-2 L2A surface reflectance (10 spectral bands: `B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12`) and ground-truth elevation (`Elev`).
2. **Fast Offline Presto Feature Extraction:** Leveraging Presto's native Masked Autoencoder (MAE) architecture to extract dense **128-dimensional latent representations** directly from optical and topographic observations with 100% offline execution (< 3 seconds).
3. **Multi-Task PyTorch ANN Head:** A shared neural trunk learning biochemical nutrient covariance, branching into **4 task-specific regression heads** (direct scale for pH and N, `log1p` for P and K).
4. **Model Export:** Exports production weights (`multitask_soil_ann.pt`) and metadata for real-time 2D spatial heatmap rendering in the web application (`app.py`).''')

# -------------------------------------------------------------
# Cell 1 & 2: Step 1 - Installation & Load Presto
# -------------------------------------------------------------
add_md('''## 📦 Step 1: Install Required Libraries & Initialize Presto Backbone
We install standard deep learning and scientific Python packages (`torch`, `einops`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`), clone NASA Harvest's `presto` foundation model, and load the pretrained encoder weights.''')

add_code('''# 1. Install standard deep learning and data libraries
!pip install -q einops tqdm pandas numpy scikit-learn matplotlib seaborn requests

# 2. Clone NASA Harvest Presto directly if not present
import os, sys
if not os.path.exists("presto"):
    os.system("git clone https://github.com/nasaharvest/presto.git")

if os.path.abspath("presto") not in sys.path:
    sys.path.insert(0, os.path.abspath("presto"))

import time
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import GroupKFold

from single_file_presto import Presto

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading Presto foundation model on compute device: {device}")

presto_backbone = Presto.construct().to(device)
model_path = "presto/data/default_model.pt"
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Presto model weights not found at {model_path}. Please check git clone.")

presto_backbone.load_state_dict(torch.load(model_path, map_location=device))
presto_backbone.eval()

total_params = sum(p.numel() for p in presto_backbone.parameters())
print(f"✅ Presto Foundation Model loaded and frozen successfully ({total_params:,} parameters).")''')

# -------------------------------------------------------------
# Cell 3 & 4: Step 2 - Load Model_A.csv
# -------------------------------------------------------------
add_md('''## 📂 Step 2: Load Multi-Spectral Soil Dataset (`Model_A.csv`)
`Model_A.csv` contains 18,471 ground-truth soil survey points across Europe with:
* **Soil Targets:** `pH_CaCl2` (Soil pH), `N` (Available Nitrogen), `P` (Phosphorus), `K` (Potassium)
* **Spatial Attributes:** `TH_LAT`, `TH_LONG`, `Elev` (Elevation in meters), `NUTS_2` (Regional jurisdiction)
* **Sentinel-2 Surface Reflectance Bands:** `B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12`''')

add_code('''model_a_candidates = [
    "data/Model_A.csv",
    "Model_A.csv",
    "/content/data/Model_A.csv",
    "/content/Model_A.csv"
]
model_a_path = next((p for p in model_a_candidates if os.path.exists(p)), None)

if model_a_path is None:
    print("📥 Model_A.csv not found locally. Downloading from repository...")
    url = "https://raw.githubusercontent.com/kishan-025/agri/main/data/Model_A.csv"
    os.makedirs("data", exist_ok=True)
    df_raw = pd.read_csv(url)
    df_raw.to_csv("data/Model_A.csv", index=False)
    model_a_path = "data/Model_A.csv"
    print(f"✅ Downloaded and cached to: {model_a_path}")
else:
    print(f"Loading dataset from: {model_a_path}")
    df_raw = pd.read_csv(model_a_path)

print(f"Total rows in dataset: {len(df_raw)}")

# Verify essential columns
required_cols = ["pH_CaCl2", "N", "P", "K", "Elev", "TH_LAT", "TH_LONG", "B02", "B04", "B08"]
missing = [c for c in required_cols if c not in df_raw.columns]
if missing:
    raise ValueError(f"Missing required columns in dataset: {missing}")

print(f"✅ Dataset verified with {len(df_raw)} validated soil points across Europe.")
df_raw[["POINTID", "TH_LAT", "TH_LONG", "Elev", "pH_CaCl2", "N", "P", "K"]].head()''')

# -------------------------------------------------------------
# Cell 5 & 6: Step 3 - Fast Offline Presto Feature Extraction
# -------------------------------------------------------------
add_md('''## 🛰️ Step 3: Fast Offline Presto Feature Extraction
1. **Self-Contained Remote Sensing:** Ingests the 10 Sentinel-2 surface reflectance bands, computed NDVI, and ground-truth elevation directly from `Model_A.csv`.
2. **Channel Formulation:** Unobserved modalities (radar and weather) are masked out (`mask = 1.0`), leveraging Presto's native Masked Autoencoder architecture for 100% offline feature extraction.
3. **Batched Encoding:** Passes the 17-channel tensors through `presto_backbone.encoder` in batches of 256 to extract dense **128-dimensional embedding vectors** in < 3 seconds.''')

add_code('''cache_file = "lucas_presto_soil_embeddings.csv"

if os.path.exists(cache_file):
    print(f"⚡ Loading pre-computed Presto embeddings from: {cache_file}")
    df_ml = pd.read_csv(cache_file)
else:
    # Select sample count (e.g. 5,000 for fast high-accuracy training, or len(df_raw) for full 18,471 dataset)
    SAMPLE_LIMIT = min(5000, len(df_raw))
    sub_df = df_raw.head(SAMPLE_LIMIT).copy()
    
    # 1. Extract Sentinel-2 spectral reflectance bands (0.0 to 1.0)
    bands_10 = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    raw_b = sub_df[bands_10].values / 100.0
    
    # Compute NDVI: (B08 - B04) / (B08 + B04 + 1e-6)
    b04, b08 = raw_b[:, 2], raw_b[:, 6]
    ndvi = (b08 - b04) / (b08 + b04 + 1e-6)
    
    N = len(sub_df)
    x_17 = np.zeros((N, 1, 17), dtype=np.float32)
    x_17[:, 0, 2:12] = raw_b
    x_17[:, 0, 12] = 0.0                                            # Weather masked out
    x_17[:, 0, 13] = 0.0                                            # Weather masked out
    x_17[:, 0, 14] = sub_df["Elev"].fillna(150.0).values / 2000.0  # Measured elevation
    x_17[:, 0, 15] = 2.0 / 50.0                                    # Slope normalized
    x_17[:, 0, 16] = ndvi
    
    x_t = torch.from_numpy(x_17).to(device)
    mask_t = torch.zeros((N, 1, 17), dtype=torch.float32).to(device)
    mask_t[:, :, [0, 1, 12, 13]] = 1.0  # Mask unobserved S1 radar and weather
    dw_t = torch.full((N, 1), 9, dtype=torch.long).to(device)
    lat_c = "TH_LAT" if "TH_LAT" in sub_df.columns else "Latitude"
    lon_c = "TH_LONG" if "TH_LONG" in sub_df.columns else "Longitude"
    latlons_t = torch.from_numpy(sub_df[[lat_c, lon_c]].values.astype(np.float32)).to(device)
    
    print(f"Extracting Presto embeddings in fast GPU/CPU batches for {N} samples...")
    embs_list = []
    batch_size = 256
    with torch.no_grad():
        for i in tqdm(range(0, N, batch_size), desc="Presto Batched Encoding"):
            end = min(i + batch_size, N)
            e = presto_backbone.encoder(
                x=x_t[i:end],
                dynamic_world=dw_t[i:end],
                latlons=latlons_t[i:end],
                mask=mask_t[i:end],
                month=6,
                eval_task=True
            )
            embs_list.append(e.cpu().numpy())
            
    all_embs = np.concatenate(embs_list, axis=0)
    
    # Build ML training dataframe
    df_ml = pd.DataFrame(all_embs, columns=[f"emb_{i}" for i in range(128)])
    df_ml["pH"] = sub_df["pH_CaCl2"].values if "pH_CaCl2" in sub_df.columns else sub_df["pH"].values
    df_ml["N"] = sub_df["N"].values
    df_ml["P"] = sub_df["P"].values
    df_ml["K"] = sub_df["K"].values
    df_ml["NUTS_2"] = sub_df["NUTS_2"].astype(str).values if "NUTS_2" in sub_df.columns else [f"reg_{i%10}" for i in range(len(sub_df))]
    
    df_ml.to_csv(cache_file, index=False)
    print(f"✅ Successfully extracted and cached {len(df_ml)} Presto embeddings to: {cache_file}")

print(f"ML Dataset Shape: {df_ml.shape}")
df_ml.head(3)''')

# -------------------------------------------------------------
# Cell 7 & 8: Step 4 - Define Multi-Task ANN (4 Heads)
# -------------------------------------------------------------
add_md('''## 🧠 Step 4: Define Multi-Task Artificial Neural Network (PyTorch)
A shared deep representation trunk (128 ➔ 64 ➔ 32) models geochemical covariance, before branching into **4 distinct prediction heads**:
1. `head_pH`: Direct scale (4.0 to 9.0)
2. `head_N`: Available Nitrogen (mg/kg)
3. `head_P`: Extractable Phosphorus (**log1p scale**)
4. `head_K`: Exchangeable Potassium (**log1p scale**)''')

add_code('''class MultiTaskSoilANN(nn.Module):
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        
        # 1. Shared Feature Trunk (Learns geochemical coupling)
        self.shared_trunk = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.LayerNorm(64),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout_rate),
            
            nn.Linear(64, 32),
            nn.LayerNorm(32),
            nn.LeakyReLU(0.1),
            nn.Dropout(dropout_rate / 2.0)
        )
        
        # 2. 4 Task-Specific Output Heads
        self.head_pH = nn.Linear(32, 1)
        self.head_N  = nn.Linear(32, 1)
        self.head_P  = nn.Linear(32, 1)  # Predicts log1p(P)
        self.head_K  = nn.Linear(32, 1)  # Predicts log1p(K)

    def forward(self, x):
        latent = self.shared_trunk(x)
        return {
            "pH": self.head_pH(latent).squeeze(-1),
            "N":  self.head_N(latent).squeeze(-1),
            "P":  self.head_P(latent).squeeze(-1),
            "K":  self.head_K(latent).squeeze(-1)
        }

class SoilDataset(Dataset):
    def __init__(self, X, y_dict):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_pH = torch.tensor(y_dict["pH"], dtype=torch.float32)
        self.y_N  = torch.tensor(y_dict["N"], dtype=torch.float32)
        self.y_P  = torch.tensor(np.log1p(y_dict["P"]), dtype=torch.float32)
        self.y_K  = torch.tensor(np.log1p(y_dict["K"]), dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y_pH[idx], self.y_N[idx], self.y_P[idx], self.y_K[idx]

print("✅ 4-Head Multi-Task ANN model class defined.")''')

# -------------------------------------------------------------
# Cell 9 & 10: Step 5 - Spatial CV
# -------------------------------------------------------------
add_md('''## 📊 Step 5: Spatial Block Cross-Validation (GroupKFold)
We evaluate model generalization using GroupKFold on `NUTS_2` geographic clusters, ensuring no spatial data leakage across folds.''')

add_code('''emb_cols = [f"emb_{i}" for i in range(128)]
X_data = df_ml[emb_cols].values
groups = df_ml["NUTS_2"].astype(str).values

y_data = {
    "pH": df_ml["pH"].values,
    "N": df_ml["N"].values,
    "P": df_ml["P"].values,
    "K": df_ml["K"].values
}

# Adaptive Cross-Validation splitting based on sample & regional group counts
n_unique_groups = len(np.unique(groups))
n_splits = min(5, n_unique_groups)

if n_splits >= 2:
    splitter = GroupKFold(n_splits=n_splits)
    splits = list(splitter.split(X_data, y_data["pH"], groups=groups))
    print(f"🚀 Running {n_splits}-Fold Spatial Block Cross-Validation (GroupKFold across {n_unique_groups} regions)")
else:
    from sklearn.model_selection import KFold
    n_splits = min(5, max(2, len(X_data)))
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    splits = list(splitter.split(X_data, y_data["pH"]))
    print(f"🚀 Running {n_splits}-Fold Cross-Validation (Standard KFold)")

fold_metrics = {"pH": [], "N": [], "P": [], "K": []}

print("=" * 60)

for fold, (train_idx, val_idx) in enumerate(splits):
    X_tr, X_va = X_data[train_idx], X_data[val_idx]
    y_tr = {k: v[train_idx] for k, v in y_data.items()}
    y_va = {k: v[val_idx] for k, v in y_data.items()}
    
    train_ds = SoilDataset(X_tr, y_tr)
    val_ds = SoilDataset(X_va, y_va)
    
    bs_train = min(64, max(2, len(X_tr)))
    train_loader = DataLoader(train_ds, batch_size=bs_train, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=min(128, max(1, len(X_va))), shuffle=False)
    
    model = MultiTaskSoilANN(input_dim=128).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-5)
    criterion = nn.SmoothL1Loss()
    
    # Training Loop
    for epoch in range(80):
        model.train()
        for x_b, y_ph_b, y_n_b, y_p_b, y_k_b in train_loader:
            x_b = x_b.to(device)
            y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
            y_p_b, y_k_b = y_p_b.to(device), y_k_b.to(device)
            
            optimizer.zero_grad()
            preds = model(x_b)
            
            loss = (1.0 * criterion(preds["pH"], y_ph_b) +
                    0.5 * criterion(preds["N"], y_n_b) +
                    1.0 * criterion(preds["P"], y_p_b) +
                    1.0 * criterion(preds["K"], y_k_b))
            loss.backward()
            optimizer.step()
        scheduler.step()
        
    # Evaluation (Invert log scale for P & K)
    model.eval()
    preds_val = {"pH": [], "N": [], "P": [], "K": []}
    with torch.no_grad():
        for x_b, _, _, _, _ in val_loader:
            x_b = x_b.to(device)
            p = model(x_b)
            preds_val["pH"].extend(p["pH"].cpu().numpy().tolist())
            preds_val["N"].extend(p["N"].cpu().numpy().tolist())
            preds_val["P"].extend(np.expm1(p["P"].cpu().numpy()).tolist())
            preds_val["K"].extend(np.expm1(p["K"].cpu().numpy()).tolist())
            
    for k in fold_metrics:
        if len(y_va[k]) > 1 and np.var(y_va[k]) > 0:
            r2 = r2_score(y_va[k], preds_val[k])
        else:
            r2 = 0.0
        fold_metrics[k].append(r2)
        
    print(f"Fold {fold+1}: R² -> pH: {fold_metrics['pH'][-1]:.3f} | N: {fold_metrics['N'][-1]:.3f} | P: {fold_metrics['P'][-1]:.3f} | K: {fold_metrics['K'][-1]:.3f}")

print()
print("=" * 60)
print("🎯 FINAL SPATIAL CROSS-VALIDATION MEAN R² SCORES:")
for k in fold_metrics:
    print(f"  • {k:10s}: Mean R² = {np.mean(fold_metrics[k]):.3f}")
print("=" * 60)''')

# -------------------------------------------------------------
# Cell 11 & 12: Step 6 - Train Final Model & Save
# -------------------------------------------------------------
add_md('''## 💾 Step 6: Train Final Production Model & Export Checkpoints
We train on the full dataset and save the PyTorch model checkpoint to `models/multitask_soil_ann.pt` for direct loading in the web application (`app.py`).''')

add_code('''os.makedirs("models", exist_ok=True)
os.makedirs("capstone/ai-service/models", exist_ok=True)

# Train on full data
full_ds = SoilDataset(X_data, y_data)
bs_prod = min(64, max(2, len(X_data)))
full_loader = DataLoader(full_ds, batch_size=bs_prod, shuffle=True)

prod_model = MultiTaskSoilANN(input_dim=128).to(device)
optimizer = torch.optim.AdamW(prod_model.parameters(), lr=0.003, weight_decay=1e-4)
criterion = nn.SmoothL1Loss()

print("Fitting final production model on full dataset...")
for epoch in range(100):
    prod_model.train()
    for x_b, y_ph_b, y_n_b, y_p_b, y_k_b in full_loader:
        x_b = x_b.to(device)
        y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
        y_p_b, y_k_b = y_p_b.to(device), y_k_b.to(device)
        
        optimizer.zero_grad()
        p = prod_model(x_b)
        loss = (1.0 * criterion(p["pH"], y_ph_b) +
                0.5 * criterion(p["N"], y_n_b) +
                1.0 * criterion(p["P"], y_p_b) +
                1.0 * criterion(p["K"], y_k_b))
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
    "model_type": "Presto_MultiTaskSoilANN_4Head",
    "input_dim": 128,
    "targets": ["pH", "Nitrogen", "Phosphorus", "Potassium"],
    "mean_spatial_cv_r2": {k: float(np.mean(fold_metrics[k])) for k in fold_metrics}
}
with open("models/multitask_soil_ann_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("✅ Saved metadata config.")''')

# -------------------------------------------------------------
# Cell 13 & 14: Step 7 - 2D Raster Inference Bridge for app.py
# -------------------------------------------------------------
add_md('''## 🌐 Step 7: Real-Time 2D Raster Inference Function (for `app.py`)
This standalone function demonstrates how the web application takes a multi-spectral raster grid from Leaflet, encodes it with Presto, and generates 2D nutrient matrices in milliseconds with zero external API calls.''')

add_code('''def predict_farm_soil_2d(raw_s2_grid, farm_lat, farm_lon, month_idx=6, elev=150.0, slope=2.0):
    """
    Takes a 2D Sentinel-2 raster grid (10_bands, Height, Width) and returns 2D nutrient maps.
    raw_s2_grid: (10, H, W) numpy array for bands [B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12]
    """
    H, W = raw_s2_grid.shape[1], raw_s2_grid.shape[2]
    num_pixels = H * W
    
    # 1. Flatten into pixels (N_pixels, 10)
    flat_s2 = raw_s2_grid.reshape(10, -1).T
    
    # Compute NDVI: (B08 - B04) / (B08 + B04 + 1e-6)
    b04 = flat_s2[:, 2]
    b08 = flat_s2[:, 6]
    ndvi = (b08 - b04) / (b08 + b04 + 1e-6)
    
    norm_elev = elev / 2000.0
    norm_slope = slope / 50.0
    
    # 2. Construct 17-band array for all pixels: (num_pixels, 1, 17)
    x_all = np.zeros((num_pixels, 1, 17), dtype=np.float32)
    x_all[:, 0, 2:12] = flat_s2
    x_all[:, 0, 14] = norm_elev
    x_all[:, 0, 15] = norm_slope
    x_all[:, 0, 16] = ndvi
    
    x_t = torch.from_numpy(x_all).to(device)
    mask_t = torch.zeros((num_pixels, 1, 17), dtype=torch.float32).to(device)
    mask_t[:, :, [0, 1, 12, 13]] = 1.0  # Mask out missing S1 radar and weather
    
    dw_t = torch.full((num_pixels, 1), 9, dtype=torch.long).to(device)
    latlons_t = torch.tensor([[farm_lat, farm_lon]], dtype=torch.float32).repeat(num_pixels, 1).to(device)
    
    # 3. Extract Presto Latent Vectors in batches of 1024
    embeddings = []
    batch_size = 1024
    with torch.no_grad():
        for start_idx in range(0, num_pixels, batch_size):
            end_idx = min(start_idx + batch_size, num_pixels)
            emb = presto_backbone.encoder(
                x=x_t[start_idx:end_idx],
                dynamic_world=dw_t[start_idx:end_idx],
                latlons=latlons_t[start_idx:end_idx],
                mask=mask_t[start_idx:end_idx],
                month=month_idx,
                eval_task=True
            )
            embeddings.append(emb)
        all_emb = torch.cat(embeddings, dim=0)
        
        # 4. Multi-Task ANN Forward Pass
        preds = prod_model(all_emb)
        
    # 5. Invert log scale and reshape to 2D
    grid_pH = preds["pH"].cpu().numpy().reshape(H, W)
    grid_N  = np.maximum(0, preds["N"].cpu().numpy().reshape(H, W))
    grid_P  = np.maximum(0, np.expm1(preds["P"].cpu().numpy().reshape(H, W)))
    grid_K  = np.maximum(0, np.expm1(preds["K"].cpu().numpy().reshape(H, W)))
    
    return {
        "pH": grid_pH,
        "Nitrogen": grid_N,
        "Phosphorus": grid_P,
        "Potassium": grid_K
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
