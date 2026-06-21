from __future__ import annotations

POSITIVE = {"lancar", "cepat", "bagus", "mudah", "responsif", "oke", "mantap", "puas"}
NEGATIVE = {"error", "crash", "gagal", "lemot", "lambat", "nyangkut", "buruk", "kesel", "susah", "masalah"}

TOPIC_RULES = {
    "login_otp": {"login", "otp", "password"},
    "order_execution": {"order", "beli", "jual", "nyangkut", "reject"},
    "app_stability": {"error", "crash", "bug"},
    "performance_speed": {"lemot", "lambat", "cepat", "lancar"},
    "customer_service": {"cs", "customer", "service", "respon", "responsif"},
    "fees_commission": {"fee", "komisi", "biaya"},
}


def classify_rule_based(cleaned_text: str) -> dict:
    tokens = set(cleaned_text.split())
    pos = len(tokens & POSITIVE)
    neg = len(tokens & NEGATIVE)
    if pos > neg:
        label, score = "positive", min(1.0, 0.35 + 0.2 * pos)
    elif neg > pos:
        label, score = "negative", max(-1.0, -0.35 - 0.2 * neg)
    else:
        label, score = "neutral", 0.0
    confidence = min(0.95, 0.55 + 0.1 * abs(pos - neg)) if label != "neutral" else 0.6
    topics = [name for name, words in TOPIC_RULES.items() if tokens & words]
    return {"label": label, "score": score, "confidence": confidence, "topics": topics}
