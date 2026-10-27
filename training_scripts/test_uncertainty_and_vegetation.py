import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

# -----------------------------------------------------------------------------
# 1. Dataset & Model Definitions
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# 2. Trainable Homoscedastic Multi-Task Uncertainty Loss
# -----------------------------------------------------------------------------
class HomoscedasticUncertaintyLoss(nn.Module):
    """
    Kendall, Gal & Cipolla (CVPR 2018): Multi-Task Loss with Homoscedastic Uncertainty.
    L_total = sum_i [ 0.5 * exp(-s_i) * L_i + 0.5 * s_i ]
    where s_i = log(sigma_i^2).
    """
    def __init__(self, num_tasks=4):
        super().__init__()
        # Initialized to s_i = 0.0 (sigma_i = 1.0)
        self.log_vars = nn.Parameter(torch.zeros(num_tasks))
        self.base_loss = nn.SmoothL1Loss()
        
    def forward(self, preds_dict, targets_dict):
        tasks = ["pH", "N", "P", "K"]
        total_loss = 0.0
        for i, t in enumerate(tasks):
            task_loss = self.base_loss(preds_dict[t], targets_dict[t])
            precision = torch.exp(-self.log_vars[i])
            # 0.5 * exp(-s) * loss + 0.5 * s
            total_loss += 0.5 * precision * task_loss + 0.5 * self.log_vars[i]
        return total_loss

    def get_sigmas(self):
        # sigma_i = exp(s_i / 2)
        with torch.no_grad():
            sigmas = torch.exp(0.5 * self.log_vars).cpu().numpy()
        return dict(zip(["pH", "N", "P", "K"], sigmas))


# -----------------------------------------------------------------------------
# 3. Cross-Validation Trainer
# -----------------------------------------------------------------------------
def run_spatial_cv(X, y_dict, groups, use_uncertainty_loss=True, epochs=20, lr=3e-3, batch_size=128, experiment_name=""):
    print(f"\n=======================================================")
    print(f">> Running: {experiment_name} (N = {len(X)} samples)")
    print(f">> Loss: {'Homoscedastic Uncertainty Loss' if use_uncertainty_loss else 'Fixed Equal Huber Loss'}")
    print(f"=======================================================")
    
    gkf = GroupKFold(n_splits=5)
    splits = list(gkf.split(X, y_dict["pH"], groups=groups))
    
    criterion_fixed = nn.SmoothL1Loss()
    device = torch.device("cpu")
    
    results = {
        "pH": [], "N": [],
        "P_raw": [], "P_log": [],
        "K_raw": [], "K_log": []
    }
    learned_sigmas = []
    
    t0 = time.time()
    for fold, (train_idx, val_idx) in enumerate(splits, 1):
        torch.manual_seed(42 + fold)
        np.random.seed(42 + fold)
        
        train_y = {k: v[train_idx] for k, v in y_dict.items()}
        val_y = {k: v[val_idx] for k, v in y_dict.items()}
        
        train_dataset = SoilDataset(X[train_idx], train_y)
        val_dataset = SoilDataset(X[val_idx], val_y)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=len(val_dataset), shuffle=False)
        
        model = DecoupledSoilANN().to(device)
        
        if use_uncertainty_loss:
            loss_fn = HomoscedasticUncertaintyLoss().to(device)
            optimizer = torch.optim.AdamW(list(model.parameters()) + list(loss_fn.parameters()), lr=lr, weight_decay=1e-4)
        else:
            loss_fn = criterion_fixed
            optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
            
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
        
        p_clip_val = np.percentile(train_y["P"], 99.5)
        k_clip_val = np.percentile(train_y["K"], 99.5)
        
        for epoch in range(epochs):
            model.train()
            for bx, by_pH, by_N, by_P_log, by_K_log in train_loader:
                preds = model(bx)
                if use_uncertainty_loss:
                    target_dict = {"pH": by_pH, "N": by_N, "P": by_P_log, "K": by_K_log}
                    loss = loss_fn(preds, target_dict)
                else:
                    loss = (
                        loss_fn(preds["pH"], by_pH) +
                        loss_fn(preds["N"], by_N) +
                        loss_fn(preds["P"], by_P_log) +
                        loss_fn(preds["K"], by_K_log)
                    )
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            scheduler.step()
            
        # Validation
        model.eval()
        with torch.no_grad():
            for vx, vy_pH, vy_N, vy_P_log, vy_K_log in val_loader:
                val_preds = model(vx)
                
                pred_pH = val_preds["pH"].numpy()
                pred_N = val_preds["N"].numpy()
                true_pH = vy_pH.numpy()
                true_N = vy_N.numpy()
                
                pred_P_log = val_preds["P"].numpy()
                pred_K_log = val_preds["K"].numpy()
                true_P_log = vy_P_log.numpy()
                true_K_log = vy_K_log.numpy()
                
                pred_P_raw = np.clip(np.expm1(pred_P_log), 0, p_clip_val)
                pred_K_raw = np.clip(np.expm1(pred_K_log), 0, k_clip_val)
                true_P_raw = val_y["P"]
                true_K_raw = val_y["K"]
                
                r2_pH = r2_score(true_pH, pred_pH)
                r2_N = r2_score(true_N, pred_N)
                r2_P_log = r2_score(true_P_log, pred_P_log)
                r2_K_log = r2_score(true_K_log, pred_K_log)
                r2_P_raw = r2_score(true_P_raw, pred_P_raw)
                r2_K_raw = r2_score(true_K_raw, pred_K_raw)
                
                results["pH"].append(r2_pH)
                results["N"].append(r2_N)
                results["P_log"].append(r2_P_log)
                results["K_log"].append(r2_K_log)
                results["P_raw"].append(r2_P_raw)
                results["K_raw"].append(r2_K_raw)
                
        if use_uncertainty_loss:
            sig_dict = loss_fn.get_sigmas()
            learned_sigmas.append(sig_dict)
            sig_str = f"sigma: [pH={sig_dict['pH']:.2f}, N={sig_dict['N']:.2f}, P={sig_dict['P']:.2f}, K={sig_dict['K']:.2f}]"
        else:
            sig_str = ""
            
        print(f"  Fold {fold}: pH={r2_pH:.3f} | N={r2_N:.3f} | P(raw)={r2_P_raw:.3f} [log: {r2_P_log:.3f}] | K(raw)={r2_K_raw:.3f} [log: {r2_K_log:.3f}] | {sig_str}")

    elapsed = time.time() - t0
    print(f"[Time] Completed in {elapsed:.1f}s")
    
    summary = {k: np.mean(v) for k, v in results.items()}
    summary["sigmas"] = learned_sigmas
    return summary


