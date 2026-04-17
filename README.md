# 🚀 Intelligent Fraudulent Transaction Detection System

## 🧠 Overview

This project is a real-time, scalable fraud detection system designed to identify fraudulent transactions using a combination of:

- Machine Learning
- Graph-Based Fraud Detection
- Anomaly Detection
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
- Detect fraud networks and suspicious clusters via graph intelligence

---

## 🏗️ System Architecture

```
Raw Transaction
      ↓
Feature Builder
      ↓
ML Model (XGBoost + Graph Features)
      ↓
Anomaly Detection (Isolation Forest)
      ↓
Graph Engine (SQLite + NetworkX)
      ↓
Cluster Detection
      ↓
Risk Engine (Hybrid Scoring)
      ↓
FastAPI Backend
      ↓
React Dashboard (D3 Visualization)
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
│   ├── train_model_with_graph.py       🔥 NEW
│   ├── train_anomaly.py                🔥 NEW
│   └── artifacts/
│       ├── fraud_model.pkl
│       ├── fraud_model_with_graph.pkl  🔥 NEW
│       ├── anomaly_model.pkl           🔥 NEW
│       └── metrics.json
│
├── model_inference/
│   ├── predictor.py
│   ├── feature_builder.py
│   ├── risk_engine.py
│   ├── graph_engine.py                 🔥 NEW
│   ├── graph_store.py                  🔥 NEW (SQLite)
│   ├── visualize_graph.py              🔥 NEW
│   └── graph.db                        🔥 NEW
│
├── backend/
│   └── main.py
│
├── frontend/                           🔥 NEW
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   └── package.json
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
- Isolation Forest *(NEW)*
- scikit-learn

### 🔹 Graph Processing
- NetworkX *(NEW)*
- SQLite — persistent graph storage *(NEW)*

### 🔹 Frontend
- React (Vite) *(NEW)*
- D3.js *(NEW)*

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

- **Model Used:** XGBoost Classifier (with graph-aware features)
- Handles class imbalance using `scale_pos_weight`
- **Graph Features Added:**
  - `user_degree`
  - `device_degree`
  - `user_embedding`
  - `device_embedding`
- **Evaluation Metrics:**
  - ROC-AUC
  - PR-AUC
- **Output:**
  - `fraud_model.pkl`
  - `fraud_model_with_graph.pkl`
  - `anomaly_model.pkl`
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

### 🔹 5. Graph Engine *(NEW 🔥)*

Implemented in `graph_engine.py` + `graph_store.py`:
- Persistent graph layer using **SQLite**
- Tracks relationships: Users ↔ Devices
- Detects:
  - Shared devices across users
  - Fraud clusters and rings
  - Suspicious connectivity patterns
- Generates lightweight graph embeddings:
  - `user_embedding`
  - `device_embedding`

### 🔹 6. Anomaly Detection Layer *(NEW 🔥)*

Implemented in `train_anomaly.py`:
- Uses **Isolation Forest**
- Detects unknown and novel fraud patterns
- Fully integrated into the risk scoring pipeline

### 🔹 7. Fraud Cluster Detection *(NEW 🔥)*

- Uses graph connected components
- Flags:
  - Suspicious user groups
  - Fraud rings

### 🔹 8. Risk Scoring Engine *(Core Intelligence 🔥 — Upgraded)*

Implemented in `risk_engine.py`. Now combines:
- ML probability (XGBoost)
- Rule-based logic
- Anomaly score (Isolation Forest)
- Graph features
- Fraud cluster signals

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

### 🔹 9. API Layer

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

### 🔹 10. Frontend Dashboard *(NEW 🔥)*

Built with **React (Vite) + D3.js**:
- Full SaaS-style UI
- Graph visualization of user-device relationships
- Fraud insights and analytics
- Real-time transaction monitoring

---

## 🚀 How to Run

### 1️⃣ Activate Environment

```bash
source .venv/bin/activate
# or (Windows)
.venv\Scripts\activate
```

### 2️⃣ Train Models

```bash
# Base model
python model_training/train_model.py

# Graph-aware model
python model_training/train_model_with_graph.py

# Anomaly detection model
python model_training/train_anomaly.py
```

### 3️⃣ Run API

```bash
uvicorn backend.main:app --reload
```

### 4️⃣ Run Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5️⃣ Open Swagger UI

```
http://127.0.0.1:8000/docs
```

---

## 🧠 Key Features

| Feature | Description |
|---|---|
| ✅ ML Detection | XGBoost with graph-aware features |
| ✅ Anomaly Detection | Isolation Forest for unknown patterns |
| ✅ Graph Intelligence | User-device relationship tracking |
| ✅ Fraud Clusters | Detect suspicious groups and fraud rings |
| ✅ Persistent Graph | SQLite-backed graph storage |
| ✅ Explainable AI | Risk score + human-readable reasons |
| ✅ Real-Time API | FastAPI-based inference pipeline |
| ✅ Dashboard | React + D3 graph visualization |

---

## 🔥 Unique Selling Points (USP)

### 🔹 1. Graph-Based Fraud Detection
Detects **fraud networks** instead of isolated transactions — identifies suspicious relationships between users, devices, and accounts.

### 🔹 2. Hybrid Intelligence System
Combines four layers of detection:
- Machine Learning (XGBoost)
- Rule-based logic
- Anomaly detection (Isolation Forest)
- Graph analytics (NetworkX + SQLite)

### 🔹 3. Explainable AI
Provides **clear, human-readable reasons** for every prediction — not just a probability score.

### 🔹 4. Real-Time API System
Fast and scalable prediction pipeline built on FastAPI, ready for production integration.

### 🔹 5. Full-Stack Implementation
Backend + ML + Graph Engine + React Dashboard — a complete end-to-end system.

---

## ⚠️ Current Limitations

- Graph is not yet distributed (local SQLite only)
- No real-time streaming (Kafka planned)
- Graph embeddings are basic (not full GNN yet)
- No drift detection module *(planned)*

---

## 🚀 Future Enhancements

- 🔹 Graph Neural Networks (PyTorch Geometric)
- 🔹 Kafka real-time streaming pipeline
- 🔹 Drift Detection System
- 🔹 Advanced graph embeddings (Node2Vec)
- 🔹 Production deployment (Docker + Cloud)

---

## 🎯 Final Summary

> *"A real-time, scalable, and explainable fraud detection system combining machine learning, anomaly detection, graph-based intelligence, and a modern React dashboard for end-to-end fraud monitoring."*

---

## 👨‍💻 Author

**Raman Gandewar**