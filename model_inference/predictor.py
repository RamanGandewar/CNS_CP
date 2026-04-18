import joblib
import pandas as pd
from pathlib import Path

from model_inference.feature_builder import align_features, build_feature_vector
from model_inference.risk_engine import compute_risk

# ==============================
# PATH CONFIG
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT_DIR / "model_training" / "artifacts" / "fraud_model_with_graph.pkl"
ANOMALY_MODEL_PATH = ROOT_DIR / "model_training" / "artifacts" / "anomaly_model.pkl"

# ==============================
# LOAD MODELS
# ==============================
print("Loading models...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Fraud model not found at {MODEL_PATH}")

if not ANOMALY_MODEL_PATH.exists():
    raise FileNotFoundError(f"Anomaly model not found at {ANOMALY_MODEL_PATH}")

model = joblib.load(MODEL_PATH)
anomaly_model = joblib.load(ANOMALY_MODEL_PATH)

MODEL_FEATURE_NAMES = [str(column) for column in getattr(model, "feature_names_in_", [])]
ANOMALY_FEATURE_NAMES = [str(column) for column in getattr(anomaly_model, "feature_names_in_", [])]

print("Models loaded successfully!")


# ==============================
# PREDICT FUNCTION
# ==============================
def predict_transaction(transaction: dict):

    # Step 1: Build features
    processed_df = build_feature_vector(transaction)
    combined_features = processed_df.iloc[0].to_dict()

    model_input = (
        align_features(combined_features, MODEL_FEATURE_NAMES)
        if MODEL_FEATURE_NAMES
        else processed_df
    )
    anomaly_input = (
        align_features(combined_features, ANOMALY_FEATURE_NAMES)
        if ANOMALY_FEATURE_NAMES
        else processed_df
    )

    # Step 2: ML prediction
    fraud_prob = float(model.predict_proba(model_input)[0][1])

    # Step 3: Anomaly detection
    anomaly_raw = anomaly_model.decision_function(anomaly_input)[0]

    # Normalize anomaly score
    anomaly_score = float(1 - anomaly_raw)

    # Step 4: Risk engine
    result = compute_risk(fraud_prob, transaction, anomaly_score)

    return result


# ==============================
# TEST RUN
# ==============================
if __name__ == "__main__":

    sample_transaction = {
        "TransactionAmt": 5000,
        "card1": 1234,
        "device": "unknown"
    }

    result = predict_transaction(sample_transaction)

    print("\nPrediction Result:")
    print(result)
