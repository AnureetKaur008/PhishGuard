"""
generate_dataset.py
--------------------
Creates a synthetic (but realistic-looking) labeled dataset of reported
emails: half phishing, half safe. This stands in for a public phishing
dataset (e.g. Nazario / PhishTank / Enron-safe-mail samples) so the team
can train and demo PhishGuard without needing internet access.

Run:
    python generate_dataset.py

Output:
    emails.json   (list of {id, sender, subject, body, label})
"""

import json
import random

random.seed(42)

# ---------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------

LEGIT_DOMAINS = [
    "company.com", "microsoft.com", "google.com", "slack.com",
    "github.com", "zoom.us", "workday.com", "atlassian.com",
]

LOOKALIKE_DOMAINS = [
    "micros0ft-support.com", "paypa1-secure.com", "appleid-verify.net",
    "secure-0ffice365.com", "g00gle-alerts.com", "hr-portal-update.xyz",
    "bank0famerica-alert.com", "verify-account-now.top", "login-secure.club",
    "it-helpdesk-support.info", "payroll-update-request.ru",
]

SAFE_SENDER_NAMES = [
    "Priya (HR)", "GitHub", "Slack", "Zoom", "Workday Notifications",
    "IT Support Desk", "Finance Team", "Atlassian", "Google Calendar",
    "Manager - Raj Mehta",
]

PHISH_SENDER_NAMES = [
    "Microsoft Support", "IT Security Team", "PayPal Account Team",
    "Apple ID Support", "HR Payroll Update", "Bank Security Alert",
    "Office 365 Admin", "Account Verification", "Helpdesk Support",
]

URGENCY_PHRASES = [
    "Your account will be suspended in 24 hours",
    "Immediate action required",
    "Act now to avoid permanent deactivation",
    "This is your final notice",
    "Your access expires in 30 minutes",
    "Failure to respond will result in account closure",
    "Urgent: verify your identity today",
]

CREDENTIAL_PHRASES = [
    "click here to verify your password",
    "confirm your login credentials",
    "enter your account details to continue",
    "re-enter your password to unlock your account",
    "provide your employee ID and password",
    "verify your bank account details",
    "confirm your social security number",
]

SAFE_SUBJECTS = [
    "Weekly team sync notes",
    "Your leave request has been approved",
    "Reminder: submit your timesheet by Friday",
    "New comment on your pull request",
    "Meeting invite: Q3 planning",
    "Your Zoom recording is ready",
    "Payslip for this month is available",
    "Welcome to the new onboarding portal",
    "Calendar invite: 1:1 with your manager",
    "Slack workspace update notes",
]

PHISH_SUBJECTS = [
    "URGENT: Your account has been locked",
    "Action Required: Verify your Office 365 account",
    "Your password will expire today - verify now",
    "Security Alert: unusual sign-in activity detected",
    "HR Payroll Update - action needed",
    "Your mailbox is almost full, click to resolve",
    "Final Notice: account suspension pending",
    "Invoice attached - payment overdue, verify now",
    "IT Helpdesk: confirm your credentials to continue",
    "Your PayPal account has been limited",
]

SAFE_BODY_TEMPLATES = [
    "Hi team, attaching the notes from today's sync. Let me know if I missed anything.",
    "Hi {name}, your leave request for next week has been approved by your manager.",
    "Hi, this is a friendly reminder to submit your timesheet before end of day Friday.",
    "{name} left a comment on your pull request: 'Looks good, just fix the lint warnings.'",
    "You're invited to the Q3 planning meeting on Thursday at 3 PM. See the calendar link inside our internal portal.",
    "Your Zoom recording from yesterday's meeting is now available on the internal drive.",
    "Hi {name}, your payslip for this month has been generated and is available on the HR portal.",
    "Welcome aboard! Here is your onboarding checklist for your first week.",
    "Reminder: 1:1 with your manager is scheduled for tomorrow at 10 AM.",
    "Here are this week's Slack workspace updates and new channel guidelines.",
]

