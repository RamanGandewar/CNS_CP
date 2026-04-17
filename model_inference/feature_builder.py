import pandas as pd
import numpy as np
from pathlib import Path

from model_inference.graph_engine import compute_graph_features

# ==============================
# LOAD TRAINING SCHEMA
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_train.csv"

df = pd.read_csv(DATA_PATH)
FEATURE_COLUMNS = df.drop(columns=["isFraud"]).columns.tolist()


# ==============================
# FEATURE ENGINEERING
# ==============================
def create_features(input_data: dict):
    features = {}

    # Basic
    features["TransactionAmt"] = input_data.get("TransactionAmt", 0)
    features["card1"] = input_data.get("card1", 0)

    # Time features
    features["transaction_hour"] = input_data.get("transaction_hour", 12)
    features["transaction_day"] = input_data.get("transaction_day", 15)

    # Log transform
    amt = features["TransactionAmt"]
    features["log_transaction_amt"] = np.log1p(amt)

    # Device features
    device = input_data.get("device", "unknown")
    features["is_mobile_device"] = 1 if device == "mobile" else 0
    features["device_info_missing"] = 1 if device == "unknown" else 0

    # Address
    features["has_full_address"] = 1 if input_data.get("addr1") else 0

    # Dummy engineered features
    features["email_domain_match"] = 0
    features["product_amount_ratio"] = 1.0

    return features


# ==============================
# BUILD FINAL FEATURE VECTOR
# ==============================
def build_feature_vector(raw_input: dict):

    # Step 1: engineered features
    engineered = create_features(raw_input)

    # Step 2: graph features 🔥
    graph_features = compute_graph_features(raw_input)

    # Step 3: merge all
    combined = {**raw_input, **engineered, **graph_features}

    # Step 4: align with training schema
    final_features = {}

    for col in FEATURE_COLUMNS:
        final_features[col] = combined.get(col, 0)

    return pd.DataFrame([final_features])