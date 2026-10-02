let ALL_EMAILS = [];
let ACTIVE_FILTER = "all";

const TIER_LABEL = { high: "HIGH RISK", medium: "NEEDS REVIEW", low: "LOW RISK" };

const SIMULATION_POOL = [
  {
    sender_name: "Account Verification",
    sender_email: "no-reply@secure-login-alert.xyz",
    subject: "Immediate action: unusual sign-in blocked",
    body: "Dear User, we blocked a sign-in from a new device. Verify your password immediately to restore access. http://secure-login-alert.xyz/verify-account!!!",
  },
  {
    sender_name: "Zoom",
    sender_email: "no-reply@zoom.us",
    subject: "Your recording is ready to view",
    body: "Your recording from today's standup is now available on the internal drive. https://zoom.us/dashboard",
  },
  {
    sender_name: "Finance Team",
    sender_email: "finance@company.com",
    subject: "Expense report reminder",
    body: "Hi, just a reminder to submit your expense report for this month by Friday.",
  },
  {
    sender_name: "IT Helpdesk",
    sender_email: "no-reply@it-helpdesk-support.info",
    subject: "Your mailbox is almost full",
    body: "Dear Customer, your mailbox storage is nearly full. Confirm your login credentials now to avoid losing access to your emails. http://it-helpdesk-support.info/confirm-id",
  },
  {
    sender_name: "GitHub",
    sender_email: "notifications@github.com",
    subject: "New review requested on your pull request",
    body: "Meera requested changes on your pull request. Please address the comments when you get a chance.",
  },
  {
    sender_name: "HR Payroll Update",
    sender_email: "no-reply@payroll-update-request.ru",
    subject: "Final Notice: payroll account suspension pending",
    body: "This is your final notice. Confirm your bank account details immediately to avoid permanent closure of your payroll account. http://payroll-update-request.ru/verify-account!!!",
  },
];

async function loadInbox() {
  try {
    const res = await fetch("/api/inbox");
    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }
    const data = await res.json();
    ALL_EMAILS = data.emails;
    renderMetrics(data.model_metrics);
    renderStats(data.stats);
    renderQueue();
  } catch (err) {
    console.error("Failed to load inbox:", err);
    document.getElementById("queue").innerHTML =
      `<div class="empty-state">Couldn't load the email queue (${err.message}).
       Check that the server is running correctly and try refreshing.</div>`;
  }
}

function recomputeStats() {
  return {
    total: ALL_EMAILS.length,
    high: ALL_EMAILS.filter(e => e.risk_tier === "high").length,
    medium: ALL_EMAILS.filter(e => e.risk_tier === "medium").length,
    low: ALL_EMAILS.filter(e => e.risk_tier === "low").length,
  };
}

