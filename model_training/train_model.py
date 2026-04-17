import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    classification_report
)

# ==============================
# PATH CONFIG
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

# 🔥 CHANGE ONLY THIS IF DATASET NAME CHANGES
DATASET_PREFIX = "ieee_dev_model_ready"

DATASET_DIR = ROOT_DIR / "model_preparation" / "outputs" / "datasets"

TRAIN_DATA_PATH = DATASET_DIR / f"{DATASET_PREFIX}_train.csv"
VALID_DATA_PATH = DATASET_DIR / f"{DATASET_PREFIX}_validation.csv"

ARTIFACT_DIR = ROOT_DIR / "model_training" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "fraud_model.pkl"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"


# ==============================
# LOAD DATA
# ==============================
def load_data():
    print(f"Looking for train data at: {TRAIN_DATA_PATH}")
    print(f"Looking for validation data at: {VALID_DATA_PATH}")

    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Train file not found: {TRAIN_DATA_PATH}")

    if not VALID_DATA_PATH.exists():
        raise FileNotFoundError(f"Validation file not found: {VALID_DATA_PATH}")

    train_df = pd.read_csv(TRAIN_DATA_PATH)
    valid_df = pd.read_csv(VALID_DATA_PATH)

    X_train = train_df.drop(columns=["isFraud"])
    y_train = train_df["isFraud"]

    X_valid = valid_df.drop(columns=["isFraud"])
    y_valid = valid_df["isFraud"]

    return X_train, y_train, X_valid, y_valid


# ==============================
# HANDLE CLASS IMBALANCE
# ==============================
def compute_scale_pos_weight(y):
    fraud = np.sum(y == 1)
    non_fraud = np.sum(y == 0)

    if fraud == 0:
        return 1.0

    return non_fraud / fraud


# ==============================
# TRAIN MODEL
# ==============================
def train_model(X_train, y_train):
    print("Computing class imbalance weight...")
    scale_pos_weight = compute_scale_pos_weight(y_train)

    print(f"scale_pos_weight: {scale_pos_weight:.2f}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        eval_metric="logloss"
    )

    print("Fitting model...")
    model.fit(X_train, y_train)

    return model


# ==============================
# EVALUATE MODEL
# ==============================
def evaluate_model(model, X_valid, y_valid):
    print("Running evaluation...")

    y_probs = model.predict_proba(X_valid)[:, 1]
    y_preds = (y_probs > 0.5).astype(int)

    roc_auc = roc_auc_score(y_valid, y_probs)
    pr_auc = average_precision_score(y_valid, y_probs)

    report = classification_report(y_valid, y_preds, output_dict=True)

    metrics = {
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "classification_report": report
    }

    return metrics


# ==============================
# SAVE ARTIFACTS
# ==============================
def save_artifacts(model, metrics):
    print("Saving model...")
    joblib.dump(model, MODEL_PATH)

    print("Saving metrics...")
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)


# ==============================
# MAIN PIPELINE
# ==============================
def main():
    print("\n🚀 Starting Model Training Pipeline\n")

    X_train, y_train, X_valid, y_valid = load_data()

    print("\nTraining model...\n")
    model = train_model(X_train, y_train)

    print("\nEvaluating model...\n")
    metrics = evaluate_model(model, X_valid, y_valid)

    print(f"\n✅ ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"✅ PR-AUC: {metrics['pr_auc']:.4f}")

    save_artifacts(model, metrics)

    print("\n🎯 Training Complete!")
    print(f"Model saved at: {MODEL_PATH}")
    print(f"Metrics saved at: {METRICS_PATH}")


if __name__ == "__main__":
    main()