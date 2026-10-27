import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# -----------------------------------------------------------------------------
# 1. Dataset Definition
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


# -----------------------------------------------------------------------------
# 2. Architectures
# -----------------------------------------------------------------------------

# Configuration 1: Baseline Decoupled MLP (LeakyReLU, No Skips)
class BaselineDecoupledANN(nn.Module):
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        def build_head():
            return nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.LayerNorm(64),
                nn.LeakyReLU(0.1),
                nn.Dropout(dropout_rate),
                nn.Linear(64, 32),
                nn.LayerNorm(32),
                nn.LeakyReLU(0.1),
                nn.Dropout(dropout_rate / 2.0),
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


# Configuration 2: Decoupled MLP with Mish Activation (No Skips)
class MishDecoupledANN(nn.Module):
    def __init__(self, input_dim=128, dropout_rate=0.2):
        super().__init__()
        def build_head():
            return nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.LayerNorm(64),
                nn.Mish(),
                nn.Dropout(dropout_rate),
                nn.Linear(64, 32),
                nn.LayerNorm(32),
                nn.Mish(),
                nn.Dropout(dropout_rate / 2.0),
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


# Configuration 3: Decoupled MLP with Residual Skip Connections & Mish Activation
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


class ResidualMishDecoupledANN(nn.Module):
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
# 3. Training & Evaluation Pipeline
# -----------------------------------------------------------------------------
def train_and_eval_model(model_cls, X, y_dict, groups, model_name, epochs=20, lr=3e-3, batch_size=128):
    print(f"\n=======================================================")
    print(f">> Benchmarking: {model_name}")
    print(f"=======================================================")
    
    gkf = GroupKFold(n_splits=5)
    splits = list(gkf.split(X, y_dict["pH"], groups=groups))
    
    criterion = nn.SmoothL1Loss()
    device = torch.device("cpu")
    
    results = {
        "pH": [], "N": [],
        "P_raw": [], "P_log": [],
        "K_raw": [], "K_log": []
    }
    
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
        
        model = model_cls().to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
        
        # Outlier clipping thresholds from training set
        p_clip_val = np.percentile(train_y["P"], 99.5)
        k_clip_val = np.percentile(train_y["K"], 99.5)
        
        for epoch in range(epochs):
            model.train()
            for bx, by_pH, by_N, by_P_log, by_K_log in train_loader:
                preds = model(bx)
                loss = (
                    criterion(preds["pH"], by_pH) +
                    criterion(preds["N"], by_N) +
                    criterion(preds["P"], by_P_log) +
                    criterion(preds["K"], by_K_log)
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
                
                # pH & N (direct)
                pred_pH = val_preds["pH"].numpy()
                pred_N = val_preds["N"].numpy()
                true_pH = vy_pH.numpy()
                true_N = vy_N.numpy()
                
                # P & K (log scale & raw inverted + clipped)
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
                
                print(f"  Fold {fold}: pH={r2_pH:.3f} | N={r2_N:.3f} | P(raw)={r2_P_raw:.3f} [P-log: {r2_P_log:.3f}] | K(raw)={r2_K_raw:.3f} [K-log: {r2_K_log:.3f}]")

    elapsed = time.time() - t0
    print(f"[Time] Finished in {elapsed:.1f}s")
    
    summary = {k: np.mean(v) for k, v in results.items()}
    return summary


# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    data_path = "data/lucas_presto_soil_embeddings.csv"
    if not os.path.exists(data_path):
        data_path = "../data/lucas_presto_soil_embeddings.csv"
    
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape}")
    
    emb_cols = [f"emb_{i}" for i in range(128)]
    X = df[emb_cols].values
    groups = df["NUTS_2"].astype(str).values
    
    y_dict = {
        "pH": df["pH"].values,
        "N": df["N"].values,
        "P": df["P"].values,
        "K": df["K"].values
    }
    
    # 1. Baseline Decoupled MLP (LeakyReLU, No Residuals)
    res_baseline = train_and_eval_model(
        BaselineDecoupledANN, X, y_dict, groups,
        model_name="1. Baseline Decoupled MLP (LeakyReLU, No Residuals)"
    )
    
    # 2. Decoupled MLP with Mish Activation (No Residuals)
    res_mish = train_and_eval_model(
        MishDecoupledANN, X, y_dict, groups,
        model_name="2. Decoupled MLP with Mish Activation (No Residuals)"
    )
    
    # 3. Decoupled MLP with Residual Skip Connections & Mish Activation
    res_resmish = train_and_eval_model(
        ResidualMishDecoupledANN, X, y_dict, groups,
        model_name="3. Decoupled MLP with Residual Skip Connections & Mish"
    )
    
    # Print Grand Comparison Table
    print("\n" + "=" * 70)
    print("FINAL COMPARATIVE BENCHMARK: RESIDUAL SKIPS & MISH ACTIVATION")
    print("=" * 70)
    print(f"{'Target Metric':<20} | {'1. Baseline (LeakyReLU)':<24} | {'2. Mish Only':<15} | {'3. Residual + Mish':<18}")
    print("-" * 84)
    for metric in ["pH", "N", "P_raw", "P_log", "K_raw", "K_log"]:
        v1 = res_baseline[metric]
        v2 = res_mish[metric]
        v3 = res_resmish[metric]
        best = max(v1, v2, v3)
        fmt1 = f"{v1:.4f}{' [*]' if v1 == best else ''}"
        fmt2 = f"{v2:.4f}{' [*]' if v2 == best else ''}"
        fmt3 = f"{v3:.4f}{' [*]' if v3 == best else ''}"
        print(f"{metric:<20} | {fmt1:<24} | {fmt2:<15} | {fmt3:<18}")
    print("=" * 70)