PHISH_BODY_TEMPLATES = [
    "Dear Customer, {urgency}. {credential} at the link below to keep your account active.",
    "Dear User, we detected unusual activity on your account. {credential} immediately to prevent suspension.",
    "Hello, your password expires today. {urgency}. {credential} using the secure link provided.",
    "Attention: your mailbox storage is full. {credential} to avoid losing access to your emails.",
    "Dear Employee, HR requires you to {credential} to process this month's payroll. {urgency}.",
    "Your invoice is overdue. Please {credential} to release your account from hold. {urgency}.",
    "Security Notice: {urgency}. Please {credential} to restore full access to your account.",
    "Dear Valued Customer, {urgency}. Click the link and {credential} to avoid permanent closure.",
]

NAMES = ["Alex", "Priya", "Sam", "Rohit", "Meera", "Jordan", "Ananya", "Kabir"]


def make_link(domain, suspicious=False):
    if suspicious:
        paths = ["/verify-account", "/secure-login", "/update-info", "/confirm-id"]
        return f"http://{domain}{random.choice(paths)}"
    return f"https://{domain}/dashboard"


def gen_safe(i):
    name = random.choice(NAMES)
    sender_name = random.choice(SAFE_SENDER_NAMES)
    domain = random.choice(LEGIT_DOMAINS)
    subject = random.choice(SAFE_SUBJECTS)
    body = random.choice(SAFE_BODY_TEMPLATES).format(name=name)
    if random.random() < 0.4:
        body += f" Link: {make_link(domain)}"
    return {
        "id": f"safe_{i}",
        "sender_name": sender_name,
        "sender_email": f"{sender_name.split()[0].lower()}@{domain}",
        "subject": subject,
        "body": body,
        "label": "safe",
    }


def gen_phish(i):
    sender_name = random.choice(PHISH_SENDER_NAMES)
    lookalike = random.choice(LOOKALIKE_DOMAINS)
    subject = random.choice(PHISH_SUBJECTS)
    urgency = random.choice(URGENCY_PHRASES)
    credential = random.choice(CREDENTIAL_PHRASES)
    body = random.choice(PHISH_BODY_TEMPLATES).format(urgency=urgency, credential=credential)
    body += f" {make_link(lookalike, suspicious=True)}"
    if random.random() < 0.5:
        body += "!!!"
    return {
        "id": f"phish_{i}",
        "sender_name": sender_name,
        "sender_email": f"no-reply@{lookalike}",
        "subject": subject,
        "body": body,
        "label": "phishing",
    }


def gen_ambiguous(i):
    """Borderline emails — legit-ish domain but a couple of soft red flags,
    or phishing-ish wording but no lookalike domain. These are what should
    land in the "needs human review" bucket."""
    style = random.choice(["soft_phish", "jumpy_safe"])
    if style == "soft_phish":
        # Real-looking domain, but urgent/credential-ish wording slipped in
        domain = random.choice(LEGIT_DOMAINS)
        sender_name = random.choice(["IT Support Desk", "Finance Team", "Workday Notifications"])
        subject = random.choice([
            "Reminder: update your password before it expires",
            "Action needed: confirm your details for payroll",
            "Please verify your account information",
        ])
        body = (
            "Hi, as part of a routine security update, please confirm your login "
            f"details before Friday. {make_link(domain)}"
        )
        return {
            "id": f"ambig_{i}",
            "sender_name": sender_name,
            "sender_email": f"noreply@{domain}",
            "subject": subject,
            "body": body,
            "label": "safe",
        }
    else:
        # Lookalike-ish domain but calm, low-pressure wording
        lookalike = random.choice(LOOKALIKE_DOMAINS)
        sender_name = random.choice(SAFE_SENDER_NAMES)
        subject = random.choice([
            "Your monthly statement is ready",
            "Document shared with you",
            "New notification from your account",
        ])
        body = f"Hello, a new document has been shared with you. {make_link(lookalike)}"
        return {
            "id": f"ambig_{i}",
            "sender_name": sender_name,
            "sender_email": f"updates@{lookalike}",
            "subject": subject,
            "body": body,
            "label": "phishing",
        }


def main():
    n_each = 90
    n_ambig = 24
    rows = (
        [gen_safe(i) for i in range(n_each)]
        + [gen_phish(i) for i in range(n_each)]
        + [gen_ambiguous(i) for i in range(n_ambig)]
    )
    random.shuffle(rows)
    with open("emails.json", "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Wrote {len(rows)} emails ({n_each} safe, {n_each} phishing, "
          f"{n_ambig} ambiguous) to emails.json")


if __name__ == "__main__":
    main()
