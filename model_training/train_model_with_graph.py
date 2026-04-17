import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pandas as pd
import joblib
from xgboost import XGBClassifier

from model_inference.graph_engine import compute_graph_features

# ==============================
# PATHS
# ==============================
ROOT_DIR = Path(__file__).resolve().parents[1]

TRAIN_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_train.csv"
VALID_PATH = ROOT_DIR / "model_preparation" / "outputs" / "datasets" / "ieee_dev_model_ready_validation.csv"

ARTIFACT_DIR = ROOT_DIR / "model_training" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "fraud_model_with_graph.pkl"


# ==============================
# LOAD DATA
# ==============================
print("Loading data...")

train_df = pd.read_csv(TRAIN_PATH)
valid_df = pd.read_csv(VALID_PATH)


# ==============================
# ADD GRAPH FEATURES
# ==============================
def add_graph_features(df):
    graph_features_list = []

    for _, row in df.iterrows():
        raw = {
            "card1": row.get("card1", 0),
            "device": "unknown"
        }

        gf = compute_graph_features(raw)
        graph_features_list.append(gf)

    gf_df = pd.DataFrame(graph_features_list)

    return pd.concat([df.reset_index(drop=True), gf_df], axis=1)


print("Adding graph features...")

train_df = add_graph_features(train_df)
valid_df = add_graph_features(valid_df)


# ==============================
# SPLIT
# ==============================
X_train = train_df.drop(columns=["isFraud"])
y_train = train_df["isFraud"]

X_valid = valid_df.drop(columns=["isFraud"])
y_valid = valid_df["isFraud"]


# ==============================
# TRAIN MODEL
# ==============================
print("Training model with graph features...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=30,
    random_state=42
)

model.fit(X_train, y_train)

# ==============================
# SAVE MODEL
# ==============================
joblib.dump(model, MODEL_PATH)

print(f"Model saved at: {MODEL_PATH}")