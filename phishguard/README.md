# PhishGuard — AI-Assisted Phishing Triage
### Microsoft Innovate 2026 — Problem #19: The Overloaded Phishing Inbox

A working prototype: reported emails go in, each one gets a **risk score**,
a **plain-English explanation**, and gets **ranked** so the security team
checks the scariest ones first. Anything the model isn't confident about
is sent to a **human**, not auto-decided.

This is the MVP (Phase 1 + Phase 2 from the plan) — fully runnable, no
external services or API keys needed.

---

## Quick start

```bash
cd backend
pip install -r requirements.txt

python data/generate_dataset.py   # creates data/emails.json (synthetic labeled data)
python train_model.py             # trains the classifier, prints precision/recall/F1
python app.py                     # starts the dashboard at http://localhost:5000
```

Open **http://localhost:5000** — you'll land on the welcome screen. Click
**Enter Security Console** to reach the login portal (demo credentials are
shown right on the page: `analyst01` / `phishguard123`). Signing in takes
you to the live queue of reported emails, sorted by risk, with the
model's precision/recall/F1 shown at the top. Click any email to see
exactly why it was flagged, and use the Correct/Incorrect buttons to
simulate the analyst feedback loop. Use **Log out** in the top bar to
return to the welcome screen.

> The login is a demo-only gate (checked in the browser, not a real
> backend auth system) — good enough to show judges an "enterprise"
> access-control story without spending hackathon time building real
> authentication. See "Ideas to extend" below if you want to make it real.

---

## How it works

```
Reported email
      │
      ▼
┌─────────────────┐
│ features.py     │  → pulls out signals: urgency words, credential
│ (feature +      │    requests, lookalike domains, generic greetings,
│  explanation     │    suspicious links, display-name spoofing...
│  extractor)      │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ model.pkl        │  → RandomForest trained on data/emails.json,
│ (classify.py)    │    outputs a 0–100 risk score
└────────┬─────────┘
         │
    ┌────┴─────┐
    │ score ≥ HIGH_THRESHOLD (default 80)   → HIGH RISK, top of queue
    │ score ≥ MEDIUM_THRESHOLD (default 50)  → NEEDS REVIEW, sent to a human
    │ below that                             → LOW RISK
    └──────────┘
         │
         ▼
   four connected pages, all behind the login gate:
   Overview · Test an Email · Analytics · Settings
```

The important design choice: **the reasons shown to the analyst are the
exact same signals used to compute the score** (see `features.py`) — so
the explanation is never a made-up afterthought, it's the real "why."
The thresholds above aren't hardcoded either — they're read live from
`classify.py`'s module state, which the Settings page updates directly,
so a change there instantly changes how every other page classifies.

---

## The four pages (all behind login)

- **Overview** (`/dashboard`) — the reported-email queue, sorted by
  risk, with the "why flagged" modal and analyst feedback buttons.
- **Test an Email** (`/test`) — paste or type any email and get a live
  score + explanation from the same model, instantly. Built for live
  demos: click "Try a phishing example" and hit Analyze in front of judges.
- **Analytics** (`/analytics`) — real numbers derived from the current
  inbox: risk distribution, the most common red flags across all
  reported emails, and the trusted domain list. Nothing here is
  fabricated for the demo — it's all computed from `features.py` output.
- **Settings** (`/settings`) — sliders for the HIGH / NEEDS REVIEW
  thresholds and a textarea for trusted sender domains. Saving updates
  `classify.py` and `features.py`'s in-memory state immediately — go
  back to Overview or Test an Email and the change is already live.
- **Activity Log** (`/activity`) — every time an analyst marks a
  decision Correct or Incorrect (on Overview or Test an Email), it's
  logged here with a timestamp, the analyst's name, and the email it
  was about. This is the audit trail a real security team would need,
  and doubles as the raw material for a "retrain on feedback" story.

