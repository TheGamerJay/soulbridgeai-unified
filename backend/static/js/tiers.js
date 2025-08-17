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
      console.log('🎯 Success check:', {
        'res.ok': res.ok,
        'data.ok': data.ok,
        'data.trial_active': data.trial_active,
        'all_success': res.ok && data.ok === true && data.trial_active === true
      });

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

        // Force session sync before reload to ensure trial state is properly set
        fetch('/api/sync-trial-session', { credentials: 'include' })
          .then(() => {
            // Reload with cache buster after session sync
            setTimeout(() => {
              location.replace('/tiers?trial=1&ts=' + Date.now());
            }, 500);
          })
          .catch(() => {
            // Reload anyway if sync fails
            setTimeout(() => {
              location.replace('/tiers?trial=1&ts=' + Date.now());
            }, 1000);
          });
        return;
      }

      // ❌ backend said no  
      const msg = (data && data.error) ? data.error : `HTTP ${res.status}`;
      console.error('❌ Trial activation failed:', {
        status: res.status,
        ok: res.ok,
        data: data,
        error_msg: msg
      });
      throw new Error(msg);

    } catch (err) {
      console.error('startTrial failed:', err);
      setStatus('Failed to start trial');
      btn?.removeAttribute('disabled');
      
      // Enhanced user feedback with alert for critical errors
      const errorMsg = `Failed to start trial: ${err.message || err}`;
      console.error(errorMsg);
      
      // Always show error alert to debug the issue
      alert(`Trial activation failed!\n\nError: ${err.message || 'Unknown error'}\n\nCheck console for details.`);
    }
  }

  // Check session state on page load and update UI accordingly
  async function checkTrialStateAndUpdateUI() {
    try {
      const res = await fetch('/api/session-lite', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        console.log('🎯 Session state:', data);
        
        if (data.ok && data.trial_active) {
          // Trial is active - hide button and update UI
          btn?.classList.add('hidden');
          document.body.classList.add('trial-active', 'max-access');
          setStatus('Trial active');
          
          // Unlock Growth/Max companions
          document.querySelectorAll('[data-lock="growth"],[data-lock="max"]').forEach(el => {
            el.classList.remove('locked');
            el.setAttribute('aria-disabled', 'false');
          });
          
          // Start countdown if we have expiry time
          const expires = data.trial_expires_at || localStorage.getItem('trial_expires_at');
          if (expires && window.initTrialCountdown) {
            window.initTrialCountdown({
              containerId: 'trialTimerMount',
              expiresAtIso: expires,
              startedAtIso: data.trial_started_at || localStorage.getItem('trial_started_at')
            });
          }
        }
      }
    } catch (err) {
      console.warn('Failed to check trial state:', err);
      // Fallback to localStorage check
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
    }
  }

  // Initialize trial UI on page load
  checkTrialStateAndUpdateUI();

  // Debug session endpoint removed (not available in production)

  // Make globally available 
  window.startTrial = startTrial;
})();