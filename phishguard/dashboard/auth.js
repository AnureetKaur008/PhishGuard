/* auth.js — shared across every page behind the login gate.
   Include this BEFORE the page's own script so the redirect happens
   as early as possible. */

(function () {
  if (sessionStorage.getItem("pg_logged_in") !== "true") {
    window.location.href = "/login";
    return;
  }

  const analystName = sessionStorage.getItem("pg_analyst") || "analyst";
  const nameEl = document.getElementById("sidebar-analyst-name");
  if (nameEl) nameEl.textContent = analystName;

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      sessionStorage.removeItem("pg_logged_in");
      sessionStorage.removeItem("pg_analyst");
      window.location.href = "/";
    });
  }

  function tickClock() {
    const el = document.getElementById("live-clock");
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleString(undefined, {
      weekday: "short", hour: "2-digit", minute: "2-digit"
    });
  }
  tickClock();
  setInterval(tickClock, 1000 * 30);
})();

/* Shared score-ring SVG builder — used by the Overview modal and the
   Test an Email result panel so both look identical. */
function scoreRingSvg(score, dark) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(Math.max(score, 0), 100) / 100);
  const fillClass = dark ? "score-ring-fill dark" : "score-ring-fill";
  const textClass = dark ? "score-ring-text dark" : "score-ring-text";
  return `
    <svg width="64" height="64" viewBox="0 0 64 64">
      <circle class="score-ring-track" cx="32" cy="32" r="${r}"></circle>
      <circle class="${fillClass}" cx="32" cy="32" r="${r}"
        stroke-dasharray="${c}" stroke-dashoffset="${offset}"></circle>
      <text x="32" y="37" text-anchor="middle" class="${textClass}">${Math.round(score)}%</text>
    </svg>
  `;
}
