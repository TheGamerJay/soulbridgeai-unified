// tiers.js - Clean trial handling for tiers page
(function () {
  const btn = document.getElementById('startTrialBtn');
  const statusEl = document.getElementById('trialStatus');

  function setStatus(msg) { 
    if (statusEl) statusEl.textContent = msg || ''; 
  }

  // Bind click defensively (prevents form submit or parent click handlers)
  if (btn) {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      startTrial();
    }, { passive: false });
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
        try { data = await res.json(); } catch {}
      }

      console.log('🎯 Response status:', res.status);
      console.log('🎯 Response data:', data);

      if (res.ok && data.ok === true && data.trial_active === true) {
        // ✅ persist state for client UI and countdown
        localStorage.setItem('trial_active', '1');
        localStorage.setItem('trial_started_at', data.trial_started_at || new Date().toISOString());
        localStorage.setItem('trial_expires_at', data.trial_expires_at);
        localStorage.setItem('trial_plan_limits_from', data.plan_limits_from || 'free');

        // UI: hide button immediately; add trial CSS flags
        btn?.classList.add('hidden');
        document.body.classList.add('trial-active', 'max-access');
        setStatus('🎉 5-hour trial activated!');

        // One-time SSR refresh to pull server-side gated content (cache-busted)
        // Use a flag to avoid reload loops
        localStorage.setItem('trial_refreshed_once', '1');
        location.replace('/tiers?trial=1&ts=' + Date.now());
        return;
      }

      // ❌ backend said no
      const msg = (data && data.error) ? data.error : `HTTP ${res.status}`;
      throw new Error(msg);

    } catch (err) {
      console.error('startTrial failed:', err);
      setStatus('Failed to start trial');
      btn?.removeAttribute('disabled');
      // Show error message (removed alert to avoid interfering with navigation)
      console.error(`Failed to start trial: ${err.message || err}`);
    }
  }

  // Init: if trial already active, lock UI instantly and start countdown
  (function initTrialUI() {
    const active = localStorage.getItem('trial_active') === '1';
    const expires = localStorage.getItem('trial_expires_at');
    if (active && expires) {
      document.body.classList.add('trial-active', 'max-access');
      btn?.classList.add('hidden');
      setStatus('Trial active');
      
      // Unlock Growth/Max companions
      document.querySelectorAll('[data-lock="growth"],[data-lock="max"]').forEach(el => {
        el.classList.remove('locked');
        el.setAttribute('aria-disabled', 'false');
      });
      
      // Start/attach circular countdown if present
      if (window.initTrialCountdown) {
        window.initTrialCountdown({
          containerId: 'trialTimerMount',
          expiresAtIso: expires,
          startedAtIso: localStorage.getItem('trial_started_at')
        });
      }
    }
  })();

  // Optional: verify server session after load (helps confirm SSR sync)
  (async function debugSessionOnce() {
    try {
      const res = await fetch('/api/debug-session', { credentials: 'include' });
      if (res.ok) {
        const s = await res.json();
        console.log('[debug-session]', s);
      }
    } catch {}
  })();

  // Make globally available 
  window.startTrial = startTrial;
})();