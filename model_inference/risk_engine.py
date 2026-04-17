from typing import Dict, List

from model_inference.graph_engine import (
    update_graph,
    compute_graph_risk,
    detect_fraud_clusters
)


# ==============================
# RULE ENGINE
# ==============================
def rule_based_checks(transaction: Dict):
    score = 0
    reasons: List[str] = []

    amount = transaction.get("TransactionAmt", 0)
    device = transaction.get("device", "unknown")
    addr1 = transaction.get("addr1", None)

    if amount > 5000:
        score += 40
        reasons.append("Very high transaction amount")
    elif amount > 1000:
        score += 25
        reasons.append("High transaction amount")

    if device == "unknown":
        score += 15
        reasons.append("Unknown device")

    if addr1 is None:
        score += 10
        reasons.append("Missing address")

    if device == "mobile":
        score += 5
        reasons.append("Mobile device usage")

    return score, reasons


# ==============================
# FINAL RISK ENGINE
# ==============================
def compute_risk(ml_probability: float, transaction: Dict, anomaly_score: float):

    # 🔹 Update graph DB
    update_graph(transaction)

    # ML score
    ml_score = ml_probability * 100

    # Rule score
    rule_score, reasons = rule_based_checks(transaction)

    # Anomaly score
    anomaly_component = anomaly_score * 100

    # Graph score
    graph_score, graph_reasons = compute_graph_risk(transaction)
    reasons.extend(graph_reasons)

    # 🔥 Base score
    final_score = (
        0.5 * ml_score +
        0.2 * rule_score +
        0.15 * anomaly_component +
        0.15 * graph_score
    )

    # 🔥 Cluster detection
    clusters = detect_fraud_clusters()
    user = f"user_{transaction.get('card1', 'unknown')}"

    for cluster in clusters:
        if user in cluster:
            final_score += 10
            reasons.append("Part of suspicious transaction cluster")
            break

    final_score = round(final_score, 2)

    # Risk level
    if final_score < 30:
        level = "Low"
    elif final_score < 70:
        level = "Medium"
    else:
        level = "High"

    # Anomaly explanation
    if anomaly_score > 0.7:
        reasons.append("Unusual transaction behavior detected")

    return {
        "fraud_probability": round(ml_probability, 4),
        "risk_score": final_score,
        "risk_level": level,
        "reasons": reasons
    }