async function simulateIncoming() {
  const btn = document.getElementById("simulate-btn");
  btn.disabled = true;
  btn.textContent = "Simulating…";

  const template = SIMULATION_POOL[Math.floor(Math.random() * SIMULATION_POOL.length)];
  const employeeNum = Math.floor(Math.random() * 280) + 1;

  try {
    const res = await fetch("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(template),
    });
    const result = await res.json();
    result.id = "sim_" + Date.now();
    result.reported_by = "employee_" + String(employeeNum).padStart(3, "0");
    result.reported_at = new Date().toISOString();
    result._justAdded = true;

    ALL_EMAILS.forEach(e => { e._justAdded = false; });
    ALL_EMAILS.unshift(result);

    renderStats(recomputeStats());
    renderQueue();

    const newRow = document.querySelector(`.email-row[data-id="${result.id}"]`);
    if (newRow) newRow.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (err) {
    console.error("Simulate failed", err);
    alert("Couldn't simulate a new email — check the server is running.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Simulate Incoming Email";
  }
}

function renderMetrics(m) {
  const el = document.getElementById("model-metrics");
  const pct = (v) => (v === null || v === undefined) ? "—" : Math.round(v * 100) + "%";
  el.innerHTML = `
    <div class="metric-pill"><div class="val">${pct(m.precision)}</div><div class="lbl">Precision</div></div>
    <div class="metric-pill"><div class="val">${pct(m.recall)}</div><div class="lbl">Recall</div></div>
    <div class="metric-pill"><div class="val">${pct(m.f1)}</div><div class="lbl">F1 Score</div></div>
  `;
}

function renderStats(stats) {
  const el = document.getElementById("stats-row");
  el.innerHTML = `
    <div class="stat-card">
      <div class="num">${stats.total}</div>
      <div class="lbl">Total reported emails</div>
    </div>
    <div class="stat-card high">
      <div class="num">${stats.high}</div>
      <div class="lbl">High risk — flagged first</div>
    </div>
    <div class="stat-card medium">
      <div class="num">${stats.medium}</div>
      <div class="lbl">Needs human review</div>
    </div>
    <div class="stat-card low">
      <div class="num">${stats.low}</div>
      <div class="lbl">Low risk</div>
    </div>
  `;
}

function renderQueue() {
  const el = document.getElementById("queue");
  const filtered = ACTIVE_FILTER === "all"
    ? ALL_EMAILS
    : ALL_EMAILS.filter(e => e.risk_tier === ACTIVE_FILTER);

  if (filtered.length === 0) {
    el.innerHTML = `<div class="empty-state">No emails in this bucket right now.</div>`;
    return;
  }

  el.innerHTML = filtered.map(e => `
    <div class="email-row ${e._justAdded ? 'row-new' : ''}" data-id="${e.id}">
      <div class="risk-badge ${e.risk_tier}">${TIER_LABEL[e.risk_tier]}</div>
      <div class="email-main">
        <div class="email-subject">${escapeHtml(e.subject)}</div>
        <div class="email-sender">${escapeHtml(e.sender_name)} &lt;${escapeHtml(e.sender_email)}&gt;</div>
      </div>
      <div class="email-score">${e.risk_score.toFixed(0)}%</div>
      <div class="email-arrow">›</div>
    </div>
  `).join("");

  el.querySelectorAll(".email-row").forEach(row => {
    row.addEventListener("click", () => openModal(row.dataset.id));
  });
}

document.getElementById("filters").addEventListener("click", (ev) => {
  const btn = ev.target.closest(".filter-btn");
  if (!btn) return;
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  ACTIVE_FILTER = btn.dataset.tier;
  renderQueue();
});

function openModal(id) {
  const e = ALL_EMAILS.find(x => x.id === id);
  if (!e) return;
  const backdrop = document.getElementById("modal-backdrop");
  const modal = document.getElementById("modal");

  modal.innerHTML = `
    <div class="modal-header ${e.risk_tier}">
      <div class="score-ring-wrap">
        ${scoreRingSvg(e.risk_score, e.risk_tier === "medium")}
        <div>
          <div class="tier-label">${TIER_LABEL[e.risk_tier]}</div>
          <div class="score-label">${e.risk_score.toFixed(1)}% confidence this is phishing</div>
        </div>
      </div>
    </div>
    <div class="modal-body">
      <h3>${escapeHtml(e.subject)}</h3>
      <div class="modal-meta">
        From: ${escapeHtml(e.sender_name)} &lt;${escapeHtml(e.sender_email)}&gt;
        ${e.reported_by ? " · Reported by " + escapeHtml(e.reported_by) : ""}
      </div>
      <div class="modal-snippet">${escapeHtml(e.body)}</div>

      <div class="reasons-title">Why PhishGuard flagged this</div>
      ${e.reasons.map(r => `
        <div class="reason-item"><span class="reason-dot">&#9679;</span><span>${escapeHtml(r)}</span></div>
      `).join("")}

      <div class="modal-actions">
        <button class="btn btn-correct" data-verdict="correct">&#10003; Correct</button>
        <button class="btn btn-incorrect" data-verdict="incorrect">&#10007; Incorrect</button>
      </div>
      <div class="feedback-toast" id="feedback-toast">Thanks — feedback logged for retraining.</div>
      <button class="btn-close" id="close-modal">Close</button>
    </div>
  `;

  modal.querySelectorAll("[data-verdict]").forEach(btn => {
    btn.addEventListener("click", () => sendFeedback(e, btn.dataset.verdict));
  });
  modal.querySelector("#close-modal").addEventListener("click", closeModal);

  backdrop.classList.add("open");
}

function closeModal() {
  document.getElementById("modal-backdrop").classList.remove("open");
}

document.getElementById("modal-backdrop").addEventListener("click", (ev) => {
  if (ev.target.id === "modal-backdrop") closeModal();
});

async function sendFeedback(email, verdict) {
  try {
    await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email_id: email.id,
        verdict,
        analyst: sessionStorage.getItem("pg_analyst") || "analyst",
        subject: email.subject,
        sender_email: email.sender_email,
        risk_tier: email.risk_tier,
        risk_score: email.risk_score,
      }),
    });
  } catch (err) {
    console.error("Feedback failed", err);
  }
  const toast = document.getElementById("feedback-toast");
  if (toast) toast.style.display = "block";
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

loadInbox();

const simulateBtn = document.getElementById("simulate-btn");
if (simulateBtn) simulateBtn.addEventListener("click", simulateIncoming);
