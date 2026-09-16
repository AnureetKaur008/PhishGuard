"""
classify.py
------------
Loads the trained model and classifies a single reported email into:
  - risk_score      (0-100, how likely this is phishing)
  - risk_tier        ("high" | "medium" | "low")
  - reasons          (human-readable red flags, from features.py)
  - needs_human_review (bool)

Confidence-threshold routing (matches the "enterprise" requirement):
  score >= 80              -> HIGH risk, auto-flagged
  50 <= score < 80          -> MEDIUM risk, sent to a human for review
  score < 50                -> LOW risk

These thresholds are intentionally easy to tune — see HIGH_THRESHOLD /
MEDIUM_THRESHOLD below.
"""

import joblib
from features import extract, to_vector

HIGH_THRESHOLD = 80
MEDIUM_THRESHOLD = 50

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load("model.pkl")
    return _model


def classify_email(email: dict) -> dict:
    """email: {id?, sender_name, sender_email, subject, body}"""
    extraction = extract(email)
    feats = extraction["features"]
    reasons = extraction["reasons"]

    model = _get_model()
    proba = model.predict_proba([to_vector(feats)])[0]
    # proba[1] = probability of class "phishing"
    score = round(float(proba[1]) * 100, 1)

    if score >= HIGH_THRESHOLD:
        tier = "high"
    elif score >= MEDIUM_THRESHOLD:
        tier = "medium"
    else:
        tier = "low"

    if not reasons:
        reasons = ["No suspicious signals found — sender domain and content look normal"]

    return {
        "id": email.get("id"),
        "sender_name": email.get("sender_name"),
        "sender_email": email.get("sender_email"),
        "subject": email.get("subject"),
        "body": email.get("body"),
        "risk_score": score,
        "risk_tier": tier,
        "needs_human_review": tier == "medium",
        "reasons": reasons,
    }


if __name__ == "__main__":
    # Quick manual test
    sample = {
        "id": "test_1",
        "sender_name": "Microsoft Support",
        "sender_email": "no-reply@micros0ft-support.com",
        "subject": "URGENT: Your account has been locked",
        "body": "Dear Customer, your account will be suspended in 24 hours. "
                "Click here to verify your password. http://secure-0ffice365.com/verify-account!!!",
    }
    import json
    print(json.dumps(classify_email(sample), indent=2))