Two extra touches worth knowing about:
- **Simulate Incoming Email** (button on Overview) — picks a random
  email from a small template pool, sends it through the real
  `/api/classify` pipeline, and drops it into the live queue with a
  highlight animation. Good for making a demo feel live instead of
  static.
- **Score ring** — the circular progress indicator on the "why
  flagged" modal (Overview) and the Test an Email result panel is a
  shared component (`scoreRingSvg()` in `auth.js`), so both look
  identical and stay in sync if you restyle one.

---

## Project structure

```
phishguard/
├── backend/
│   ├── data/
│   │   ├── generate_dataset.py   # builds the synthetic training set
│   │   ├── emails.json           # generated training data (180+ emails)
│   │   └── sample_inbox.json     # the 12 "currently reported" emails shown in the demo
│   ├── features.py               # feature extraction + red-flag reasons
│   ├── train_model.py            # trains RandomForest, prints precision/recall/F1
│   ├── classify.py               # scores a single email + confidence routing
│   ├── model.pkl                 # trained model (generated by train_model.py)
│   ├── metrics.json              # last training run's metrics (generated)
│   ├── app.py                    # Flask server: dashboard + API
│   └── requirements.txt
└── dashboard/
    ├── welcome.html               # landing screen
    ├── welcome.css
    ├── login.html                 # analyst login portal (demo auth)
    ├── login.css
    ├── login.js
    ├── auth.js                    # shared session/logout/clock logic for every page below
    ├── index.html                 # Overview — the triage queue
    ├── style.css                  # shared theme + sidebar layout
    ├── script.js                  # Overview page logic
    ├── test.html                  # Test an Email — live classifier
    ├── test.js
    ├── analytics.html             # Analytics — real derived stats
    ├── analytics.js
    ├── settings.html              # Settings — tunable thresholds + trusted domains
    ├── settings.js
    ├── activity.html              # Activity Log — feedback audit trail
    └── activity.js
```

---

## API (for extending it / hooking up a real mail source later)

- `GET /api/inbox` — classifies `sample_inbox.json` and returns everything
  sorted by risk, plus the queue stats and model metrics.
- `POST /api/classify` — send one email as JSON:
  ```json
  { "sender_name": "IT Support", "sender_email": "it@company.com",
    "subject": "...", "body": "..." }
  ```
  returns `{ risk_score, risk_tier, needs_human_review, reasons: [...] }`
- `POST /api/feedback` — `{ "email_id": "...", "verdict": "correct" | "incorrect" }`
  (logged in memory for the demo — this is the hook for the "retrain on
  feedback" story if you want to build it further)
- `GET /api/analytics` — aggregate red-flag frequency + risk distribution
  across the current inbox, used by the Analytics page.
- `GET /api/settings` / `POST /api/settings` — read or update the HIGH /
  MEDIUM thresholds and the trusted domain list. A POST here changes
  `classify.py` and `features.py`'s in-memory state immediately, so
  every other page (Overview, Test an Email, Analytics) reflects it on
  the very next request — no restart needed.
- `GET /api/activity` — the feedback log (every Correct/Incorrect
  click), most recent first.

---

## What to say on stage

> "A company with 5,000 employees has one problem: people are reporting
> phishing emails faster than the security team can check them."

Then show the dashboard: 12 reported emails → 5 high risk, 1 needs human
review, 6 safe — sorted automatically. Click into a high-risk one and
walk through the reasons. That's the whole demo, and it's real, running
code — not mockup screenshots.

## Ideas to extend if you have time left

- Swap `data/emails.json` for a real public phishing dataset (e.g.
  Nazario phishing corpus + Enron ham) for a stronger accuracy story.
- Wire `/api/feedback` into an actual retraining step.
- Add a small "analyst notes" field for each reviewed email.
- Add authentication so the dashboard isn't wide open (not needed for
  a hackathon demo, but worth mentioning if judges ask about production
  readiness).
