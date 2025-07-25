(function () {
  console.log("🔐 auth.js loaded");

  function hookForm(id, opts) {
    const form = document.getElementById(id);
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      const action = form.getAttribute("action") || opts.action;
      const method = (form.getAttribute("method") || opts.method || "POST").toUpperCase();

      try {
        const res = await fetch(action, {
          method,
          body: formData,
          // **critical** to persist session cookies
          credentials: "include",
        });

        const contentType = res.headers.get("content-type") || "";
        const isJson = contentType.includes("application/json");
        const data = isJson ? await res.json() : { success: res.ok };

        console.log("🔐 auth.js response", data);

        if (data.success) {
          const to = data.redirect || opts.onSuccessRedirect || "/";
          // multi-try redirect (some browsers can be picky after fetch)
          try { window.location.href = to; return; } catch (e) {}
          try { window.location.replace(to); return; } catch (e) {}
          window.location.reload();
        } else {
          const msg = data.message || data.error || opts.failMessage || "Something went wrong.";
          alert(msg);
        }
      } catch (err) {
        console.error("auth.js error", err);
        alert("Network or server error.");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    hookForm("loginForm",     { action: "/auth/login",     onSuccessRedirect: "/", failMessage: "Login failed." });
    hookForm("registerForm",  { action: "/auth/register",  onSuccessRedirect: "/login", failMessage: "Registration failed." });
    hookForm("resetForm",     { action: "/auth/reset",     onSuccessRedirect: "/login", failMessage: "Reset failed." });
  });
})();