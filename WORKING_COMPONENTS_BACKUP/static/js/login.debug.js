// /static/js/login.debug.js
(() => {
  console.log("🔐 login.debug.js loaded");

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const btn  = document.getElementById("loginBtn");

    if (!form) {
      console.error("❌ #loginForm not found – the submit handler will never run");
      return;
    }

    // Guard against other scripts hijacking the submit
    form.onsubmit = null;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      console.log("➡️  Submit captured by login.debug.js");

      const email = (document.getElementById("email") || {}).value?.trim();
      const password = (document.getElementById("password") || {}).value;

      console.log("📨 Sending POST /auth/login", { emailMasked: !!email });

      try {
        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include", // ensure cookie is saved
          body: JSON.stringify({ email, password })
        });

        const data = await res.json().catch(() => ({}));
        console.log("📥 /auth/login response:", res.status, data);

        if (!res.ok || !data.success) {
          alert(data.error || data.message || "Login failed");
          return;
        }

        const redirect = data.redirect || "/";
        console.log("✅ Login OK, redirecting to", redirect);
        window.location.replace(redirect);
      } catch (err) {
        console.error("🛑 Network/JS error while logging in:", err);
        alert("Network error. Check console.");
      }
    });

    // Optional: click handler on the button as a fallback
    if (btn) {
      btn.addEventListener("click", (e) => {
        console.log("🖱️ loginBtn clicked");
      });
    }

    console.log("✅ login.debug.js attached submit handler successfully");
  });
})();