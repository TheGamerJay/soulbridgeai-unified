// New Clean Trial System - JavaScript Functions
// Based on the proposed trial system implementation

// Simple toast notification system
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

// Check trial active and update UI
function refreshTrialUI(trialActive, plan) {
    const buttons = document.querySelectorAll(".btn-select");
    const upgradeBtns = document.querySelectorAll(".btn-upgrade");

    if (trialActive) {
        upgradeBtns.forEach(btn => btn.style.display = 'none');
        buttons.forEach(btn => {
            btn.textContent = "✅ Trial Active";
            btn.disabled = true;
        });
    }
}

// Display limits based on plan
function updateLimits(plan) {
    let limits = {
        free: {decoder: 3, fortune: 2, horoscope: 3},
        growth: {decoder: 15, fortune: 8, horoscope: 10},
        max: {decoder: '∞', fortune: '∞', horoscope: '∞'},
        trial: {decoder: 15, fortune: 8, horoscope: 10},
    };
    
    const decodeLimitEl = document.getElementById("decode-limit");
    const fortuneLimitEl = document.getElementById("fortune-limit");
    const horoscopeLimitEl = document.getElementById("horoscope-limit");
    
    if (decodeLimitEl) decodeLimitEl.textContent = `${limits[plan].decoder}`;
    if (fortuneLimitEl) fortuneLimitEl.textContent = `${limits[plan].fortune}`;
    if (horoscopeLimitEl) horoscopeLimitEl.textContent = `${limits[plan].horoscope}`;
}

// Fetch user plan and trial status from backend
async function fetchUserPlanStatus() {
    try {
        const response = await fetch('/api/user-plan');
        if (response.ok) {
            const data = await response.json();
            return {
                plan: data.plan || 'free',
                trialActive: data.trial_active || false
            };
        }
    } catch (error) {
        console.error('Error fetching user plan:', error);
    }
    return { plan: 'free', trialActive: false };
}

// Initialize trial system on page load
async function initializeTrialSystem() {
    const { plan, trialActive } = await fetchUserPlanStatus();
    
    // Update UI based on trial status
    refreshTrialUI(trialActive, plan);
    
    // Update limits display
    const effectivePlan = trialActive ? 'trial' : plan;
    updateLimits(effectivePlan);
    
    // Update any trial status displays
    const trialStatusElements = document.querySelectorAll('.trial-status');
    trialStatusElements.forEach(el => {
        if (trialActive) {
            el.textContent = '🔓 Trial Active (5 hours)';
            el.className = 'trial-status trial-active';
        } else {
            el.textContent = '🔒 Normal (No Trial Active)';
            el.className = 'trial-status trial-inactive';
        }
    });
}

