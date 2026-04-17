import joblib
import pandas as pd
from pathlib import Path

from model_inference.feature_builder import build_feature_vector
from model_inference.risk_engine import compute_risk

# ==============================
# PATH CONFIG
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT_DIR / "model_training" / "artifacts" / "fraud_model.pkl"

# ==============================
# LOAD MODEL
# ==============================
print("Loading model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


# ==============================
# PREDICT FUNCTION
# ==============================
def predict_transaction(transaction: dict):
    """
    Input: processed transaction (dict)
    Output: fraud probability + risk score
    """

    # Convert to DataFrame
    input_df = pd.DataFrame([transaction])

    # ⚠️ IMPORTANT:
    # Data is already processed → NO preprocessor
    from model_inference.feature_builder import build_feature_vector

    processed_df = build_feature_vector(transaction)
    processed_input = processed_df.values

    # Predict
    fraud_prob = float(model.predict_proba(processed_input)[0][1])
    result = compute_risk(fraud_prob, transaction)

    return result


# ==============================
# TEST RUN
# ==============================
if __name__ == "__main__":

    print("\nLoading sample data...")

    DATA_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_validation.csv"

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Take one real processed row
    sample_transaction = df.drop(columns=["isFraud"]).iloc[0].to_dict()

    print("Running prediction...\n")

    result = predict_transaction(sample_transaction)

    print("Prediction Result:")
    print(result)