from typing import Dict, List


# ==============================
# RULE ENGINE
# ==============================
def rule_based_checks(transaction: Dict) -> Dict:
    score = 0
    reasons: List[str] = []

    amount = transaction.get("TransactionAmt", 0)
    device = transaction.get("device", "unknown")
    addr1 = transaction.get("addr1", None)

    # 🔹 Rule 1: High transaction amount
    if amount > 1000:
        score += 25
        reasons.append("High transaction amount")

    # 🔹 Rule 2: Very high amount
    if amount > 5000:
        score += 40
        reasons.append("Very high transaction amount")

    # 🔹 Rule 3: Unknown device
    if device == "unknown":
        score += 15
        reasons.append("Unknown device")

    # 🔹 Rule 4: Missing address
    if addr1 is None:
        score += 10
        reasons.append("Missing address")

    # 🔹 Rule 5: Mobile device (slightly riskier in some fraud cases)
    if device == "mobile":
        score += 5
        reasons.append("Mobile device usage")

    return {
        "rule_score": score,
        "reasons": reasons
    }


# ==============================
# FINAL RISK SCORING
# ==============================
def compute_risk(ml_probability: float, transaction: Dict) -> Dict:
    """
    Combine ML + rules → final risk score
    """

    # ML contribution (scaled to 0–100)
    ml_score = ml_probability * 100

    # Rule-based contribution
    rule_result = rule_based_checks(transaction)
    rule_score = rule_result["rule_score"]
    reasons = rule_result["reasons"]

    # 🔥 Final weighted score
    final_score = 0.7 * ml_score + 0.3 * rule_score

    final_score = round(final_score, 2)

    # ==============================
    # RISK LEVEL
    # ==============================
    if final_score < 30:
        level = "Low"
    elif final_score < 70:
        level = "Medium"
    else:
        level = "High"

    return {
        "fraud_probability": round(ml_probability, 4),
        "risk_score": final_score,
        "risk_level": level,
        "reasons": reasons
    }