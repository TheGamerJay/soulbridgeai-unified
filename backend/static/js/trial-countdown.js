// trial-countdown.js - Beautiful countdown timer for trials
(function(){
  /**
   * initTrialCountdown({ containerId?, expiresAtIso?, startedAtIso?, durationSeconds?, onExpire? })
   * - If expires/start not passed, it auto-reads from localStorage.
   * - Uses startedAt/expiresAt to compute total duration; falls back to durationSeconds (default 5h).
   * - Adds ARIA for accessibility. Dispatches `trial:expired` on window when it ends.
   */
  function initTrialCountdown(opts = {}) {
    const containerId = opts.containerId || 'trialTimerMount';
    const mount = document.getElementById(containerId);
    if (!mount) return console.warn('[trial-timer] mount not found:', containerId);

    // Pull times
    const ls = window.localStorage;
    const expiresIso = opts.expiresAtIso || ls.getItem('trial_expires_at');
    const startedIso = opts.startedAtIso || ls.getItem('trial_started_at');
    const DEFAULT_SECONDS = (opts.durationSeconds && Number(opts.durationSeconds) > 0)
      ? Number(opts.durationSeconds)
      : 5 * 3600; // default 5h if unknown

    if (!expiresIso) {
      mount.innerHTML = '';
      return; // no active trial
    }

    // Normalize malformed ISO timestamps before parsing
    function normalizeIsoZ(s) {
      if (!s) return null;
      let x = String(s).trim().replace(' ', 'T'); // Fix space separator
      x = x.replace(/\.\d+/, '');                 // Remove microseconds
      x = x.replace(/\+00:00Z$/, 'Z');           // Fix double timezone
      x = x.replace(/\+00:00$/, 'Z');            // +00:00 -> Z
      if (!x.endsWith('Z')) x += 'Z';            // Ensure Z suffix
      return x;
    }

    // Enhanced validation for expiry date parsing
    const normalizedExpiry = normalizeIsoZ(expiresIso);
    const expiresAt = new Date(normalizedExpiry);
    if (isNaN(expiresAt.getTime())) {
      console.warn('[trial-timer] Invalid expiry date format:', expiresIso, '→', normalizedExpiry);
      mount.innerHTML = '<div class="trial-timer expired"><div class="label"><div class="title">Trial Status</div><div class="time">Invalid Date</div></div></div>';
      return;
    }

    const now = Date.now();
    let totalSeconds;
    if (startedIso) {
      const normalizedStarted = normalizeIsoZ(startedIso);
      const startedAt = new Date(normalizedStarted);
      if (isNaN(startedAt.getTime())) {
        console.warn('[trial-timer] Invalid start date format, using default duration:', startedIso, '→', normalizedStarted);
        totalSeconds = DEFAULT_SECONDS;
      } else {
        totalSeconds = Math.max(1, Math.round((expiresAt - startedAt) / 1000));
      }
    } else {
      totalSeconds = DEFAULT_SECONDS;
    }

    // Build DOM once
    const size = 140;
    const r = 54;
    const cx = 70, cy = 70;
    const circ = 2 * Math.PI * r;

    const root = document.createElement('div');
    root.className = 'trial-timer ok';
    root.setAttribute('role', 'timer');
    root.setAttribute('aria-live', 'polite');
    root.setAttribute('aria-label', 'Trial time remaining');

    root.innerHTML = `
      <svg viewBox="0 0 ${size} ${size}" aria-hidden="true">
        <circle class="ring-bg" cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke-width="10"></circle>
        <circle class="ring"    cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke-width="10"
                stroke-dasharray="${circ}" stroke-dashoffset="0"></circle>
      </svg>
      <div class="label">
        <div class="title">Trial ends in</div>
        <div class="time" id="trialTimeText">—</div>
      </div>
    `;
    mount.innerHTML = '';
    mount.appendChild(root);

    const ring = root.querySelector('.ring');
    const timeEl = root.querySelector('#trialTimeText');

    // thresholds
    const WARN_MS = 30 * 60 * 1000;   // 30m
    const DANGER_MS = 10 * 60 * 1000; // 10m

    // render tick
    let rafId = null;
    function fmt(ms) {
      if (ms <= 0) return '00:00:00';
      const s = Math.floor(ms / 1000);
      const hh = Math.floor(s / 3600);
      const mm = Math.floor((s % 3600) / 60);
      const ss = s % 60;
      return `${String(hh).padStart(2,'0')}:${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
    }
    function setBand(msLeft) {
      root.classList.remove('ok','warn','danger','expired');
      if (msLeft <= 0) root.classList.add('expired');
      else if (msLeft <= DANGER_MS) root.classList.add('danger');
      else if (msLeft <= WARN_MS) root.classList.add('warn');
      else root.classList.add('ok');
    }
    function tick() {
      const msLeft = expiresAt.getTime() - Date.now();
      // progress based on totalSeconds
      const used = Math.max(0, totalSeconds - Math.max(0, Math.round(msLeft / 1000)));
      const progress = Math.min(1, used / totalSeconds);
      const offset = circ * progress;
      ring.style.strokeDashoffset = String(offset);
      timeEl.textContent = fmt(msLeft);
      setBand(msLeft);
      root.setAttribute('aria-valuemin','0');
      root.setAttribute('aria-valuemax', String(totalSeconds));
      root.setAttribute('aria-valuenow', String(Math.max(0, Math.round(msLeft/1000))));

      if (msLeft <= 0) {
        cancelAnimationFrame(rafId);
        // mark storage + fire event with enhanced error handling
        try { 
          localStorage.setItem('trial_active','0'); 
          localStorage.removeItem('trial_expires_at');
          localStorage.removeItem('trial_started_at');
        } catch (storageError) {
          console.warn('[trial-timer] localStorage cleanup failed:', storageError);
        }
        
        try {
          const evt = new CustomEvent('trial:expired', { detail: { when: new Date().toISOString() } });
          window.dispatchEvent(evt);
        } catch (eventError) {
          console.warn('[trial-timer] Event dispatch failed:', eventError);
        }
        
        if (opts.onExpire) {
          try {
            opts.onExpire();
          } catch (callbackError) {
            console.warn('[trial-timer] onExpire callback failed:', callbackError);
          }
        }
        return;
      }
      rafId = requestAnimationFrame(tick);
    }
    tick();

    // return a small API
    return {
      destroy(){ cancelAnimationFrame(rafId); mount.innerHTML=''; },
      node: root
    };
  }

  // expose globally for easy use
  window.initTrialCountdown = initTrialCountdown;

  // auto-init if we already have a trial
  (function auto(){
    const has = localStorage.getItem('trial_active') === '1' && localStorage.getItem('trial_expires_at');
    if (has) initTrialCountdown(); // uses defaults + localStorage
  })();

  // example: relock UI on expire (you can adjust to your app)
  window.addEventListener('trial:expired', () => {
    const btn = document.getElementById('startTrialBtn');
    if (btn) btn.classList.remove('hidden'), btn.removeAttribute('disabled');
    document.body.classList.remove('trial-active', 'max-access');
    document.querySelectorAll('[data-lock="growth"],[data-lock="max"]').forEach(el => {
      el.classList.add('locked');
      el.setAttribute('aria-disabled', 'true');
    });
    const statusEl = document.getElementById('trialStatus');
    if (statusEl) statusEl.textContent = 'Trial expired';
  });
})();