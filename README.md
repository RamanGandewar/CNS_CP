# FraudGuard

**Graph-Aware Fraud Detection Platform with Live Monitoring, Real-Time Updates, and Investigation-Ready Analytics**

<p>
  <strong>FastAPI</strong> •
  <strong>React</strong> •
  <strong>SQLite</strong> •
  <strong>XGBoost</strong> •
  <strong>Isolation Forest</strong> •
  <strong>NetworkX</strong> •
  <strong>WebSockets</strong>
</p>

</div>

## Executive Summary

FraudGuard is a full-stack fraud detection platform built to demonstrate how a modern fraud-monitoring system can combine machine learning, anomaly detection, graph intelligence, persistent audit history, and live operational visibility in a single workflow.

The platform enables authenticated users to submit transactions, score them through a multi-layer risk engine, persist the results to SQLite, visualize suspicious user-device relationships, and monitor changes in real time through a live dashboard. It is structured for local execution today while remaining modular enough to evolve into a more event-driven, production-oriented architecture.

## Key Capabilities

- Multi-layer fraud scoring using supervised ML, anomaly detection, business rules, and graph-derived risk
- Live dashboard updates through WebSocket-based event delivery
- SQLite-backed persistence for users, sessions, predictions, and graph relationships
- Dynamic graph visualization of user-device behavior and suspicious clusters
- Seeded demo transaction generation for testing and presentation scenarios
- Authentication flow with sign up, login, logout, and session restoration
- Modular architecture ready for Kafka-based event streaming in the next phase

## System Architecture

FraudGuard is organized into five major layers:

1. Data engineering and model preparation
2. Model training and artifact generation
3. Runtime inference and graph-based risk computation
4. FastAPI service layer with authenticated APIs and WebSocket broadcasting
5. React dashboard for real-time fraud operations and investigation workflows

### Architecture Diagram

![FraudGuard System Architecture](images/SYSTEM_ARCH.png)

## User Workflow

FraudGuard supports a clear operational workflow for both testing and live demonstration:

1. A user signs up or logs in
2. The user enters the dashboard
3. Transactions can be submitted manually or generated through the demo seed flow
4. The backend runs fraud scoring through the inference stack
5. Results are stored in the runtime database
6. Dashboard metrics, graph relationships, alerts, and analytics update live

### Workflow Diagram

![FraudGuard User Workflow](images/USERFLOW.png)

## Technology Stack

### Frontend

- React
- Vite
- D3

### Backend

- FastAPI
- Uvicorn
- Pydantic
- WebSockets

### Data Science and Graph Analytics

- pandas
- NumPy
- scikit-learn
- XGBoost
- Isolation Forest
- NetworkX

### Persistence

- SQLite

### Planned Extension

- Kafka for event-driven transaction ingestion and asynchronous processing

## Repository Layout

```text
CP/
|-- backend/                         # FastAPI app, API routes, runtime storage utilities
|   |-- main.py
|   `-- storage.py
|-- frontend/                        # React dashboard application
|   |-- package.json
|   `-- src/
|-- model_inference/                 # Runtime inference, graph logic, feature alignment, risk engine
|   |-- feature_builder.py
|   |-- predictor.py
|   |-- risk_engine.py
|   |-- graph_engine.py
|   `-- graph_store.py
|-- model_training/                  # Model training scripts and generated artifacts
|-- model_preparation/               # Model-ready dataset generation and preprocessing artifacts
|-- data_preprocessing/              # Raw dataset preparation and transformation scripts
|-- Database/
|   |-- USERS/
|   |   `-- fraudguard.db            # Runtime SQLite database
|   `-- ...                          # Source datasets
|-- images/                          # Documentation diagrams and visual assets
|-- requirements.txt
`-- README.md
```

## Product Features

### 1. Fraud Scoring Engine

FraudGuard evaluates each transaction using:

- `fraud_model_with_graph.pkl` for supervised fraud probability
- `anomaly_model.pkl` for anomaly detection
- rule-based checks for business-sensitive risk indicators
- graph-derived signals such as shared device usage and suspicious network behavior

Each prediction returns:

- transaction ID
- fraud probability
- risk score
- risk level
- triggered reasons

