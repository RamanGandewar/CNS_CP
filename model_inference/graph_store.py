import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "model_inference" / "graph.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        device TEXT,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()


def insert_edge(user, device, amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO edges (user, device, amount) VALUES (?, ?, ?)",
        (user, device, amount)
    )

    conn.commit()
    conn.close()


def get_device_connections(device):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT user FROM edges WHERE device = ?",
        (device,)
    )

    result = cursor.fetchall()
    conn.close()

    return [r[0] for r in result]


def get_user_degree(user):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM edges WHERE user = ?",
        (user,)
    )

    count = cursor.fetchone()[0]
    conn.close()

    return count