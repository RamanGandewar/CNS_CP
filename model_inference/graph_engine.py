from model_inference.graph_store import (
    initialize_db,
    insert_edge,
    get_device_connections,
    get_user_degree,
    get_connection
)

import networkx as nx

# Initialize DB
initialize_db()


# ==============================
# UPDATE GRAPH (STORE EDGE)
# ==============================
def update_graph(transaction: dict):
    user = f"user_{transaction.get('card1', 'unknown')}"
    device = f"device_{transaction.get('device', 'unknown')}"
    amount = transaction.get("TransactionAmt", 0)

    insert_edge(user, device, amount)


# ==============================
# GRAPH RISK (RULE-STYLE)
# ==============================
def compute_graph_risk(transaction: dict):

    user = f"user_{transaction.get('card1', 'unknown')}"
    device = f"device_{transaction.get('device', 'unknown')}"

    score = 0
    reasons = []

    # User activity
    user_degree = get_user_degree(user)
    if user_degree > 5:
        score += 20
        reasons.append("User has high transaction frequency")

    # Device sharing
    connected_users = get_device_connections(device)
    if len(connected_users) > 3:
        score += 25
        reasons.append("Device shared across multiple accounts")

    return score, reasons


# ==============================
# GRAPH FEATURES FOR ML 🔥
# ==============================
def compute_graph_features(transaction: dict):

    user = f"user_{transaction.get('card1', 'unknown')}"
    device = f"device_{transaction.get('device', 'unknown')}"

    user_degree = get_user_degree(user)
    device_degree = len(get_device_connections(device))

    return {
        "user_degree": user_degree,
        "device_degree": device_degree
    }


# ==============================
# FRAUD CLUSTER DETECTION 🔥
# ==============================
def detect_fraud_clusters():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user, device FROM edges")
    edges = cursor.fetchall()

    conn.close()

    G = nx.Graph()

    for u, d in edges:
        G.add_edge(u, d)

    clusters = list(nx.connected_components(G))

    # Suspicious clusters
    suspicious_clusters = [c for c in clusters if len(c) > 4]

    return suspicious_clusters