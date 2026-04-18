import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from model_inference.graph_store import DB_PATH
SESSION_TTL_DAYS = 7


def utc_now():
    return datetime.now(timezone.utc)


def now_iso():
    return utc_now().isoformat()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def initialize_app_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            amount REAL NOT NULL,
            card1 INTEGER,
            device TEXT,
            addr1 INTEGER,
            fraud_probability REAL NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            status TEXT NOT NULL,
            reasons_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_predictions_risk_level ON predictions(risk_level)"
    )

    conn.commit()
    conn.close()


def create_user(name: str, email: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    cursor.execute(
        """
        INSERT INTO users (name, email, password_salt, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name.strip(), email.strip().lower(), salt, password_hash, now_iso()),
    )

    user_id = cursor.lastrowid
    conn.commit()
    user = get_user_by_id(user_id, conn=conn)
    conn.close()
    return user


def get_user_by_email(email: str, conn=None):
    owns_connection = conn is None
    conn = conn or get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    if owns_connection:
        conn.close()
    return row


def get_user_by_id(user_id: int, conn=None):
    owns_connection = conn is None
    conn = conn or get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if owns_connection:
        conn.close()
    return row


def verify_user(email: str, password: str):
    conn = get_connection()
    user = get_user_by_email(email, conn=conn)
    if not user:
        conn.close()
        return None

    expected_hash = hash_password(password, user["password_salt"])
    if expected_hash != user["password_hash"]:
        conn.close()
        return None

    conn.close()
    return user


def create_session(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    token = secrets.token_urlsafe(32)
    created_at = utc_now()
    expires_at = created_at + timedelta(days=SESSION_TTL_DAYS)

    cursor.execute(
        """
        INSERT INTO sessions (user_id, token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token, created_at.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def get_session_user(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT users.*
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    )
    user = cursor.fetchone()

    cursor.execute("SELECT expires_at FROM sessions WHERE token = ?", (token,))
    session = cursor.fetchone()

    if not user or not session:
        conn.close()
        return None

    expires_at = datetime.fromisoformat(session["expires_at"])
    if expires_at <= utc_now():
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None

    conn.close()
    return user


def delete_session(token: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def serialize_user(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def _status_from_level(risk_level: str) -> str:
    normalized = (risk_level or "").lower()
    if normalized == "high":
        return "flagged"
    if normalized == "medium":
        return "review"
    return "safe"


def save_prediction(user_id: int | None, transaction: dict, result: dict):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = now_iso()
    transaction_id = f"TXN-{int(datetime.fromisoformat(created_at).timestamp() * 1000)}-{secrets.token_hex(2).upper()}"
    risk_level = result.get("risk_level", "Low")
    status = _status_from_level(risk_level)

    cursor.execute(
        """
        INSERT INTO predictions (
            transaction_id,
            user_id,
            amount,
            card1,
            device,
            addr1,
            fraud_probability,
            risk_score,
            risk_level,
            status,
            reasons_json,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            user_id,
            float(transaction.get("TransactionAmt", 0) or 0),
            int(transaction.get("card1", 0) or 0),
            transaction.get("device", "unknown"),
            int(transaction.get("addr1", 0) or 0),
            float(result.get("fraud_probability", 0) or 0),
            float(result.get("risk_score", 0) or 0),
            risk_level,
            status,
            json.dumps(result.get("reasons", [])),
            created_at,
        ),
    )

    conn.commit()
    conn.close()
    return transaction_id


def _format_transaction_row(row):
    created_at = datetime.fromisoformat(row["created_at"])
    return {
        "id": row["transaction_id"],
        "amount": row["amount"],
        "card1": row["card1"],
        "device": row["device"],
        "addr1": row["addr1"],
        "fraud_probability": row["fraud_probability"],
        "risk_score": row["risk_score"],
        "risk": row["risk_level"],
        "status": row["status"],
        "reasons": json.loads(row["reasons_json"]),
        "time": created_at.strftime("%H:%M"),
        "date": created_at.strftime("%Y-%m-%d %H:%M"),
    }


def list_transactions(limit: int = 50, risk: str | None = None, device: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM predictions WHERE 1 = 1"
    params = []

    if risk and risk.lower() != "all":
        query += " AND LOWER(risk_level) = ?"
        params.append(risk.lower())

    if device and device.lower() != "all":
        query += " AND LOWER(device) = ?"
        params.append(device.lower())

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_format_transaction_row(row) for row in rows]


def _count_predictions_between(start_iso: str | None = None, end_iso: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT COUNT(*) AS count FROM predictions WHERE 1 = 1"
    params = []
    if start_iso:
        query += " AND created_at >= ?"
        params.append(start_iso)
    if end_iso:
        query += " AND created_at < ?"
        params.append(end_iso)

    cursor.execute(query, params)
    count = cursor.fetchone()["count"]
    conn.close()
    return count


def _count_by_risk_level(risk_level: str, start_iso: str | None = None, end_iso: str | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT COUNT(*) AS count FROM predictions WHERE LOWER(risk_level) = ?"
    params = [risk_level.lower()]
    if start_iso:
        query += " AND created_at >= ?"
        params.append(start_iso)
    if end_iso:
        query += " AND created_at < ?"
        params.append(end_iso)

    cursor.execute(query, params)
    count = cursor.fetchone()["count"]
    conn.close()
    return count


def _get_average_risk_score():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(risk_score) AS avg_score FROM predictions")
    row = cursor.fetchone()
    conn.close()
    return round(row["avg_score"] or 0, 2)


def _get_detection_rate():
    total = _count_predictions_between()
    if total == 0:
        return 0.0
    fraud_count = _count_by_risk_level("high")
    return round((fraud_count / total) * 100, 1)


def _weekday_series():
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    now = utc_now()
    start = now - timedelta(days=6)

    series = []
    conn = get_connection()
    cursor = conn.cursor()
    for offset in range(7):
        day = (start + timedelta(days=offset)).date()
        next_day = day + timedelta(days=1)
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN LOWER(risk_level) = 'high' THEN 1 ELSE 0 END) AS high,
                SUM(CASE WHEN LOWER(risk_level) = 'medium' THEN 1 ELSE 0 END) AS medium,
                SUM(CASE WHEN LOWER(risk_level) = 'low' THEN 1 ELSE 0 END) AS low
            FROM predictions
            WHERE created_at >= ? AND created_at < ?
            """,
            (
                datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
                datetime.combine(next_day, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            ),
        )
        row = cursor.fetchone()
        series.append(
            {
                "label": labels[day.weekday()],
                "high": row["high"] or 0,
                "med": row["medium"] or 0,
                "low": row["low"] or 0,
            }
        )

    conn.close()
    return series


def get_dashboard_summary():
    now = utc_now()
    start_today = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    start_yesterday = start_today - timedelta(days=1)

    total_scanned = _count_predictions_between()
    scanned_today = _count_predictions_between(start_today.isoformat())
    scanned_yesterday = _count_predictions_between(start_yesterday.isoformat(), start_today.isoformat())
    fraud_detected = _count_by_risk_level("high")
    review_count = _count_by_risk_level("medium")
    detection_rate = _get_detection_rate()

    return {
        "stats": [
            {
                "label": "Total Scanned",
                "value": total_scanned,
                "delta": f"+{max(scanned_today - scanned_yesterday, 0)} from yesterday",
                "up": True,
            },
            {
                "label": "Fraud Detected",
                "value": fraud_detected,
                "delta": f"{fraud_detected} high-risk transactions logged",
                "up": False,
            },
            {
                "label": "Under Review",
                "value": review_count,
                "delta": f"{review_count} medium-risk transactions",
                "up": None,
            },
            {
                "label": "Detection Rate",
                "value": detection_rate,
                "delta": "High-risk share of total scans",
                "up": True,
            },
        ],
        "breakdown": {
            "high": fraud_detected,
            "med": review_count,
            "low": _count_by_risk_level("low"),
        },
        "risk_over_time": _weekday_series(),
        "recent_transactions": list_transactions(limit=5),
        "alerts": get_alerts(),
        "analytics": get_analytics_snapshot(),
    }


def get_graph_stats(node_count: int, edge_count: int, cluster_count: int):
    high_risk = _count_by_risk_level("high")
    return [
        {"label": "Total Nodes", "value": node_count},
        {"label": "Total Edges", "value": edge_count},
        {"label": "Flagged Nodes", "value": high_risk},
        {"label": "Clusters", "value": cluster_count},
    ]


def get_alerts():
    recent_high = list_transactions(limit=3, risk="high")
    alerts = []

    for txn in recent_high:
        alerts.append(
            {
                "title": "High-risk transaction detected",
                "sub": f"{txn['id']} scored {round(txn['risk_score'])} on {txn['device']}",
                "urgent": True,
            }
        )

    medium_txns = list_transactions(limit=2, risk="medium")
    for txn in medium_txns:
        alerts.append(
            {
                "title": "Manual review suggested",
                "sub": f"{txn['id']} has {len(txn['reasons'])} triggered rules",
                "urgent": False,
            }
        )

    return alerts[:4]


def get_analytics_snapshot():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS total, AVG(risk_score) AS avg_risk
        FROM predictions
        """
    )
    base = cursor.fetchone()
    conn.close()

    cluster_proxy = max(1, round((_count_by_risk_level("high") + _count_by_risk_level("medium")) / 2, 1))
    false_positive_proxy = round(max(0.5, 100 - _get_detection_rate()) / 20, 1)

    return [
        {
            "label": "Avg. Risk Score",
            "value": round(base["avg_risk"] or 0, 2),
            "delta": "Across all saved transaction scans",
            "up": None,
        },
        {
            "label": "Avg. Cluster Size",
            "value": cluster_proxy,
            "delta": "Approximation from suspicious activity groups",
            "up": None,
        },
        {
            "label": "False Positive Proxy",
            "value": false_positive_proxy,
            "delta": "Presentation metric from current scan history",
            "up": True,
        },
        {
            "label": "Detection Rate",
            "value": _get_detection_rate(),
            "delta": "High-risk percentage",
            "up": True,
        },
    ]


def get_latest_prediction_timestamp():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT created_at FROM predictions ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row["created_at"] if row else None
