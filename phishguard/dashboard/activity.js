const TIER_LABEL = { high: "HIGH RISK", medium: "NEEDS REVIEW", low: "LOW RISK" };

function timeAgo(isoString) {
  if (!isoString) return "";
  const then = new Date(isoString);
  const diffMs = Date.now() - then.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

async function loadActivity() {
  const res = await fetch("/api/activity");
  const data = await res.json();
  renderLog(data.entries || []);
}

function renderLog(entries) {
  const el = document.getElementById("log-list");
  if (!entries.length) {
    el.innerHTML = `<div class="empty-log">No feedback logged yet — mark an email Correct or Incorrect
      on Overview or Test an Email, then check back here.</div>`;
    return;
  }

  el.innerHTML = entries.map(e => {
    const isCorrect = e.verdict === "correct";
    const icon = isCorrect ? "&#10003;" : "&#10007;";
    const verdictWord = isCorrect ? "confirmed" : "flagged as wrong";
    const tierBadge = e.risk_tier
      ? `<span class="log-badge ${e.risk_tier}">${TIER_LABEL[e.risk_tier] || e.risk_tier}</span>`
      : "";
    return `
      <div class="log-row">
        <div class="log-verdict ${isCorrect ? 'correct' : 'incorrect'}">${icon}</div>
        <div class="log-main">
          <div class="log-line">
            <b>${escapeHtml(e.analyst || "analyst")}</b> ${verdictWord} the verdict on
            "${escapeHtml(e.subject || "an email")}" ${tierBadge}
          </div>
          <div class="log-meta">
            ${e.sender_email ? escapeHtml(e.sender_email) + " · " : ""}
            ${e.risk_score !== undefined && e.risk_score !== null ? e.risk_score.toFixed(1) + "% score · " : ""}
            ${timeAgo(e.timestamp)}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

loadActivity();
