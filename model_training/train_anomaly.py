import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest

# ==============================
# PATHS
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_train.csv"

ARTIFACT_DIR = ROOT_DIR / "model_training" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "anomaly_model.pkl"


# ==============================
# LOAD DATA
# ==============================
df = pd.read_csv(DATA_PATH)

X = df.drop(columns=["isFraud"])


# ==============================
# TRAIN ISOLATION FOREST
# ==============================
print("Training Isolation Forest...")

model = IsolationForest(
    n_estimators=100,
    contamination=0.02,
    random_state=42,
    n_jobs=-1
)

model.fit(X)

# ==============================
# SAVE MODEL
# ==============================
joblib.dump(model, MODEL_PATH)

print(f"Anomaly model saved at: {MODEL_PATH}")