const DEMO_USER = "analyst01";
const DEMO_PASS = "phishguard123";

// If already "signed in" this session, skip straight to the dashboard.
if (sessionStorage.getItem("pg_logged_in") === "true") {
  window.location.href = "/dashboard";
}

const form = document.getElementById("login-form");
const errorMsg = document.getElementById("error-msg");

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  // Demo-only check. For a real deployment this would call a backend
  // auth endpoint instead of comparing against a hardcoded credential.
  if (username === DEMO_USER && password === DEMO_PASS) {
    sessionStorage.setItem("pg_logged_in", "true");
    sessionStorage.setItem("pg_analyst", username);
    window.location.href = "/dashboard";
  } else {
    errorMsg.classList.add("show");
  }
});
