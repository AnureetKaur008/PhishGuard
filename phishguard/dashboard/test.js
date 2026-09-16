const TIER_LABEL = { high: "HIGH RISK", medium: "NEEDS REVIEW", low: "LOW RISK" };

const EXAMPLES = {
  phish: {
    sender_name: "Microsoft Support",
    sender_email: "no-reply@micros0ft-support.com",
    subject: "URGENT: Your account has been locked",
    body: "Dear Customer, your account will be suspended in 24 hours. Click here to verify your password. http://secure-0ffice365.com/verify-account!!!",
  },
  safe: {
    sender_name: "Priya (HR)",
    sender_email: "priya@company.com",
    subject: "Your leave request has been approved",
    body: "Hi Alex, your leave request for next week has been approved by your manager.",
  },
};

function fillForm(data) {
  document.getElementById("f-sender-name").value = data.sender_name;
  document.getElementById("f-sender-email").value = data.sender_email;
  document.getElementById("f-subject").value = data.subject;
  document.getElementById("f-body").value = data.body;
}

document.getElementById("example-phish").addEventListener("click", () => fillForm(EXAMPLES.phish));
document.getElementById("example-safe").addEventListener("click", () => fillForm(EXAMPLES.safe));
document.getElementById("example-clear").addEventListener("click", () => {
  fillForm({ sender_name: "", sender_email: "", subject: "", body: "" });
  document.getElementById("result-panel").classList.remove("show");
});

document.getElementById("analyze-btn").addEventListener("click", async () => {
  const email = {
    sender_name: document.getElementById("f-sender-name").value,
    sender_email: document.getElementById("f-sender-email").value,
    subject: document.getElementById("f-subject").value,
    body: document.getElementById("f-body").value,
  };

  if (!email.body && !email.subject) {
    alert("Add at least a subject or body to analyze.");
    return;
  }

  const loadingNote = document.getElementById("loading-note");
  loadingNote.classList.add("show");
  document.getElementById("result-panel").classList.remove("show");

  try {
    const res = await fetch("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(email),
    });
    const result = await res.json();
    renderResult(result);
  } catch (err) {
    console.error(err);
    alert("Something went wrong analyzing this email.");
  } finally {
    loadingNote.classList.remove("show");
  }
});

function renderResult(result) {
  const header = document.getElementById("result-header");
  header.className = "result-header " + result.risk_tier;

  document.getElementById("result-ring").innerHTML = scoreRingSvg(result.risk_score, result.risk_tier === "medium");
  document.getElementById("result-tier").textContent = TIER_LABEL[result.risk_tier];
  document.getElementById("result-score").textContent =
    result.risk_score.toFixed(1) + "% confidence this is phishing";

  const reasonsEl = document.getElementById("result-reasons");
  reasonsEl.innerHTML = result.reasons.map(r => `
    <div class="reason-item"><span class="reason-dot">&#9679;</span><span>${escapeHtml(r)}</span></div>
  `).join("");

  document.getElementById("result-panel").classList.add("show");
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
