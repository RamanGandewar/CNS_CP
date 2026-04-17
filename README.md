# 🚀 Intelligent Fraudulent Transaction Detection System

## 🧠 Overview

This project is a real-time, scalable fraud detection system designed to identify fraudulent transactions using a combination of:

- Machine Learning
- Rule-Based Detection
- Feature Engineering
- API Deployment
- Explainable Risk Scoring

Unlike traditional systems, this solution goes beyond simple classification and provides **interpretable risk scores and reasons**, making it suitable for real-world financial systems.

---

## 🎯 Objectives

- Detect fraudulent transactions in real-time
- Handle evolving fraud patterns
- Reduce false positives
- Provide explainable predictions
- Build a scalable and modular system

---

## 🏗️ System Architecture

```
Raw Transaction Input
        ↓
Feature Builder
        ↓
ML Model (XGBoost)
        ↓
Risk Engine (Rules + ML)
        ↓
FastAPI Backend
        ↓
Response (Score + Explanation)
```

---

## 📁 Project Structure

```
CP/
│
├── model_preparation/
│   ├── outputs/
│   │   └── datasets/
│   │       ├── ieee_dev_model_ready_train.csv
│   │       └── ieee_dev_model_ready_validation.csv
│   └── artifacts/
│       └── ieee_dev_model_ready_preprocessor.joblib
│
├── model_training/
│   ├── train_model.py
│   └── artifacts/
│       ├── fraud_model.pkl
│       └── metrics.json
│
├── model_inference/
│   ├── predictor.py
│   ├── feature_builder.py
│   └── risk_engine.py
│
├── backend/
│   └── main.py
│
└── README.md
```

---

## ⚙️ Tech Stack

### 🔹 Backend
- FastAPI
- Uvicorn

### 🔹 Machine Learning
- XGBoost
- scikit-learn

### 🔹 Data Processing
- Pandas
- NumPy

### 🔹 Model Persistence
- joblib

---

## 📊 Dataset

**Primary Dataset:** [IEEE-CIS Fraud Detection Dataset](https://www.kaggle.com/c/ieee-fraud-detection)

Preprocessed into:
- Training dataset
- Validation dataset

---

## 🔄 Workflow

### 🔹 1. Data Preparation
- Cleaning missing values
- Feature engineering
- Encoding categorical variables
- Saving processed datasets

### 🔹 2. Model Training

- **Model Used:** XGBoost Classifier
- Handles class imbalance using `scale_pos_weight`
- **Evaluation Metrics:**
  - ROC-AUC
  - PR-AUC
- **Output:**
  - `fraud_model.pkl`
  - `metrics.json`

### 🔹 3. Inference Layer

Implemented in `predictor.py`:
- Loads trained model
- Accepts transaction input
- Returns fraud probability

### 🔹 4. Feature Builder *(Key Component 🔥)*

Implemented in `feature_builder.py`:
- Converts raw input → model-ready features
- Handles:
  - Missing values
  - Feature engineering
  - Schema alignment

### 🔹 5. Risk Scoring Engine *(Core Intelligence 🔥)*

Implemented in `risk_engine.py`. Combines:
- ML probability
- Rule-based logic

**Example Rules:**
- High transaction amount
- Unknown device
- Missing address
- Mobile device usage

**Output:**
```json
{
  "fraud_probability": 0.0015,
  "risk_score": 1.61,
  "risk_level": "Low",
  "reasons": ["Mobile device usage"]
}
```

### 🔹 6. API Layer

Built using **FastAPI**

**Endpoint:** `POST /predict`

**Input:**
```json
{
  "transaction": {
    "TransactionAmt": 500,
    "card1": 1234,
    "device": "mobile",
    "addr1": 330
  }
}
```

**Output:**
```json
{
  "fraud_probability": 0.0015,
  "risk_score": 1.61,
  "risk_level": "Low",
  "reasons": ["Mobile device usage"]
}
```

---

## 🚀 How to Run

### 1️⃣ Activate Environment

```bash
source .venv/bin/activate
# or (Windows)
.venv\Scripts\activate
```

### 2️⃣ Train Model

```bash
python model_training/train_model.py
```

### 3️⃣ Run API

```bash
uvicorn backend.main:app --reload
```

### 4️⃣ Open Swagger UI

```
http://127.0.0.1:8000/docs
```

---

## 🧠 Key Features

| Feature | Description |
|---|---|
| ✅ Real-Time Prediction | API-based inference |
| ✅ Explainable AI | Risk score + reasons |
| ✅ Hybrid Detection | ML + Rule-based system |
| ✅ Modular Architecture | Easy to extend |
| ✅ Raw Input Handling | No need for full feature vector |

---

## 🔥 Unique Selling Points (USP)

### 🔹 1. Feature Builder Layer
Bridges the gap between raw data and the ML model — no preprocessing required from the client.

### 🔹 2. Risk Scoring Engine
Not just a prediction — an **interpretable decision system** that explains *why* a transaction is flagged.

### 🔹 3. End-to-End Pipeline
From data → model → API → output, fully integrated and production-ready.

---

## ⚠️ Current Limitations

- Feature engineering is simplified
- No real-time streaming yet
- Graph-based fraud detection not integrated yet
- No drift detection module *(planned)*

---

## 🚀 Future Enhancements

- 🔹 Anomaly Detection (Isolation Forest)
- 🔹 Graph-Based Fraud Detection (GNN)
- 🔹 Kafka Streaming Integration
- 🔹 Dashboard (Streamlit / React)
- 🔹 Drift Detection System

---

## 🎯 Final Summary

> *"A real-time, explainable fraud detection system combining machine learning, rule-based intelligence, and feature engineering into a scalable API-driven architecture."*

---

## 👨‍💻 Author

**Raman Gandewar**
**Divij Gujarathi**
