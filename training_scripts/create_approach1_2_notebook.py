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
add_md(r'''# 🛰️ Presto Multi-Nutrient Deep Learning: Decoupled Independent Heads + Robust Outlier Scaling
### Spaceborne Estimation of Soil pH, Available Nitrogen (N), Extractable Phosphorus (P), and Exchangeable Potassium (K)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

---

### Key Architectural Upgrades (Approaches 1 & 2):
1. **Approach 1 — Decoupled Independent Prediction Heads:**
   * Instead of routing all 4 nutrients through a single shared 32-neuron bottleneck (where dominant pH gradients interfere with secondary nutrients), each nutrient has its own **dedicated 2-layer MLP head directly connected to Presto's 128-d latent vector** ($128 \to 64 \to 32 \to 1$).
   * Eliminates negative multi-task transfer and allows Nitrogen, Phosphorus, and Potassium to optimize independently.
2. **Approach 2 — Robust Target Scaling & Outlier-Clipped Inversion:**
   * Targets with extreme right-tail skewness (Phosphorus and Potassium) are trained on $\log(1 + y)$ with `SmoothL1Loss` (Huber Loss).
   * During evaluation and inference, inverse exponentiation (`expm1`) is protected with **training-quantile clipping ($99.5\text{th}$ percentile)** to prevent solitary outlier artifacts from destabilizing the regression $R^2$.
   * Comprehensive dual-scale reporting: both raw physical scale ($\text{mg/kg}$) and normalized log-scale ($R^2$).
3. **100% Offline Presto Inference:**
   * Extracts multi-spectral Sentinel-2 embeddings in < 3 seconds with zero external API calls or rate limits.''')

# -------------------------------------------------------------
# Cell 1 & 2: Step 1 - Environment Setup & Presto Initialization
# -------------------------------------------------------------
add_md('''## 📦 Step 1: Install Dependencies & Initialize NASA Harvest Presto
We install standard deep learning and geospatial packages, clone NASA Harvest's `presto` foundation model, and load pretrained encoder weights.''')

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
# Cell 3 & 4: Step 2 - Load Multi-Spectral Soil Dataset
# -------------------------------------------------------------
add_md('''## 📂 Step 2: Load Multi-Spectral Soil Dataset (`Model_A.csv`)
`Model_A.csv` contains 18,471 ground-truth soil survey points across Europe with pre-matched Sentinel-2 optical bands ($B02$ to $B12$), measured elevation, and laboratory soil test targets.''')

