import pandas as pd
import numpy as np
from pathlib import Path

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
    """
    Convert raw transaction → feature-rich dict
    """

    features = {}

    # 🔹 Basic fields
    features["TransactionAmt"] = input_data.get("TransactionAmt", 0)
    features["card1"] = input_data.get("card1", 0)

    # 🔹 Time-based features
    features["transaction_hour"] = input_data.get("transaction_hour", 12)
    features["transaction_day"] = input_data.get("transaction_day", 15)

    # 🔹 Log transform
    amt = features["TransactionAmt"]
    features["log_transaction_amt"] = np.log1p(amt)

    # 🔹 Device flags
    device = input_data.get("device", "unknown")

    features["is_mobile_device"] = 1 if device == "mobile" else 0
    features["device_info_missing"] = 1 if device == "unknown" else 0

    # 🔹 Address flags
    features["has_full_address"] = 1 if input_data.get("addr1") else 0

    # 🔹 Email match (dummy logic)
    features["email_domain_match"] = 0

    # 🔹 Ratio feature (safe default)
    features["product_amount_ratio"] = 1.0

    return features


# ==============================
# BUILD FULL FEATURE VECTOR
# ==============================
def build_feature_vector(raw_input: dict):
    """
    Create full model-ready feature vector
    """

    # Step 1: generate engineered features
    engineered = create_features(raw_input)

    # Step 2: merge raw + engineered
    combined = {**raw_input, **engineered}

    # Step 3: align with training schema
    final_features = {}

    for col in FEATURE_COLUMNS:
        final_features[col] = combined.get(col, 0)

    return pd.DataFrame([final_features])