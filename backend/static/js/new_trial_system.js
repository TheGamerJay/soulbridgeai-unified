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

// Start trial function
async function startTrial() {
    try {
        const response = await fetch('/api/start-trial', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Trial started successfully
            showToast('🎉 5-hour trial activated! All premium features unlocked.', 'success');
            
            // Refresh the page to update UI
            window.location.reload();
        } else {
            showToast(data.error || 'Failed to start trial', 'error');
        }
    } catch (error) {
        console.error('Error starting trial:', error);
        showToast('Error starting trial. Please try again.', 'error');
    }
}

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
window.startTrial = startTrial;
window.isCompanionUnlocked = isCompanionUnlocked;
window.updateCompanionAccess = updateCompanionAccess;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTrialSystem();
    updateCompanionAccess();
});