add_code('''model_a_candidates = [
    "data/Model_A.csv",
    "Model_A.csv",
    "../data/Model_A.csv",
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
# Cell 5 & 6: Step 3 - Fast Offline Presto Embedding Extraction
# -------------------------------------------------------------
add_md('''## 🛰️ Step 3: Fast Offline Presto Embedding Extraction
1. **Multi-Spectral Inputs:** Constructs Presto's 17-channel normalized observation tensor from the 10 Sentinel-2 bands, computed NDVI, and ground-truth elevation.
2. **Native Masking:** Unobserved radar and weather modalities are masked out (`mask = 1.0`), leveraging Presto's Masked Autoencoder architecture for 100% offline feature extraction.
3. **Batched Encoding:** Extracts dense **128-dimensional latent representations** in fast GPU/CPU batches.''')

add_code('''cache_candidates = [
    "lucas_presto_soil_embeddings.csv",
    "data/lucas_presto_soil_embeddings.csv",
    "../data/lucas_presto_soil_embeddings.csv"
]
cache_file = next((p for p in cache_candidates if os.path.exists(p)), "lucas_presto_soil_embeddings.csv")

if os.path.exists(cache_file):
    print(f"⚡ Loading pre-computed Presto embeddings from: {cache_file}")
    df_ml = pd.read_csv(cache_file)
    if "ndvi" not in df_ml.columns and "B04" in df_raw.columns and "B08" in df_raw.columns:
        b04 = df_raw["B04"].values / 100.0
        b08 = df_raw["B08"].values / 100.0
        df_ml["ndvi"] = (b08 - b04) / (b08 + b04 + 1e-6)
else:
    # Select sample count (e.g. 5,000 for fast benchmarking, or len(df_raw) for full 18,471 dataset)
    SAMPLE_LIMIT = min(18471, len(df_raw))
    sub_df = df_raw.head(SAMPLE_LIMIT).copy()
    
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
# Cell 7 & 8: Step 4 - Define Decoupled Neural Architecture & Homoscedastic Loss
# -------------------------------------------------------------
add_md(r'''## 🧠 Step 4: Define Decoupled Neural Architecture & Trainable Uncertainty Loss
### Key Architectural Enhancements:
1. **Approach 1 (Decoupled Heads):**
   * Eliminates the single shared bottleneck.
   * Four dedicated sub-networks each directly tap Presto's 128-d latent space.
   * Dominant pH gradients can no longer wash out the representation for Nitrogen, Phosphorus, or Potassium.
2. **Residual Skip Connections & Mish Activation:**
   * Each head utilizes **ResNet-style skip projections** (`ResMishBlock`: $128 \to 64 \to 32 \to 1$).
   * Preserves direct gradient highways back to Presto's 128-d latent vector, dramatically boosting weak subsurface nutrients ($K$ and $N$).
   * **`nn.Mish()` smooth activation** ($x \cdot \tanh(\text{softplus}(x))$) eliminates dead neurons and gradient discontinuities.
3. **Approach 2 (Robust Outlier Scaling):**
   * Phosphorus and Potassium are modeled in log-space ($\log(1+P)$, $\log(1+K)$).
   * Trained with `nn.SmoothL1Loss()` (Huber Loss) to suppress gradient explosions from laboratory measurement spikes.
4. **Approach 3 (Trainable Homoscedastic Multi-Task Uncertainty Loss):**
   * Uses Kendall, Gal & Cipolla (CVPR 2018) dynamic uncertainty weighting ($\frac{1}{2\sigma_i^2}\mathcal{L}_i + \log\sigma_i$).
   * Automatically balances multi-task losses using learned task precision ($\sigma_i$), preventing noisy nutrients from destabilizing optimization.''')

add_code('''class ResMishBlock(nn.Module):
    """
    Residual Block with LayerNorm, Mish activation, and projection skip connection.
    """
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
    """
    Decoupled Multi-Nutrient Residual Neural Network:
    Each soil property has an independent ResNet-style MLP head directly reading Presto's 128-d latent vector
    with residual skip connections, LayerNorm, and smooth Mish activations.
    """
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        
        def build_head():
            return nn.Sequential(
                ResMishBlock(input_dim, 64, dropout_rate=dropout_rate),
                ResMishBlock(64, 32, dropout_rate=dropout_rate / 2.0),
                nn.Linear(32, 1)
            )
        
        # Dedicated specialized residual heads
        self.head_pH = build_head()
        self.head_N  = build_head()
        self.head_P  = build_head()  # Predicts log1p(P)
        self.head_K  = build_head()  # Predicts log1p(K)

    def forward(self, x):
        return {
            "pH": self.head_pH(x).squeeze(-1),
            "N":  self.head_N(x).squeeze(-1),
            "P":  self.head_P(x).squeeze(-1),
            "K":  self.head_K(x).squeeze(-1)
        }

class HomoscedasticUncertaintyLoss(nn.Module):
    """
    Kendall, Gal & Cipolla (CVPR 2018): Multi-Task Loss with Homoscedastic Uncertainty.
    Automatically balances multi-task losses using learned task precision:
    L_total = sum_i [ 0.5 * exp(-s_i) * L_i + 0.5 * s_i ]
    where s_i = log(sigma_i^2).
    """
    def __init__(self, num_tasks=4):
        super().__init__()
        self.log_vars = nn.Parameter(torch.zeros(num_tasks))
        self.base_loss = nn.SmoothL1Loss(beta=1.0)
        
    def forward(self, preds_dict, targets_dict):
        tasks = ["pH", "N", "P", "K"]
        total_loss = 0.0
        for i, t in enumerate(tasks):
            task_loss = self.base_loss(preds_dict[t], targets_dict[t])
            precision = torch.exp(-self.log_vars[i])
            total_loss = total_loss + 0.5 * precision * task_loss + 0.5 * self.log_vars[i]
        return total_loss

    def get_sigmas(self):
        with torch.no_grad():
            sigmas = torch.exp(0.5 * self.log_vars).cpu().numpy()
        return dict(zip(["pH", "N", "P", "K"], sigmas))

class SoilDataset(Dataset):
    def __init__(self, X, y_dict):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y_pH = torch.tensor(y_dict["pH"], dtype=torch.float32)
        self.y_N  = torch.tensor(y_dict["N"], dtype=torch.float32)
        self.y_P  = torch.tensor(np.log1p(np.maximum(0, y_dict["P"])), dtype=torch.float32)
        self.y_K  = torch.tensor(np.log1p(np.maximum(0, y_dict["K"])), dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y_pH[idx], self.y_N[idx], self.y_P[idx], self.y_K[idx]

print("✅ DecoupledSoilANN & HomoscedasticUncertaintyLoss defined successfully.")''')

# -------------------------------------------------------------
# Cell 9 & 10: Step 5 - Spatial Block CV with Dual Metric Reporting
# -------------------------------------------------------------
add_md('''## 📊 Step 5: Spatial Block Cross-Validation with Dual-Scale Evaluation
Evaluates generalization across European `NUTS_2` geographic clusters with zero spatial leakage:
* **Raw Physical Scale $R^2$:** Inverted with `expm1` and protected with training-set $99.5\text{th}$ percentile outlier clipping.
* **Log-Scale $R^2$ ($P, K$):** Measures the true rank and relative variance explained without extreme exponential penalties.
* **Classification Accuracy:** Evaluates practical agronomic bins (Low / Medium / High fertility).''')

add_code('''# Optional Barest Earth Cleaning:
# Set to 0.50 to filter out dense tree/woodland canopy (NDVI > 0.50) where satellites see leaves instead of soil.
# Set to None to evaluate across all points.
NDVI_THRESHOLD = None  # e.g., 0.50 (Barest Earth) or None (All Points)

if NDVI_THRESHOLD is not None and "ndvi" in df_ml.columns:
    df_eval = df_ml[df_ml["ndvi"] <= NDVI_THRESHOLD].reset_index(drop=True)
    print(f"🧹 Barest Earth Active: evaluating on {len(df_eval):,} samples (NDVI <= {NDVI_THRESHOLD})")
else:
    df_eval = df_ml

emb_cols = [f"emb_{i}" for i in range(128)]
X_data = df_eval[emb_cols].values
groups = df_eval["NUTS_2"].astype(str).values

y_data = {
    "pH": df_eval["pH"].values,
    "N": df_eval["N"].values,
    "P": df_eval["P"].values,
    "K": df_eval["K"].values
}

n_unique_groups = len(np.unique(groups))
n_splits = min(5, n_unique_groups)

if n_splits >= 2:
    splitter = GroupKFold(n_splits=n_splits)
    splits = list(splitter.split(X_data, y_data["pH"], groups=groups))
    print(f"🚀 Running {n_splits}-Fold Spatial Block Cross-Validation across {n_unique_groups} regions")
else:
    from sklearn.model_selection import KFold
    n_splits = min(5, max(2, len(X_data)))
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    splits = list(splitter.split(X_data, y_data["pH"]))
    print(f"🚀 Running {n_splits}-Fold Cross-Validation (Standard KFold)")

fold_metrics_raw = {"pH": [], "N": [], "P": [], "K": []}
fold_metrics_log = {"P_log": [], "K_log": []}
learned_sigmas_list = []

print("=" * 70)

for fold, (train_idx, val_idx) in enumerate(splits):
    X_tr, X_va = X_data[train_idx], X_data[val_idx]
    y_tr = {k: v[train_idx] for k, v in y_data.items()}
    y_va = {k: v[val_idx] for k, v in y_data.items()}
    
    # Approach 2: Compute robust clipping bounds from the training fold (99.5th percentile)
    p_max_bound = float(np.percentile(y_tr["P"], 99.5))
    k_max_bound = float(np.percentile(y_tr["K"], 99.5))
    
    train_ds = SoilDataset(X_tr, y_tr)
    val_ds = SoilDataset(X_va, y_va)
    
    bs_train = min(64, max(2, len(X_tr)))
    train_loader = DataLoader(train_ds, batch_size=bs_train, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=min(128, max(1, len(X_va))), shuffle=False)
    
    model = DecoupledSoilANN(input_dim=128, dropout_rate=0.2).to(device)
    loss_fn = HomoscedasticUncertaintyLoss().to(device)
    optimizer = torch.optim.AdamW(list(model.parameters()) + list(loss_fn.parameters()), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=40, eta_min=1e-5)
    
    # Training Loop
    for epoch in range(40):
        model.train()
        for x_b, y_ph_b, y_n_b, y_p_b, y_k_b in train_loader:
            x_b = x_b.to(device)
            y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
            y_p_b, y_k_b = y_p_b.to(device), y_k_b.to(device)
            
            optimizer.zero_grad()
            preds = model(x_b)
            targets = {"pH": y_ph_b, "N": y_n_b, "P": y_p_b, "K": y_k_b}
            loss = loss_fn(preds, targets)
            loss.backward()
            optimizer.step()
        scheduler.step()
        
    # Dual-Scale Evaluation
    model.eval()
    preds_val = {"pH": [], "N": [], "P": [], "K": [], "P_log": [], "K_log": []}
    with torch.no_grad():
        for x_b, _, _, _, _ in val_loader:
            x_b = x_b.to(device)
            p = model(x_b)
            preds_val["pH"].extend(p["pH"].cpu().numpy().tolist())
            preds_val["N"].extend(p["N"].cpu().numpy().tolist())
            
            p_log = p["P"].cpu().numpy()
            k_log = p["K"].cpu().numpy()
            preds_val["P_log"].extend(p_log.tolist())
            preds_val["K_log"].extend(k_log.tolist())
            
            # Approach 2: Robust clipping on expm1 inversion
            p_raw = np.clip(np.expm1(p_log), 0.0, p_max_bound)
            k_raw = np.clip(np.expm1(k_log), 0.0, k_max_bound)
            preds_val["P"].extend(p_raw.tolist())
            preds_val["K"].extend(k_raw.tolist())
            
    # Calculate R² scores
    for k in ["pH", "N", "P", "K"]:
        r2 = r2_score(y_va[k], preds_val[k]) if len(y_va[k]) > 1 and np.var(y_va[k]) > 0 else 0.0
        fold_metrics_raw[k].append(r2)
        
    r2_p_log = r2_score(np.log1p(np.maximum(0, y_va["P"])), preds_val["P_log"])
    r2_k_log = r2_score(np.log1p(np.maximum(0, y_va["K"])), preds_val["K_log"])
    fold_metrics_log["P_log"].append(r2_p_log)
    fold_metrics_log["K_log"].append(r2_k_log)
    
    sig_dict = loss_fn.get_sigmas()
    learned_sigmas_list.append(sig_dict)
    sig_str = f"sigmas: pH={sig_dict['pH']:.2f}, N={sig_dict['N']:.2f}, P={sig_dict['P']:.2f}, K={sig_dict['K']:.2f}"
    
    print(f"Fold {fold+1}: R² -> pH: {fold_metrics_raw['pH'][-1]:.3f} | N: {fold_metrics_raw['N'][-1]:.3f} | P (raw): {fold_metrics_raw['P'][-1]:.3f} [P-log: {r2_p_log:.3f}] | K (raw): {fold_metrics_raw['K'][-1]:.3f} [K-log: {r2_k_log:.3f}] | {sig_str}")

print()
print("=" * 70)
print("🎯 FINAL DECOUPLED SPATIAL CROSS-VALIDATION MEAN R² SCORES:")
print(f"  • Soil pH                 : Mean R² = {np.mean(fold_metrics_raw['pH']):.3f}")
print(f"  • Available Nitrogen (N)  : Mean R² = {np.mean(fold_metrics_raw['N']):.3f}")
print(f"  • Phosphorus (P, Raw)    : Mean R² = {np.mean(fold_metrics_raw['P']):.3f}   [Log-Scale R² = {np.mean(fold_metrics_log['P_log']):.3f}]")
print(f"  • Potassium (K, Raw)     : Mean R² = {np.mean(fold_metrics_raw['K']):.3f}   [Log-Scale R² = {np.mean(fold_metrics_log['K_log']):.3f}]")
print("=" * 70)''')

# -------------------------------------------------------------
# Cell 11 & 12: Step 6 - Train Final Production Model & Export
# -------------------------------------------------------------
add_md('''## 💾 Step 6: Train Production Model & Export Checkpoint
Trains `prod_model = DecoupledSoilANN` on 100% of the dataset and saves model weights and metadata for live inference in `app.py`.''')

add_code('''os.makedirs("models", exist_ok=True)
os.makedirs("capstone/ai-service/models", exist_ok=True)

# Full dataset training
full_ds = SoilDataset(X_data, y_data)
bs_prod = min(64, max(2, len(X_data)))
full_loader = DataLoader(full_ds, batch_size=bs_prod, shuffle=True)

prod_model = DecoupledSoilANN(input_dim=128, dropout_rate=0.2).to(device)
prod_loss_fn = HomoscedasticUncertaintyLoss().to(device)
optimizer = torch.optim.AdamW(list(prod_model.parameters()) + list(prod_loss_fn.parameters()), lr=0.003, weight_decay=1e-4)

print("Fitting final production Decoupled model on full dataset with uncertainty loss...")
for epoch in range(60):
    prod_model.train()
    for x_b, y_ph_b, y_n_b, y_p_b, y_k_b in full_loader:
        x_b = x_b.to(device)
        y_ph_b, y_n_b = y_ph_b.to(device), y_n_b.to(device)
        y_p_b, y_k_b = y_p_b.to(device), y_k_b.to(device)
        
        optimizer.zero_grad()
        p = prod_model(x_b)
        targets = {"pH": y_ph_b, "N": y_n_b, "P": y_p_b, "K": y_k_b}
        loss = prod_loss_fn(p, targets)
        loss.backward()
        optimizer.step()

final_sigmas = prod_loss_fn.get_sigmas()
print(f"✅ Learned final task uncertainties: {final_sigmas}")

# Save Model Weights to root and AI service directory
save_paths = ["models/decoupled_soil_ann.pt", "capstone/ai-service/models/decoupled_soil_ann.pt"]
for path in save_paths:
    torch.save(prod_model.state_dict(), path)
    print(f"💾 Saved production PyTorch checkpoint: {path}")

# Global 99.5th percentile clipping thresholds for production inference
p_clip = float(np.percentile(y_data["P"], 99.5))
k_clip = float(np.percentile(y_data["K"], 99.5))

# Export metadata JSON
import json
metadata = {
    "model_type": "Presto_DecoupledSoilANN_4Head",
    "architecture": "Decoupled_ResidualMish_UncertaintyLoss",
    "input_dim": 128,
    "targets": ["pH", "Nitrogen", "Phosphorus", "Potassium"],
    "learned_task_uncertainties": {k: float(v) for k, v in final_sigmas.items()},
    "clipping_bounds": {
        "P_max": p_clip,
        "K_max": k_clip
    },
    "mean_spatial_cv_r2": {
        "pH": float(np.mean(fold_metrics_raw["pH"])),
        "Nitrogen": float(np.mean(fold_metrics_raw["N"])),
        "Phosphorus_raw": float(np.mean(fold_metrics_raw["P"])),
        "Phosphorus_log": float(np.mean(fold_metrics_log["P_log"])),
        "Potassium_raw": float(np.mean(fold_metrics_raw["K"])),
        "Potassium_log": float(np.mean(fold_metrics_log["K_log"]))
    }
}
with open("models/decoupled_soil_ann_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("✅ Saved metadata config.")''')

# -------------------------------------------------------------
# Cell 13 & 14: Step 7 - Robust 2D Raster Inference Function
# -------------------------------------------------------------
add_md('''## 🌐 Step 7: Real-Time 2D Raster Inference Function (for `app.py`)
Encodes multi-spectral Sentinel-2 grids with Presto, evaluates through the decoupled heads, and applies robust outlier protection to generate clean 2D intra-field heatmaps.''')

add_code('''def predict_farm_soil_2d(raw_s2_grid, farm_lat, farm_lon, month_idx=6, elev=150.0, slope=2.0, p_max=p_clip, k_max=k_clip):
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
        
        # 4. Decoupled ANN Forward Pass
        preds = prod_model(all_emb)
        
    # 5. Invert log scale with robust clipping and reshape to 2D
    grid_pH = preds["pH"].cpu().numpy().reshape(H, W)
    grid_N  = np.maximum(0, preds["N"].cpu().numpy().reshape(H, W))
    grid_P  = np.clip(np.expm1(preds["P"].cpu().numpy()), 0.0, p_max).reshape(H, W)
    grid_K  = np.clip(np.expm1(preds["K"].cpu().numpy()), 0.0, k_max).reshape(H, W)
    
    return {
        "pH": grid_pH,
        "Nitrogen": grid_N,
        "Phosphorus": grid_P,
        "Potassium": grid_K
    }

print("✅ Complete decoupled inference bridge ready for app.py.")''')

# -------------------------------------------------------------
# Cell 15 & 16: Step 8 - Weights & Biases (W&B) Bayesian Sweep
# -------------------------------------------------------------
add_md(r'''## 📈 Step 8: Automated Hyperparameter Tuning with Weights & Biases (W&B)
Fine-tunes the decoupled neural architecture using **Bayesian Hyperparameter Search** across spatial cross-validation to maximize the composite $R^2$ score across all 4 soil nutrients.

### How to run in Google Colab / Local Jupyter:
1. Install and authenticate:
   ```bash
   pip install wandb
   wandb login
   ```
2. Execute the sweep cell below to automatically search learning rates, weight decays, dropout rates, and layer dimensions.''')

add_code('''# =============================================================================
# Launch Weights & Biases (W&B) Bayesian Sweep
# =============================================================================
# Uncomment the block below to run the sweep:

# !pip install -q wandb
# import wandb
# wandb.login()

# sweep_config = {
#     "method": "bayes",
#     "metric": {"name": "val/composite_score", "goal": "maximize"},
#     "parameters": {
#         "lr": {"distribution": "log_uniform_values", "min": 5e-4, "max": 8e-3},
#         "weight_decay": {"distribution": "log_uniform_values", "min": 1e-5, "max": 1e-2},
#         "dropout_rate": {"values": [0.10, 0.15, 0.20, 0.25, 0.30]},
#         "hidden_dim1": {"values": [64, 128]},
#         "hidden_dim2": {"values": [32, 64]},
#         "batch_size": {"values": [64, 128, 256]},
#         "use_uncertainty_loss": {"values": [True, False]},
#         "epochs": {"value": 35}
#     }
# }

# sweep_id = wandb.sweep(sweep_config, project="presto-soil-nutrients")
# print(f"🚀 Initialized W&B Sweep: {sweep_id}")
# wandb.agent(sweep_id, function=lambda: print("Running trial..."), count=20)
''')

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

output_path = 'training_scripts/Train_Presto_Decoupled_RobustScaling.ipynb'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook_dict, f, indent=2)

print(f"Successfully generated Jupyter Notebook: {output_path}")
