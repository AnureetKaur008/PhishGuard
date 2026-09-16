const mediumSlider = document.getElementById("medium-slider");
const highSlider = document.getElementById("high-slider");
const mediumValue = document.getElementById("medium-value");
const highValue = document.getElementById("high-value");
const domainsInput = document.getElementById("domains-input");
const preview = document.getElementById("threshold-preview");

function renderPreview() {
  const medium = parseInt(mediumSlider.value, 10);
  const high = parseInt(highSlider.value, 10);

  mediumValue.textContent = medium + "%";
  highValue.textContent = high + "%";

  // keep medium below high, both stay usable
  const safeHigh = Math.max(high, medium + 5);
  if (safeHigh !== high) {
    highSlider.value = safeHigh;
    highValue.textContent = safeHigh + "%";
  }

  const lowPct = medium;
  const medPct = Math.max(safeHigh - medium, 0);
  const highPct = Math.max(100 - safeHigh, 0);

  preview.innerHTML = `
    <div style="width:${lowPct}%; background: var(--mint);">LOW 0–${medium}%</div>
    <div style="width:${medPct}%; background: var(--amber); color: var(--navy);">REVIEW ${medium}–${safeHigh}%</div>
    <div style="width:${highPct}%; background: var(--coral);">HIGH ${safeHigh}–100%</div>
  `;
}

mediumSlider.addEventListener("input", renderPreview);
highSlider.addEventListener("input", renderPreview);

async function loadSettings() {
  const res = await fetch("/api/settings");
  const data = await res.json();
  mediumSlider.value = data.medium_threshold;
  highSlider.value = data.high_threshold;
  domainsInput.value = data.trusted_domains.join("\n");
  renderPreview();
}

document.getElementById("save-btn").addEventListener("click", async () => {
  const payload = {
    medium_threshold: parseInt(mediumSlider.value, 10),
    high_threshold: parseInt(highSlider.value, 10),
    trusted_domains: domainsInput.value.split("\n").map(d => d.trim()).filter(Boolean),
  };

  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    const toast = document.getElementById("save-toast");
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2500);
  } else {
    alert("Couldn't save settings — check the console app is running correctly.");
  }
});

loadSettings();
