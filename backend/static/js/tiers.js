// tiers.js - Clean trial handling for tiers page
(function () {
  const btn = document.getElementById('startTrialBtn');
  const statusEl = document.getElementById('trialStatus');

  function setStatus(msg) { 
    if (statusEl) statusEl.textContent = msg || ''; 
  }

  async function startTrial() {
    try {
      btn?.setAttribute('disabled', 'true');
      setStatus('Starting trial…');

      const res = await fetch('/api/start-trial', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      let data = {};
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) {
        try {
          data = await res.json();
        } catch (parseErr) {
          console.error('JSON parse error:', parseErr);
        }
      }

      console.log('🎯 Response status:', res.status);
      console.log('🎯 Response data:', data);

      if (res.ok && data.ok === true && data.trial_active === true) {
        // ✅ success: persist and update UI
        localStorage.setItem('trial_active', '1');
        localStorage.setItem('trial_started_at', data.trial_started_at || new Date().toISOString());
        localStorage.setItem('trial_expires_at', data.trial_expires_at);
        localStorage.setItem('trial_plan_limits_from', data.plan_limits_from || 'free');

        setStatus('Trial started!');
        btn?.classList.add('hidden');
        document.body.classList.add('trial-active', 'max-access');

        // Show success message
        alert('🎉 5-hour trial activated! All premium features unlocked.');

        // If other parts depend on server-side session, refresh once:
        setTimeout(() => {
          window.location.reload();
        }, 1000);
        return;
      }

      // ❌ backend said no
      const msg = (data && data.error) ? data.error : `HTTP ${res.status}`;
      throw new Error(msg);

    } catch (err) {
      console.error('startTrial failed:', err);
      setStatus('Failed to start trial');     // ← only here on real failure
      btn?.removeAttribute('disabled');
      
      // Show error message
      alert(`Failed to start trial: ${err.message || err}`);
    }
  }

  // Prevent duplicate bindings
  if (btn) {
    btn.removeEventListener?.('click', startTrial);
    btn.addEventListener('click', startTrial, { once: false });
  }

  // On load: if trial already active, hide button & show status
  (function initTrialUI() {
    const active = localStorage.getItem('trial_active') === '1';
    if (active) {
      btn?.classList.add('hidden');
      document.body.classList.add('trial-active', 'max-access');
      setStatus('Trial active');
      
      // Unlock Growth/Max companions
      document.querySelectorAll('[data-lock="growth"],[data-lock="max"]').forEach(el => {
        el.classList.remove('locked');
        el.setAttribute('aria-disabled', 'false');
      });
    }
  })();

  // Make globally available 
  window.startTrial = startTrial;
})();