(function () {
  console.log("🔐 auth.js loaded - version 2025-07-25");

  // Simple toast notification system (shared)
  function showToast(message, type = 'info') {
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          padding: 15px 20px;
          border-radius: 8px;
          color: white;
          font-weight: 500;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          z-index: 10000;
          max-width: 400px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      `;
      
      // Set background color based on type
      const colors = {
          success: '#10B981',
          error: '#EF4444', 
          warning: '#F59E0B',
          info: '#3B82F6'
      };
      toast.style.backgroundColor = colors[type] || colors.info;
      
      toast.textContent = message;
      document.body.appendChild(toast);
      
      // Auto remove after 4 seconds
      setTimeout(() => {
          if (toast.parentNode) {
              toast.style.transition = 'opacity 0.3s ease';
              toast.style.opacity = '0';
              setTimeout(() => toast.remove(), 300);
          }
      }, 4000);
  }

  function hookForm(id, opts) {
    const form = document.getElementById(id);
    console.log(`🔍 Looking for form with ID: ${id}`, form);
    if (!form) {
      console.warn(`❌ Form with ID '${id}' not found`);
      return;
    }
    
    console.log(`✅ Found form '${id}', adding event listener`);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      console.log(`🚀 FORM SUBMITTED: ${id}`);

      const formData = new FormData(form);
      const action = form.getAttribute("action") || opts.action;
      const method = (form.getAttribute("method") || opts.method || "POST").toUpperCase();

      console.log(`🚀 Submitting form to: ${action} with method: ${method}`);
      console.log(`📝 Form data:`, Object.fromEntries(formData.entries()));
      
      try {
        const res = await fetch(action, {
          method,
          body: formData,
          // **critical** to persist session cookies
          credentials: "include",
        });

        console.log(`📡 Response status: ${res.status}`);
        console.log(`📡 Response headers:`, res.headers);
        
        const contentType = res.headers.get("content-type") || "";
        const isJson = contentType.includes("application/json");
        console.log(`📦 Content type: ${contentType}, isJson: ${isJson}`);
        
        const data = isJson ? await res.json() : { success: res.ok };

        console.log("🔐 auth.js response", data);

        if (data.success) {
          const to = data.redirect || opts.onSuccessRedirect || "/";
          console.log(`🚀 Login successful! Redirecting to: ${to}`);
          
          // Force a small delay to ensure session is saved
          setTimeout(() => {
            window.location.href = to;
          }, 100);
        } else {
          const msg = data.message || data.error || opts.failMessage || "Something went wrong.";
          
          // For reset form, show message in page instead of alert
          if (form.id === 'resetForm') {
            const msgEl = document.getElementById('resetMessage');
            if (msgEl) {
              msgEl.textContent = msg;
              msgEl.className = data.success ? 'success' : 'error';
              msgEl.style.display = 'block';
              return;
            }
          }
          
          showToast(msg, 'error');
        }
      } catch (err) {
        console.error("auth.js error", err);
        showToast("Network or server error.", 'error');
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    hookForm("loginForm",     { action: "/auth/login",     onSuccessRedirect: "/", failMessage: "Login failed." });
    // Disabled registerForm hook - register.html has its own AJAX handler
    // hookForm("registerForm",  { action: "/auth/register",  onSuccessRedirect: "/intro", failMessage: "" });
    hookForm("resetForm",     { action: "/auth/reset",     onSuccessRedirect: "/login", failMessage: "Reset failed." });
  });
})();