### 2. Live Monitoring Dashboard

The dashboard provides:

- Overview metrics
- Recent transaction monitoring
- Prediction form and risk assessment view
- User-device graph visualization
- Suspicious cluster monitoring
- Analytics and trend summaries
- Live refresh through backend WebSocket events

### 3. Authentication and Session Management

The authentication layer supports:

- sign up
- login
- logout
- persisted session lookup
- SQLite-backed account and session storage

### 4. Seeded Demo Transactions

The `Seed Demo Data` workflow generates realistic sample transactions and routes them through the same prediction and persistence path as manual submissions. This is useful for:

- academic presentations
- UI validation
- graph population
- alert generation
- end-to-end testing

## Runtime Database

The runtime database is stored at:

`Database/USERS/fraudguard.db`

It persists:

- `users`
- `sessions`
- `predictions`
- `edges`

This database acts as the operational store for authentication, transaction history, graph edges, and dashboard state.

## API Surface

### Authentication APIs

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

### Prediction and Dashboard APIs

- `POST /predict`
- `GET /dashboard/summary`
- `GET /transactions`
- `GET /graph-data`
- `GET /clusters`
- `GET /alerts`
- `GET /health`

### Demo and Real-Time APIs

- `POST /demo/seed`
- `WS /ws/dashboard`

## Local Development Setup

### 1. Create and activate the virtual environment

```powershell
cd "C:\Users\HP\Desktop\SEM 6\CNS\CP"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start the backend service

```powershell
uvicorn backend.main:app --reload
```

Backend default URL:

`http://localhost:8000`

### 3. Start the frontend application

Open a second terminal and run:

```powershell
cd "C:\Users\HP\Desktop\SEM 6\CNS\CP\frontend"
npm install
npm run dev
```

Frontend default URL:

`http://localhost:5173`

## Recommended Demo Flow

1. Start backend and frontend
2. Create a user account or log in
3. Open the overview dashboard
4. Click `Seed Demo Data`
5. Observe transactions, alerts, analytics, and graph updates
6. Submit a manual prediction from the `Predict` page
7. Show the new result appearing immediately across the dashboard

## ML and Data Pipeline

### Data Preprocessing

- `data_preprocessing/scripts/preprocess_ieee_cis.py`
- `data_preprocessing/scripts/prepare_datasets.py`

### Model Preparation

- `model_preparation/scripts/prepare_ieee_model_data.py`

### Training

- `model_training/train_model.py`
- `model_training/train_model_with_graph.py`
- `model_training/train_anomaly.py`

### Runtime Inference

- `model_inference/feature_builder.py`
- `model_inference/predictor.py`
- `model_inference/risk_engine.py`
- `model_inference/graph_engine.py`
- `model_inference/graph_store.py`

## Engineering Enhancements Implemented

- Structured backend storage layer for runtime persistence
- SQLite-backed auth and session management
- Persistent transaction and prediction history
- Live WebSocket broadcasting for dashboard updates
- Seeded demo transaction generation
- Dynamic graph updates driven by saved relationships
- Centralized runtime database under `Database/USERS`
- Presentation-oriented branding and UX improvements

## Roadmap

The next major enhancement is Kafka integration for:

- asynchronous transaction ingestion
- producer-consumer based processing
- event-stream architecture
- improved decoupling between ingestion, inference, and notification layers

## Troubleshooting

### Backend starts but predictions fail

Ensure model artifacts exist under:

`model_training/artifacts/`

### Frontend cannot connect to backend

Verify:

- backend is running on port `8000`
- frontend is running on port `5173`
- frontend API base points to `http://localhost:8000`

### Live updates are not appearing

Verify:

- backend WebSocket route is active at `/ws/dashboard`
- the browser is connected to the WebSocket endpoint
- predictions or seeded demo transactions are being created successfully

## Production Notes

- SQLite is intentionally used for portability, simplicity, and inspectability during local development and presentation.
- The current architecture is well-suited for academic demonstration and local operational testing.
- The codebase is structured to support future migration to Kafka, PostgreSQL, Redis, or dedicated graph infrastructure without redesigning the entire application.

## Author

Raman Gandewar
Divij Gujarathi
Prathamesh Ghalsasi