# -----------------------------------------------------------------------------
# Main Execution Pipeline
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    emb_path = "data/lucas_presto_soil_embeddings.csv"
    raw_path = "data/Model_A.csv"
    
    print("Loading datasets...")
    df_emb = pd.read_csv(emb_path)
    df_raw = pd.read_csv(raw_path)
    print(f"Loaded {len(df_emb)} points.")
    
    # Compute NDVI from raw Sentinel-2 bands
    b04 = df_raw["B04"].values / 100.0
    b08 = df_raw["B08"].values / 100.0
    ndvi = (b08 - b04) / (b08 + b04 + 1e-6)
    df_emb["ndvi"] = ndvi
    df_emb["LC0_Desc"] = df_raw["LC0_Desc"].values
    
    emb_cols = [f"emb_{i}" for i in range(128)]
    
    # Helper to slice dataset
    def get_arrays(df_sub):
        X = df_sub[emb_cols].values
        groups = df_sub["NUTS_2"].astype(str).values
        y_dict = {
            "pH": df_sub["pH"].values,
            "N": df_sub["N"].values,
            "P": df_sub["P"].values,
            "K": df_sub["K"].values
        }
        return X, y_dict, groups

    # =========================================================================
    # PART 1: Uncertainty Loss Ablation (All 18,471 Points)
    # =========================================================================
    X_all, y_all, groups_all = get_arrays(df_emb)
    
    # 1. Fixed Equal Loss (Baseline ResMish)
    res_fixed = run_spatial_cv(
        X_all, y_all, groups_all,
        use_uncertainty_loss=False,
        experiment_name="1. ResMish + Fixed Equal Huber Loss (All 18,471 Points)"
    )
    
    # 2. Homoscedastic Uncertainty Loss
    res_uncertainty = run_spatial_cv(
        X_all, y_all, groups_all,
        use_uncertainty_loss=True,
        experiment_name="2. ResMish + Trainable Homoscedastic Uncertainty Loss (All 18,471 Points)"
    )

    # =========================================================================
    # PART 2: Dense Vegetation Filtering (Barest Earth Cleaning)
    # =========================================================================
    # 3. Moderate Vegetation Filter: NDVI <= 0.50 (Excludes dense forest canopy)
    df_ndvi50 = df_emb[df_emb["ndvi"] <= 0.50].reset_index(drop=True)
    X_50, y_50, groups_50 = get_arrays(df_ndvi50)
    res_barest50 = run_spatial_cv(
        X_50, y_50, groups_50,
        use_uncertainty_loss=True,
        experiment_name="3. Barest Earth Cleaned (NDVI <= 0.50, Moderate Filter)"
    )
    
    # 4. Strict Barest Earth: NDVI <= 0.40 (True bare and sparse soils)
    df_ndvi40 = df_emb[df_emb["ndvi"] <= 0.40].reset_index(drop=True)
    X_40, y_40, groups_40 = get_arrays(df_ndvi40)
    res_barest40 = run_spatial_cv(
        X_40, y_40, groups_40,
        use_uncertainty_loss=True,
        experiment_name="4. Strict Barest Earth (NDVI <= 0.40, Highly Exposed Soil)"
    )
    
    # 5. Cropland & Bareland Only (Agricultural Soil Target Domain)
    df_agri = df_emb[df_emb["LC0_Desc"].isin(["Cropland", "Bareland"])].reset_index(drop=True)
    X_agri, y_agri, groups_agri = get_arrays(df_agri)
    res_agri = run_spatial_cv(
        X_agri, y_agri, groups_agri,
        use_uncertainty_loss=True,
        experiment_name="5. Agricultural Soils (Cropland & Bareland Only)"
    )

    # =========================================================================
    # Print Grand Comparison Tables
    # =========================================================================
    print("\n" + "=" * 80)
    print("TABLE 1: HOMOSCEDASTIC UNCERTAINTY LOSS ABLATION (ALL 18,471 POINTS)")
    print("=" * 80)
    print(f"{'Target Metric':<18} | {'1. Fixed Equal Loss':<22} | {'2. Trainable Uncertainty Loss':<30} | {'Delta':<10}")
    print("-" * 86)
    for m in ["pH", "N", "P_raw", "P_log", "K_raw", "K_log"]:
        v1 = res_fixed[m]
        v2 = res_uncertainty[m]
        delta = v2 - v1
        print(f"{m:<18} | {v1:.4f}{'':<16} | {v2:.4f}{'':<24} | {delta:+.4f}")
    print("=" * 80)
    
    # Print learned sigmas
    if len(res_uncertainty["sigmas"]) > 0:
        mean_sigmas = {k: np.mean([s[k] for s in res_uncertainty["sigmas"]]) for k in ["pH", "N", "P", "K"]}
        print(">> Learned Homoscedastic Uncertainty (mean sigma_i):")
        for k, v in mean_sigmas.items():
            print(f"   * Task {k:<3}: sigma = {v:.3f} (precision weight = {1.0/(2*v**2):.3f})")

    print("\n" + "=" * 90)
    print("TABLE 2: DENSE VEGETATION FILTERING (BAREST EARTH CLEANING)")
    print("=" * 90)
    print(f"{'Target Metric':<15} | {'All (N=18.4k)':<15} | {'NDVI<=0.50 (N=13.7k)':<20} | {'NDVI<=0.40 (N=10.1k)':<20} | {'Cropland (N=7.8k)':<18}")
    print("-" * 90)
    for m in ["pH", "N", "P_raw", "P_log", "K_raw", "K_log"]:
        v_all = res_uncertainty[m]
        v_50 = res_barest50[m]
        v_40 = res_barest40[m]
        v_ag = res_agri[m]
        print(f"{m:<15} | {v_all:<15.4f} | {v_50:<20.4f} | {v_40:<20.4f} | {v_ag:<18.4f}")
    print("=" * 90)