// Start trial function - Fixed to handle new backend response format
window.startTrial = async function startTrial() {
  const btn = document.querySelector('#startTrialBtn');
  const toast = (msg, type = 'info') => showToast(msg, type); // Use existing toast system

  // simple loading state
  btn?.setAttribute('disabled', 'disabled');
  btn?.classList.add('opacity-60', 'pointer-events-none');

  try {
    console.log('🎯 Trial button clicked!');
    const res = await fetch('/api/start-trial', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      cache: 'no-store',
    });

    console.log('🎯 Response status:', res.status);

    // Attempt to parse JSON either way (200 or not)
    let data = null;
    try { data = await res.json(); } catch { data = null; }

    console.log('🎯 Response data:', data);

    // STRICT success gate - check both res.ok AND data.ok AND trial_active
    if (!res.ok || !data || data.ok !== true || data.trial_active !== true) {
      const msg = (data && data.error) ? data.error : `HTTP ${res.status}`;
      throw new Error(msg);
    }

    // ✅ Success — persist + update UI
    const expiresIso = data.trial_expires_at; // e.g. "2025-08-17T07:38:19.451832+00:00"
    const startedIso = data.trial_started_at;
    const planFrom  = data.plan_limits_from || 'free';

    // Enhanced localStorage persistence with error handling
    try {
      localStorage.setItem('trial_active', 'true');
      localStorage.setItem('trial_expires_at', expiresIso);
      localStorage.setItem('trial_started_at', startedIso || new Date().toISOString());
      localStorage.setItem('trial_plan_limits_from', planFrom);
    } catch (storageError) {
      console.warn('Failed to persist trial state to localStorage:', storageError);
      // Continue anyway - trial is still active on backend
    }

    // Flip UI gates (example IDs/classes—match to your DOM)
    document.body.classList.add('trial-active', 'max-access');
    document.querySelectorAll('[data-lock="growth"],[data-lock="max"]').forEach(el => {
      el.classList.remove('locked');
      el.setAttribute('aria-disabled', 'false');
    });

    // Hide the start button forever for this user
    document.querySelectorAll('#startTrialContainer, #startTrialBtn').forEach(el => el?.classList.add('hidden'));

    // Kick off your countdown (expects an ISO string)
    if (typeof window.renderTrialCountdown === 'function') {
      window.renderTrialCountdown(expiresIso);
    } else {
      // Enhanced fallback inline countdown with validation
      const el = document.getElementById('trialCountdown');
      if (el) {
        const target = Date.parse(expiresIso);
        if (isNaN(target)) {
          console.warn('Invalid expiry date for countdown:', expiresIso);
          el.textContent = 'Invalid Date';
        } else {
          const tick = () => {
            const ms = target - Date.now();
            if (ms <= 0) { 
              el.textContent = 'Expired'; 
              clearInterval(t); 
              // Clean up localStorage on expiry
              try {
                localStorage.setItem('trial_active', 'false');
                localStorage.removeItem('trial_expires_at');
                localStorage.removeItem('trial_started_at');
              } catch {}
              return; 
            }
            const h = Math.floor(ms / 3_600_000);
            const m = Math.floor((ms % 3_600_000) / 60_000);
            const s = Math.floor((ms % 60_000) / 1000);
            el.textContent = `${h}h ${m}m ${s}s`;
          };
          tick();
          const t = setInterval(tick, 1000);
        }
      }
    }

    toast('✅ Trial started — Growth & Max companions unlocked (limits stay on your plan).', 'success');

    // Update companion access and UI
    await updateCompanionAccess();
    await initializeTrialSystem();

  } catch (err) {
    console.error('❌ Failed to start trial:', err);
    
    // Enhanced error feedback with user-friendly messaging
    const msg = String(err && err.message || err || 'Unknown error');
    toast(`Failed to start trial: ${msg}`, 'error');
    
    // Show detailed error for debugging in console
    if (err.stack) {
      console.error('Full error stack:', err.stack);
    }
    
    // Additional user guidance for common errors
    if (msg.includes('already used') || msg.includes('permanently')) {
      setTimeout(() => {
        toast('Trial can only be used once per account. Consider upgrading to a subscription plan.', 'info');
      }, 2000);
    }
  } finally {
    // Always clear loading state
    btn?.removeAttribute('disabled');
    btn?.classList.remove('opacity-60', 'pointer-events-none');
  }
};

// Check if companion is unlocked for user
function isCompanionUnlocked(companionTier, userPlan, trialActive) {
    if (trialActive) {
        return true; // All companions unlocked during trial
    }
    
    if (companionTier === 'free') {
        return true;
    }
    
    if (companionTier === 'growth') {
        return userPlan === 'growth' || userPlan === 'max';
    }
    
    if (companionTier === 'max') {
        return userPlan === 'max';
    }
    
    return false;
}

// Update companion access based on trial status
async function updateCompanionAccess() {
    const { plan, trialActive } = await fetchUserPlanStatus();
    
    // Find all companion elements and update their accessibility
    const companionElements = document.querySelectorAll('[data-companion-tier]');
    
    companionElements.forEach(companionEl => {
        const tier = companionEl.dataset.companionTier;
        const unlocked = isCompanionUnlocked(tier, plan, trialActive);
        
        if (unlocked) {
            companionEl.classList.remove('locked');
            companionEl.classList.add('unlocked');
            
            // Remove any lock overlays
            const lockOverlay = companionEl.querySelector('.lock-overlay');
            if (lockOverlay) {
                lockOverlay.style.display = 'none';
            }
        } else {
            companionEl.classList.add('locked');
            companionEl.classList.remove('unlocked');
            
            // Show lock overlay
            const lockOverlay = companionEl.querySelector('.lock-overlay');
            if (lockOverlay) {
                lockOverlay.style.display = 'block';
            }
        }
    });
}

// Export functions for global use
window.refreshTrialUI = refreshTrialUI;
window.updateLimits = updateLimits;
window.fetchUserPlanStatus = fetchUserPlanStatus;
window.initializeTrialSystem = initializeTrialSystem;
// window.startTrial is already assigned above in the function definition
window.isCompanionUnlocked = isCompanionUnlocked;
window.updateCompanionAccess = updateCompanionAccess;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTrialSystem();
    updateCompanionAccess();
});