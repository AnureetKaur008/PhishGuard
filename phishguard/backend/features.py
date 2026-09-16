"""
features.py
------------
Turns a raw reported email (sender name, sender email, subject, body)
into:
  1. A numeric feature vector -> fed to the ML risk classifier
  2. A list of human-readable "red flags" -> used for the explanation

Keeping these in one place means the score and the explanation always
agree with each other (the reasons ARE the features that drove the score).
"""

import re

URGENCY_WORDS = [
    "urgent", "immediately", "act now", "final notice", "suspend",
    "24 hours", "expire", "verify now", "restricted", "locked",
    "closure", "deactivat",
]

CREDENTIAL_WORDS = [
    "password", "verify your", "confirm your", "login credentials",
    "account details", "social security", "bank account", "employee id",
    "re-enter your password", "ssn",
]

SUSPICIOUS_TLDS = [".xyz", ".top", ".club", ".ru", ".info", ".click", ".work"]

GENERIC_GREETINGS = ["dear customer", "dear user", "dear valued customer", "dear employee"]

# A tiny whitelist of "known good" company domains for this demo. In a real
# deployment this would be the org's verified sender domains.
TRUSTED_DOMAINS = {
    "company.com", "microsoft.com", "google.com", "slack.com",
    "github.com", "zoom.us", "workday.com", "atlassian.com",
}

URL_REGEX = re.compile(r"https?://([^\s/]+)")
IP_URL_REGEX = re.compile(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def _domain_of(url_host: str) -> str:
    return url_host.lower()


def _looks_like_lookalike(domain: str) -> bool:
    """Very small heuristic: digits standing in for letters, or a trusted
    brand name glued to an unrelated domain."""
    brand_markers = ["microsoft", "paypal", "apple", "google", "office365",
                      "bankofamerica", "hr-", "payroll", "it-helpdesk", "login"]
    has_digit_swap = bool(re.search(r"(micr0soft|g00gle|paypa1|0ffice)", domain))
    has_brand_marker = any(b in domain for b in brand_markers)
    is_trusted = domain in TRUSTED_DOMAINS
    return (has_digit_swap or has_brand_marker) and not is_trusted


def extract(email: dict) -> dict:
    """email: {sender_name, sender_email, subject, body}
    Returns: {features: {...numeric...}, reasons: [str, ...]}
    """
    sender_name = (email.get("sender_name") or "").strip()
    sender_email = (email.get("sender_email") or "").strip().lower()
    subject = (email.get("subject") or "").strip()
    body = (email.get("body") or "").strip()

    text = f"{subject}\n{body}".lower()
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""

    reasons = []
    feats = {}

    # --- Urgency language ---
    urgency_hits = [w for w in URGENCY_WORDS if w in text]
    feats["urgency_count"] = len(urgency_hits)
    if urgency_hits:
        reasons.append("Uses urgent or scary language (e.g. \"%s\")" % urgency_hits[0])

    # --- Credential / sensitive-info requests ---
    cred_hits = [w for w in CREDENTIAL_WORDS if w in text]
    feats["credential_request_count"] = len(cred_hits)
    if cred_hits:
        reasons.append("Asks the reader to enter a password or personal/account details")

    # --- Links ---
    urls = URL_REGEX.findall(text)
    feats["num_links"] = len(urls)
    feats["has_ip_url"] = 1 if IP_URL_REGEX.search(text) else 0
    if feats["has_ip_url"]:
        reasons.append("Link points to a raw IP address instead of a normal domain")

    suspicious_tld_hit = any(any(d.endswith(tld) for tld in SUSPICIOUS_TLDS) for d in urls)
    feats["suspicious_tld"] = 1 if suspicious_tld_hit else 0
    if suspicious_tld_hit:
        reasons.append("Link uses an unusual, high-risk domain ending (e.g. .xyz/.top/.club)")

    lookalike_link_hit = any(_looks_like_lookalike(d) for d in urls)
    feats["lookalike_link"] = 1 if lookalike_link_hit else 0
    if lookalike_link_hit:
        reasons.append("Link domain looks like a fake/lookalike version of a real company site")

    # --- Sender domain trust ---
    feats["sender_domain_trusted"] = 1 if sender_domain in TRUSTED_DOMAINS else 0
    sender_lookalike = _looks_like_lookalike(sender_domain)
    feats["sender_lookalike"] = 1 if sender_lookalike else 0
    if sender_lookalike:
        reasons.append(f"Sender domain \"{sender_domain}\" looks fake or unrelated to the claimed sender")

    # --- Display-name spoofing: display name mentions a brand not in the domain ---
    brand_words = ["microsoft", "paypal", "apple", "google", "office 365",
                    "bank", "hr", "it security", "helpdesk", "payroll"]
    name_lower = sender_name.lower()
    name_claims_brand = any(b in name_lower for b in brand_words)
    feats["display_name_brand_mismatch"] = 1 if (name_claims_brand and not feats["sender_domain_trusted"]) else 0
    if feats["display_name_brand_mismatch"]:
        reasons.append(f"Display name (\"{sender_name}\") claims to be a trusted org, but the domain doesn't match")

    # --- Generic greeting (mass phishing signal) ---
    greeting_hit = any(g in text for g in GENERIC_GREETINGS)
    feats["generic_greeting"] = 1 if greeting_hit else 0
    if greeting_hit:
        reasons.append("Uses a generic greeting (\"Dear Customer/User\") instead of your name")

    # --- Exclamation / pressure punctuation ---
    feats["exclamation_count"] = body.count("!")

    # --- Body length (very short, link-heavy emails are riskier) ---
    feats["body_length"] = len(body)

    return {"features": feats, "reasons": reasons}


FEATURE_ORDER = [
    "urgency_count", "credential_request_count", "num_links", "has_ip_url",
    "suspicious_tld", "lookalike_link", "sender_domain_trusted",
    "sender_lookalike", "display_name_brand_mismatch", "generic_greeting",
    "exclamation_count", "body_length",
]


def to_vector(feats: dict):
    return [feats.get(k, 0) for k in FEATURE_ORDER]
