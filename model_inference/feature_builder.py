import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from model_inference.graph_engine import compute_graph_features

# ==============================
# LOAD TRAINING SCHEMA
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_train.csv"
MODEL_PATH = ROOT_DIR / "model_training" / "artifacts" / "fraud_model_with_graph.pkl"

df = pd.read_csv(DATA_PATH)
FEATURE_COLUMNS = df.drop(columns=["isFraud"]).columns.tolist()


def load_feature_columns():
    columns = FEATURE_COLUMNS.copy()

    if MODEL_PATH.exists():
        model = joblib.load(MODEL_PATH)
        model_feature_names = getattr(model, "feature_names_in_", None)
        if model_feature_names is not None:
            return [str(column) for column in model_feature_names]

    for graph_column in ("user_degree", "device_degree"):
        if graph_column not in columns:
            columns.append(graph_column)

    return columns


MODEL_FEATURE_COLUMNS = load_feature_columns()


def align_features(combined: dict, columns: list[str]):
    final_features = {}
    for column in columns:
        final_features[column] = combined.get(column, 0)
    return pd.DataFrame([final_features], columns=columns)


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
    return align_features(combined, MODEL_FEATURE_COLUMNS)
