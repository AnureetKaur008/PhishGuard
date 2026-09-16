async function loadAnalytics() {
  const res = await fetch("/api/analytics");
  const data = await res.json();

  renderMetrics(data.model_metrics);
  renderTierBars(data.tier_counts, data.total);
  renderFlagList(data.red_flags, data.total);
  renderDomains(data.trusted_domains);
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

function renderTierBars(tierCounts, total) {
  const el = document.getElementById("tier-bars");
  const rows = [
    { key: "high", label: "High Risk" },
    { key: "medium", label: "Needs Review" },
    { key: "low", label: "Low Risk" },
  ];
  el.innerHTML = rows.map(row => {
    const count = tierCounts[row.key] || 0;
    const pct = total ? Math.round((count / total) * 100) : 0;
    return `
      <div class="tier-bar-row">
        <div class="tier-bar-label">${row.label}</div>
        <div class="tier-bar-track">
          <div class="tier-bar-fill ${row.key}" style="width:${Math.max(pct, 6)}%">
            <span>${pct}%</span>
          </div>
        </div>
        <div class="tier-bar-count">${count}</div>
      </div>
    `;
  }).join("");
}

function renderFlagList(redFlags, total) {
  const el = document.getElementById("flag-list");
  if (!redFlags.length) {
    el.innerHTML = `<div style="color:var(--grey); font-size:13px;">No red flags recorded yet.</div>`;
    return;
  }
  const maxCount = Math.max(...redFlags.map(f => f.count), 1);
  el.innerHTML = redFlags.map(f => `
    <div class="flag-row">
      <div class="flag-label">${escapeHtml(f.label)}</div>
      <div class="flag-track"><div class="flag-fill" style="width:${(f.count / maxCount) * 100}%"></div></div>
      <div class="flag-count">${f.count}</div>
    </div>
  `).join("");
}

function renderDomains(domains) {
  const el = document.getElementById("domain-list");
  if (!domains.length) {
    el.innerHTML = `<div style="color:var(--grey); font-size:13px;">No trusted domains configured.</div>`;
    return;
  }
  el.innerHTML = domains.map(d => `<span class="domain-chip">${escapeHtml(d)}</span>`).join("");
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

loadAnalytics();
