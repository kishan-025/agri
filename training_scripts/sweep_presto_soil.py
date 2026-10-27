"""
🛰️ Presto Multi-Nutrient Deep Learning — Weights & Biases (W&B) Sweep Script
=============================================================================
This script performs automated Bayesian hyperparameter tuning across the decoupled 
multi-nutrient neural network (pH, Nitrogen, Phosphorus, Potassium) on European LUCAS 
spatial clusters.

Search Space:
  - Learning Rate (lr): log-uniform between 5e-4 and 8e-3
  - Weight Decay: log-uniform between 1e-5 and 1e-2
  - Dropout Rate: [0.10, 0.15, 0.20, 0.25, 0.30]
  - Hidden Layer Sizes: [64 -> 32], [128 -> 64], [128 -> 32]
  - Batch Size: [64, 128, 256]
  - Loss Formulation: Homoscedastic Uncertainty Loss vs. Huber Loss
  - Objective: Maximize composite multi-task spatial R² (val/composite_score)

Usage:
  1. Install wandb:
     pip install wandb

  2. Authenticate:
     wandb login

  3. Launch Bayesian Sweep (e.g., 20 automated trials):
     python training_scripts/sweep_presto_soil.py --mode sweep --count 20

  4. Run a single test run without sweep:
     python training_scripts/sweep_presto_soil.py --mode single

  5. Join an existing sweep agent on multiple GPUs/machines:
     python training_scripts/sweep_presto_soil.py --mode agent --sweep_id <SWEEP_ID>
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import time
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score

# Check W&B installation
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


# -----------------------------------------------------------------------------
# 1. Dataset & Architectural Definitions
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
    Each soil property has an independent ResNet-style MLP head directly reading Presto's 128-d latent vector.
    """
    def __init__(self, input_dim=128, hidden_dim1=64, hidden_dim2=32, dropout_rate=0.2):
        super().__init__()
        
        def build_head():
            return nn.Sequential(
                ResMishBlock(input_dim, hidden_dim1, dropout_rate=dropout_rate),
                ResMishBlock(hidden_dim1, hidden_dim2, dropout_rate=dropout_rate / 2.0),
                nn.Linear(hidden_dim2, 1)
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


class HomoscedasticUncertaintyLoss(nn.Module):
    """
    Kendall, Gal & Cipolla (CVPR 2018): Multi-Task Loss with Homoscedastic Uncertainty.
    L_total = sum_i [ 0.5 * exp(-s_i) * L_i + 0.5 * s_i ] where s_i = log(sigma_i^2).
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


# -----------------------------------------------------------------------------
# 2. Data Loading Utility
# -----------------------------------------------------------------------------
def load_lucas_embeddings():
    candidates = [
        "data/lucas_presto_soil_embeddings.csv",
        "lucas_presto_soil_embeddings.csv",
        "../data/lucas_presto_soil_embeddings.csv"
    ]
    path = next((c for c in candidates if os.path.exists(c)), None)
    if path is None:
        raise FileNotFoundError("Could not find lucas_presto_soil_embeddings.csv in data/ or root directory.")
    
    print(f"Loading cached embeddings from: {path}")
    df = pd.read_csv(path)
    
    emb_cols = [f"emb_{i}" for i in range(128)]
    X = df[emb_cols].values
    groups = df["NUTS_2"].astype(str).values
    y_dict = {
        "pH": df["pH"].values,
        "N": df["N"].values,
        "P": df["P"].values,
        "K": df["K"].values
    }
    return X, y_dict, groups


# -----------------------------------------------------------------------------
# 3. Core Training and Evaluation Pipeline (W&B Integrated)
# -----------------------------------------------------------------------------
def train_sweep_run(config=None, cv_folds=3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Initialize W&B run if available
    run = None
    if WANDB_AVAILABLE:
        run = wandb.init(config=config)
        cfg = wandb.config
    else:
        # Fallback to default dictionary if wandb is not present
        class DummyConfig:
            def __init__(self, d):
                self.__dict__.update(d)
            def get(self, k, default=None):
                return getattr(self, k, default)
        cfg = DummyConfig(config or {
            "lr": 0.003,
            "weight_decay": 1e-4,
            "dropout_rate": 0.20,
            "hidden_dim1": 64,
            "hidden_dim2": 32,
            "batch_size": 128,
            "use_uncertainty_loss": True,
            "epochs": 35
        })

    print(f"\n>> Hyperparameters: lr={cfg.lr:.6f}, wd={cfg.weight_decay:.6f}, drop={cfg.dropout_rate:.2f}, "
          f"dims=[128->{cfg.hidden_dim1}->{cfg.hidden_dim2}->1], bs={cfg.batch_size}, "
          f"uncertainty_loss={cfg.use_uncertainty_loss}, epochs={cfg.epochs}")

    X, y_dict, groups = load_lucas_embeddings()
    
    gkf = GroupKFold(n_splits=cv_folds)
    splits = list(gkf.split(X, y_dict["pH"], groups=groups))
    
    fold_results = {
        "pH": [], "N": [],
        "P_raw": [], "P_log": [],
        "K_raw": [], "K_log": [],
        "composite": []
    }
    
    t0 = time.time()
    for fold, (train_idx, val_idx) in enumerate(splits, 1):
        torch.manual_seed(42 + fold)
        np.random.seed(42 + fold)
        
        train_y = {k: v[train_idx] for k, v in y_dict.items()}
        val_y = {k: v[val_idx] for k, v in y_dict.items()}
        
        p_clip_val = float(np.percentile(train_y["P"], 99.5))
        k_clip_val = float(np.percentile(train_y["K"], 99.5))
        
        train_ds = SoilDataset(X[train_idx], train_y)
        val_ds = SoilDataset(X[val_idx], val_y)
        
        train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=min(256, len(val_ds)), shuffle=False)
        
        model = DecoupledSoilANN(
            input_dim=128,
            hidden_dim1=cfg.hidden_dim1,
            hidden_dim2=cfg.hidden_dim2,
            dropout_rate=cfg.dropout_rate
        ).to(device)
        
        if cfg.use_uncertainty_loss:
            loss_fn = HomoscedasticUncertaintyLoss().to(device)
            params = list(model.parameters()) + list(loss_fn.parameters())
        else:
            loss_fn = nn.SmoothL1Loss(beta=1.0).to(device)
            params = model.parameters()
            
        optimizer = torch.optim.AdamW(params, lr=cfg.lr, weight_decay=cfg.weight_decay)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs, eta_min=1e-5)
        
        for epoch in range(1, cfg.epochs + 1):
            model.train()
            total_train_loss = 0.0
            num_batches = 0
            
            for bx, by_pH, by_N, by_P_log, by_K_log in train_loader:
                bx = bx.to(device)
                by_pH, by_N = by_pH.to(device), by_N.to(device)
                by_P_log, by_K_log = by_P_log.to(device), by_K_log.to(device)
                
                optimizer.zero_grad()
                preds = model(bx)
                
                if cfg.use_uncertainty_loss:
                    target_dict = {"pH": by_pH, "N": by_N, "P": by_P_log, "K": by_K_log}
                    loss = loss_fn(preds, target_dict)
                else:
                    loss = (
                        1.0 * loss_fn(preds["pH"], by_pH) +
                        1.0 * loss_fn(preds["N"], by_N) +
                        1.2 * loss_fn(preds["P"], by_P_log) +
                        1.2 * loss_fn(preds["K"], by_K_log)
                    )
                    
                loss.backward()
                optimizer.step()
                total_train_loss += loss.item()
                num_batches += 1
                
            scheduler.step()
            
        # Fold Validation Evaluation
        model.eval()
        preds_val = {"pH": [], "N": [], "P_log": [], "K_log": []}
        with torch.no_grad():
            for vx, _, _, _, _ in val_loader:
                vx = vx.to(device)
                p = model(vx)
                preds_val["pH"].extend(p["pH"].cpu().numpy().tolist())
                preds_val["N"].extend(p["N"].cpu().numpy().tolist())
                preds_val["P_log"].extend(p["P"].cpu().numpy().tolist())
                preds_val["K_log"].extend(p["K"].cpu().numpy().tolist())
                
        # Invert clipped P and K
        pred_p_raw = np.clip(np.expm1(preds_val["P_log"]), 0.0, p_clip_val)
        pred_k_raw = np.clip(np.expm1(preds_val["K_log"]), 0.0, k_clip_val)
        
        r2_pH = r2_score(val_y["pH"], preds_val["pH"])
        r2_N = r2_score(val_y["N"], preds_val["N"])
        r2_P_log = r2_score(np.log1p(np.maximum(0, val_y["P"])), preds_val["P_log"])
        r2_K_log = r2_score(np.log1p(np.maximum(0, val_y["K"])), preds_val["K_log"])
        r2_P_raw = r2_score(val_y["P"], pred_p_raw)
        r2_K_raw = r2_score(val_y["K"], pred_k_raw)
        
        # Weighted composite score to balance all 4 tasks
        fold_composite = r2_pH + 2.0 * r2_N + 1.5 * r2_P_log + 1.5 * r2_K_log
        
        fold_results["pH"].append(r2_pH)
        fold_results["N"].append(r2_N)
        fold_results["P_log"].append(r2_P_log)
        fold_results["K_log"].append(r2_K_log)
        fold_results["P_raw"].append(r2_P_raw)
        fold_results["K_raw"].append(r2_K_raw)
        fold_results["composite"].append(fold_composite)

    elapsed = time.time() - t0
    
    # Calculate Mean CV Scores
    mean_pH = float(np.mean(fold_results["pH"]))
    mean_N = float(np.mean(fold_results["N"]))
    mean_P_log = float(np.mean(fold_results["P_log"]))
    mean_K_log = float(np.mean(fold_results["K_log"]))
    mean_P_raw = float(np.mean(fold_results["P_raw"]))
    mean_K_raw = float(np.mean(fold_results["K_raw"]))
    mean_composite = float(np.mean(fold_results["composite"]))
    mean_raw = float(np.mean([mean_pH, mean_N, mean_P_raw, mean_K_raw]))

    print(f"⏱️ Finished in {elapsed:.1f}s | Mean R²: pH={mean_pH:.3f}, N={mean_N:.3f}, "
          f"P(raw)={mean_P_raw:.3f} [P-log: {mean_P_log:.3f}], K(raw)={mean_K_raw:.3f} [K-log: {mean_K_log:.3f}] "
          f"| Composite={mean_composite:.3f}")

    # Log metrics to W&B
    if WANDB_AVAILABLE and run is not None:
        metrics = {
            "val/r2_pH": mean_pH,
            "val/r2_N": mean_N,
            "val/r2_P_log": mean_P_log,
            "val/r2_K_log": mean_K_log,
            "val/r2_P_raw": mean_P_raw,
            "val/r2_K_raw": mean_K_raw,
            "val/composite_score": mean_composite,
            "val/mean_raw_r2": mean_raw,
            "train/elapsed_seconds": elapsed
        }
        
        if cfg.use_uncertainty_loss:
            sigmas = loss_fn.get_sigmas()
            metrics.update({
                "sigmas/pH": float(sigmas["pH"]),
                "sigmas/N": float(sigmas["N"]),
                "sigmas/P": float(sigmas["P"]),
                "sigmas/K": float(sigmas["K"]),
            })
            
        wandb.log(metrics)
        run.finish()

    return mean_composite


# -----------------------------------------------------------------------------
# 4. Sweep Configuration & Execution Entrypoint
# -----------------------------------------------------------------------------
SWEEP_CONFIG = {
    "method": "bayes",
    "metric": {
        "name": "val/composite_score",
        "goal": "maximize"
    },
    "parameters": {
        "lr": {
            "distribution": "log_uniform_values",
            "min": 5e-4,
            "max": 8e-3
        },
        "weight_decay": {
            "distribution": "log_uniform_values",
            "min": 1e-5,
            "max": 1e-2
        },
        "dropout_rate": {
            "values": [0.10, 0.15, 0.20, 0.25, 0.30]
        },
        "hidden_dim1": {
            "values": [64, 128]
        },
        "hidden_dim2": {
            "values": [32, 64]
        },
        "batch_size": {
            "values": [64, 128, 256]
        },
        "use_uncertainty_loss": {
            "values": [True, False]
        },
        "epochs": {
            "value": 35
        }
    }
}


def main():
    parser = argparse.ArgumentParser(description="Weights & Biases Hyperparameter Sweep for Presto Soil Model")
    parser.add_argument("--mode", type=str, choices=["single", "sweep", "agent"], default="single",
                        help="Mode: 'single' for one run, 'sweep' to create and run sweep, 'agent' to join existing sweep")
    parser.add_argument("--project", type=str, default="presto-soil-nutrients", help="W&B project name")
    parser.add_argument("--count", type=int, default=20, help="Number of sweep trials to execute")
    parser.add_argument("--sweep_id", type=str, default=None, help="Sweep ID to join (if mode=agent)")
    parser.add_argument("--cv_folds", type=int, default=3, help="Spatial cross-validation folds per run (default: 3)")
    args = parser.parse_args()

    if not WANDB_AVAILABLE:
        print("\n" + "=" * 70)
        print("⚠️ Weights & Biases (wandb) is not installed in this Python environment.")
        print("To install, run:")
        print("    pip install wandb")
        print("    wandb login")
        print("=" * 70)
        print(">> Running in local dry-run test mode with default configuration...")
        train_sweep_run(cv_folds=args.cv_folds)
        return

    if args.mode == "single":
        print(f"🚀 Running single test run with W&B logging to project '{args.project}'...")
        train_sweep_run(cv_folds=args.cv_folds)
        
    elif args.mode == "sweep":
        print(f"🚀 Initializing Bayesian Sweep on project '{args.project}'...")
        sweep_id = wandb.sweep(SWEEP_CONFIG, project=args.project)
        print(f"✅ Sweep created successfully with ID: {sweep_id}")
        print(f"Starting {args.count} trials...")
        wandb.agent(sweep_id, function=lambda: train_sweep_run(cv_folds=args.cv_folds), count=args.count)
        
    elif args.mode == "agent":
        if not args.sweep_id:
            raise ValueError("Please provide --sweep_id when running in 'agent' mode.")
        print(f"Joining sweep agent with ID: {args.sweep_id}...")
        wandb.agent(args.sweep_id, function=lambda: train_sweep_run(cv_folds=args.cv_folds), count=args.count)


if __name__ == "__main__":
    main()
