from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

# Import predictor
from model_inference.predictor import predict_transaction

# ==============================
# INIT APP
# ==============================
app = FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud detection system",
    version="1.0"
)

# ==============================
# REQUEST SCHEMA
# ==============================
class TransactionInput(BaseModel):
    transaction: Dict


# ==============================
# ROOT ENDPOINT
# ==============================
@app.get("/")
def home():
    return {"message": "Fraud Detection API is running 🚀"}


# ==============================
# PREDICT ENDPOINT
# ==============================
@app.post("/predict")
def predict(data: TransactionInput):
    result = predict_transaction(data.transaction)
    return result