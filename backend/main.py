import sqlite3
from random import choice, randint, uniform
from typing import Dict, Optional

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.storage import (
    create_session,
    create_user,
    delete_session,
    get_alerts,
    get_dashboard_summary,
    get_graph_stats,
    get_latest_prediction_timestamp,
    get_session_user,
    initialize_app_db,
    list_transactions,
    save_prediction,
    serialize_user,
    verify_user,
)
from model_inference.graph_engine import detect_fraud_clusters
from model_inference.graph_store import get_connection as get_graph_connection
from model_inference.predictor import predict_transaction


app = FastAPI(title="Fraud Detection API")
initialize_app_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionRequest(BaseModel):
    transaction: Dict


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class DemoSeedRequest(BaseModel):
    count: int = Field(default=8, ge=1, le=25)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)


manager = ConnectionManager()


def get_current_user(authorization: Optional[str]) -> Optional[dict]:
    if not authorization:
        return None

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None

    token = authorization[len(prefix):].strip()
    if not token:
        return None

    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return serialize_user(user)


def require_user(authorization: Optional[str]) -> dict:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def build_auth_response(user_row):
    token = create_session(user_row["id"])
    return {"token": token, "user": serialize_user(user_row)}


async def broadcast_data_change(event: str, transaction_id: str | None = None):
    await manager.broadcast(
        {
            "type": "dashboard_update",
            "event": event,
            "transaction_id": transaction_id,
            "last_updated": get_latest_prediction_timestamp(),
        }
    )


@app.get("/")
def home():
    return {"message": "Fraud Detection API running"}


@app.post("/auth/signup")
def signup(data: SignupRequest):
    try:
        user = create_user(data.name, data.email, data.password)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    return build_auth_response(user)


@app.post("/auth/login")
def login(data: LoginRequest):
    user = verify_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return build_auth_response(user)


@app.get("/auth/me")
def auth_me(authorization: Optional[str] = Header(default=None)):
    user = require_user(authorization)
    return {"user": user}


@app.post("/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    user = require_user(authorization)
    token = authorization[len("Bearer "):].strip()
    delete_session(token)
    return {"message": f"Logged out {user['email']}"}


@app.post("/predict")
async def predict(data: TransactionRequest, authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)
    result = predict_transaction(data.transaction)
    transaction_id = save_prediction(user["id"] if user else None, data.transaction, result)
    await broadcast_data_change("prediction_created", transaction_id)
    return {**result, "transaction_id": transaction_id}


@app.get("/dashboard/summary")
def dashboard_summary(authorization: Optional[str] = Header(default=None)):
    require_user(authorization)
    summary = get_dashboard_summary()
    summary["last_updated"] = get_latest_prediction_timestamp()
    return summary


@app.get("/transactions")
def get_transactions(
    risk: str = "all",
    device: str = "all",
    limit: int = 50,
    authorization: Optional[str] = Header(default=None),
):
    require_user(authorization)
    return {"transactions": list_transactions(limit=limit, risk=risk, device=device)}


@app.get("/graph-data")
def get_graph_data(authorization: Optional[str] = Header(default=None)):
    require_user(authorization)

    conn = get_graph_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user, device FROM edges")
    rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT DISTINCT card1, device
        FROM predictions
        WHERE LOWER(risk_level) = 'high'
        """
    )
    flagged = cursor.fetchall()
    conn.close()

    flagged_users = {f"user_{row['card1']}" for row in flagged if row["card1"] is not None}
    flagged_devices = {f"device_{row['device']}" for row in flagged if row["device"]}

    nodes = {}
    links = []
    seen_links = set()
    for row in rows:
        user = row["user"]
        device = row["device"]
        user_label = user.replace("user_", "Card ")
        device_label = device.replace("device_", "Device ").title()

        nodes[user] = {
            "id": user,
            "label": user_label,
            "type": "user",
            "fraud": user in flagged_users,
        }
        nodes[device] = {
            "id": device,
            "label": device_label,
            "type": "device",
            "fraud": device in flagged_devices,
        }
        edge_key = (user, device)
        if edge_key not in seen_links:
            seen_links.add(edge_key)
            links.append({"source": user, "target": device})

    clusters = detect_fraud_clusters()
    return {
        "nodes": list(nodes.values()),
        "links": links,
        "stats": get_graph_stats(len(nodes), len(links), len(clusters)),
    }


@app.get("/clusters")
def get_clusters(authorization: Optional[str] = Header(default=None)):
    require_user(authorization)
    clusters = detect_fraud_clusters()
    items = []
    for index, cluster in enumerate(clusters, start=1):
        risk = "high" if len(cluster) >= 6 else "medium"
        items.append(
            {
                "id": f"Cluster-{index}",
                "nodes": sorted(cluster),
                "risk": risk,
                "size": len(cluster),
            }
        )
    return {"clusters": items}


@app.get("/alerts")
def get_live_alerts(authorization: Optional[str] = Header(default=None)):
    require_user(authorization)
    return {"alerts": get_alerts()}


def _generate_demo_transaction(index: int):
    device = choice(["desktop", "mobile", "tablet", "unknown"])
    high_risk = index % 3 == 0
    amount = round(uniform(3200, 7800), 2) if high_risk else round(uniform(35, 1600), 2)
    return {
        "TransactionAmt": amount,
        "card1": randint(1000, 9999),
        "device": device,
        "addr1": randint(100, 999),
    }


@app.post("/demo/seed")
async def seed_demo_data(
    data: DemoSeedRequest,
    authorization: Optional[str] = Header(default=None),
):
    user = require_user(authorization)
    created = []

    for index in range(data.count):
        transaction = _generate_demo_transaction(index)
        result = predict_transaction(transaction)
        transaction_id = save_prediction(user["id"], transaction, result)
        created.append(
            {
                "transaction_id": transaction_id,
                "risk_level": result["risk_level"],
                "risk_score": result["risk_score"],
            }
        )

    await broadcast_data_change("demo_seeded")
    return {
        "message": f"Seeded {len(created)} demo transactions",
        "created": created,
        "last_updated": get_latest_prediction_timestamp(),
    }


@app.websocket("/ws/dashboard")
async def dashboard_updates(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "last_updated": get_latest_prediction_timestamp(),
            }
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@app.get("/health")
def health():
    return {"status": "ok"}
