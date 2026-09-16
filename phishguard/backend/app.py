"""
app.py
-------
PhishGuard backend API + dashboard server.

Routes:
  GET  /                   -> welcome / landing screen
  GET  /login               -> analyst login portal (demo credentials shown on the page)
  GET  /dashboard           -> the triage dashboard (requires a client-side "login" first)
  GET  /api/inbox           -> classifies the sample reported-emails inbox,
                               returns everything sorted by risk score + stats
  POST /api/classify        -> classify a single email you send as JSON
  POST /api/feedback        -> record analyst feedback (correct/incorrect) - in-memory demo only
  GET  /api/activity        -> the feedback log, most recent first
  GET  /api/analytics       -> aggregate red-flag frequency + risk distribution across the inbox
  GET  /api/settings        -> current risk thresholds + trusted domain list
  POST /api/settings        -> update thresholds / trusted domains (applies immediately)

Run:
    pip install -r requirements.txt
    python train_model.py      # only needed once, or after changing features.py
    python app.py
    -> open http://localhost:5000
"""

import json
import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

import classify
import features
from classify import classify_email

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_DIR = os.path.join(BASE_DIR, "..", "dashboard")

app = Flask(__name__, static_folder=None)

# in-memory feedback store, just for the demo ("analyst clicked correct/incorrect")
FEEDBACK_LOG = []


def load_inbox():
    path = os.path.join(BASE_DIR, "data", "sample_inbox.json")
    with open(path) as f:
        return json.load(f)


def load_metrics():
    path = os.path.join(BASE_DIR, "metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"precision": None, "recall": None, "f1": None, "false_positive_rate": None}


@app.route("/")
def welcome():
    return send_from_directory(DASHBOARD_DIR, "welcome.html")


@app.route("/login")
def login():
    return send_from_directory(DASHBOARD_DIR, "login.html")


@app.route("/dashboard")
def dashboard():
    return send_from_directory(DASHBOARD_DIR, "index.html")


@app.route("/test")
def test_page():
    return send_from_directory(DASHBOARD_DIR, "test.html")


@app.route("/analytics")
def analytics_page():
    return send_from_directory(DASHBOARD_DIR, "analytics.html")


@app.route("/settings")
def settings_page():
    return send_from_directory(DASHBOARD_DIR, "settings.html")


@app.route("/activity")
def activity_page():
    return send_from_directory(DASHBOARD_DIR, "activity.html")


@app.route("/<path:filename>")
def dashboard_assets(filename):
    return send_from_directory(DASHBOARD_DIR, filename)


@app.route("/api/inbox")
def api_inbox():
    inbox = load_inbox()
    results = [classify_email(e) for e in inbox]
    # keep original reported_by / reported_at metadata for the UI
    by_id = {e["id"]: e for e in inbox}
    for r in results:
        meta = by_id.get(r["id"], {})
        r["reported_by"] = meta.get("reported_by")
        r["reported_at"] = meta.get("reported_at")

    results.sort(key=lambda r: r["risk_score"], reverse=True)

    stats = {
        "total": len(results),
        "high": sum(1 for r in results if r["risk_tier"] == "high"),
        "medium": sum(1 for r in results if r["risk_tier"] == "medium"),
        "low": sum(1 for r in results if r["risk_tier"] == "low"),
    }

    return jsonify({
        "emails": results,
        "stats": stats,
        "model_metrics": load_metrics(),
    })


@app.route("/api/classify", methods=["POST"])
def api_classify():
    email = request.get_json(force=True)
    if not email:
        return jsonify({"error": "Send an email as JSON: {sender_name, sender_email, subject, body}"}), 400
    return jsonify(classify_email(email))


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    payload = request.get_json(force=True) or {}
    entry = {
        "analyst": payload.get("analyst") or "analyst",
        "verdict": payload.get("verdict"),
        "email_id": payload.get("email_id"),
        "subject": payload.get("subject"),
        "sender_email": payload.get("sender_email"),
        "risk_tier": payload.get("risk_tier"),
        "risk_score": payload.get("risk_score"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    FEEDBACK_LOG.append(entry)
    return jsonify({"ok": True, "total_feedback": len(FEEDBACK_LOG)})


@app.route("/api/activity")
def api_activity():
    return jsonify({"entries": list(reversed(FEEDBACK_LOG))})


# Human-readable labels for the boolean/count red-flag features, used by
# the Analytics page to show "how many reported emails had this signal".
RED_FLAG_LABELS = {
    "urgency_count": "Uses urgent or scary language",
    "credential_request_count": "Asks for a password / personal details",
    "lookalike_link": "Link looks like a fake/lookalike domain",
    "sender_lookalike": "Sender domain looks fake or unrelated",
    "display_name_brand_mismatch": "Display name claims a brand the domain doesn't match",
    "generic_greeting": "Uses a generic greeting (\"Dear Customer\")",
    "suspicious_tld": "Link uses a high-risk domain ending",
    "has_ip_url": "Link points to a raw IP address",
}


@app.route("/api/analytics")
def api_analytics():
    inbox = load_inbox()
    flag_counts = {k: 0 for k in RED_FLAG_LABELS}
    tier_counts = {"high": 0, "medium": 0, "low": 0}

    for email in inbox:
        result = classify_email(email)
        tier_counts[result["risk_tier"]] += 1

        feats = features.extract(email)["features"]
        for key in RED_FLAG_LABELS:
            val = feats.get(key, 0)
            if val:
                flag_counts[key] += 1

    red_flags = sorted(
        [{"label": RED_FLAG_LABELS[k], "count": v} for k, v in flag_counts.items()],
        key=lambda r: -r["count"]
    )

    return jsonify({
        "total": len(inbox),
        "tier_counts": tier_counts,
        "red_flags": red_flags,
        "model_metrics": load_metrics(),
        "trusted_domains": sorted(features.TRUSTED_DOMAINS),
        "thresholds": {
            "high": classify.HIGH_THRESHOLD,
            "medium": classify.MEDIUM_THRESHOLD,
        },
    })


@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    return jsonify({
        "high_threshold": classify.HIGH_THRESHOLD,
        "medium_threshold": classify.MEDIUM_THRESHOLD,
        "trusted_domains": sorted(features.TRUSTED_DOMAINS),
    })


@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    payload = request.get_json(force=True) or {}

    high = payload.get("high_threshold")
    medium = payload.get("medium_threshold")
    domains = payload.get("trusted_domains")

    if high is not None:
        classify.HIGH_THRESHOLD = int(high)
    if medium is not None:
        classify.MEDIUM_THRESHOLD = int(medium)
    if domains is not None:
        # mutate the same set object in place so features.extract() (which
        # references the module-level TRUSTED_DOMAINS directly) sees the update
        features.TRUSTED_DOMAINS.clear()
        features.TRUSTED_DOMAINS.update(
            d.strip().lower() for d in domains if d.strip()
        )

    return jsonify({
        "ok": True,
        "high_threshold": classify.HIGH_THRESHOLD,
        "medium_threshold": classify.MEDIUM_THRESHOLD,
        "trusted_domains": sorted(features.TRUSTED_DOMAINS),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
