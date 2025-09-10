/**
 * Tier Lock JavaScript - Feature access controls and user status management
 */

// Global user status cache
window.userStatus = null;

/**
 * Fetch user information from the V1 API
 */
async function fetchUserInfo() {
    try {
        const response = await fetch('/v1/me', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.status === 401) {
            // User not authenticated, redirect to login
            window.location.href = '/auth/login';
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`Failed to fetch user info: ${response.statusText}`);
        }
        
        const userInfo = await response.json();
        return userInfo;
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

/**
 * Fetch user entitlements (tier, trial status, limits)
 */
async function fetchUserEntitlements() {
    try {
        const response = await fetch('/v1/entitlements', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.status === 401) {
            window.location.href = '/auth/login';
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`Failed to fetch entitlements: ${response.statusText}`);
        }
        
        const entitlements = await response.json();
        return entitlements;
    } catch (error) {
        console.error('Error fetching entitlements:', error);
        return null;
    }
}

/**
 * Initialize user status and apply tier restrictions
 */
async function initializeTierSystem() {
    try {
        // Fetch user info and entitlements
        const [userInfo, entitlements] = await Promise.all([
            fetchUserInfo(),
            fetchUserEntitlements()
        ]);
        
        if (!userInfo || !entitlements) {
            console.error('Failed to initialize tier system');
            return;
        }
        
        // Combine into user status
        window.userStatus = {
            ...userInfo,
            ...entitlements
        };
        
        // Apply tier restrictions to page elements
        applyTierRestrictions();
        
        // Update UI elements with user status
        updateUserStatusUI();
        
        console.log('Tier system initialized:', window.userStatus);
        
    } catch (error) {
        console.error('Error initializing tier system:', error);
    }
}

/**
 * Apply tier restrictions to page elements
 */
function applyTierRestrictions() {
    if (!window.userStatus) return;
    
    const { tier, trial_active } = window.userStatus;
    
    // Find elements with tier requirements
    const tierElements = document.querySelectorAll('[data-tier-required]');
    
    tierElements.forEach(element => {
        const requiredTier = element.dataset.tierRequired;
        const hasAccess = checkTierAccess(tier, requiredTier, trial_active);
        
        if (!hasAccess) {
            lockFeature(element, requiredTier);
        }
    });
    
    // Apply trial indicators
    if (trial_active) {
        applyTrialIndicators();
    }
}

/**
 * Check if user has access to a tier-restricted feature
 */
function checkTierAccess(userTier, requiredTier, trialActive = false) {
    const tierLevels = { bronze: 1, silver: 2, gold: 3 };
    const userLevel = tierLevels[userTier] || 0;
    const requiredLevel = tierLevels[requiredTier] || 0;
    
    // Trial users get access to all tiers
    if (trialActive && userTier === 'bronze') {
        return true;
    }
    
    return userLevel >= requiredLevel;
}

/**
 * Lock a feature element with tier restriction overlay
 */
function lockFeature(element, requiredTier) {
    element.classList.add('feature-locked');
    
    // Create lock overlay
    const overlay = document.createElement('div');
    overlay.className = 'tier-lock-overlay';
    
    const message = document.createElement('div');
    message.className = 'tier-lock-message';
    
    const title = document.createElement('div');
    title.className = 'tier-lock-title';
    title.textContent = `${requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1)} Tier Required`;
    
    const description = document.createElement('div');
    description.className = 'tier-lock-description';
    description.textContent = `Upgrade to ${requiredTier} tier to unlock this feature`;
    
    const button = document.createElement('a');
    button.className = 'tier-lock-button';
    button.href = '/upgrade';
    button.textContent = 'Upgrade Now';
    
    message.appendChild(title);
    message.appendChild(description);
    message.appendChild(button);
    overlay.appendChild(message);
    
    // Make element container relative for overlay positioning
    if (getComputedStyle(element).position === 'static') {
        element.style.position = 'relative';
    }
    
    element.appendChild(overlay);
}

/**
 * Apply trial indicators to page elements
 */
function applyTrialIndicators() {
    const trialElements = document.querySelectorAll('[data-trial-eligible]');
    
    trialElements.forEach(element => {
        element.classList.add('trial-active');
        
        // Add trial indicator badge
        const indicator = document.createElement('div');
        indicator.className = 'trial-indicator';
        indicator.textContent = 'TRIAL ACTIVE';
        
        if (getComputedStyle(element).position === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(indicator);
    });
}

/**
 * Update UI elements with user status information
 */
function updateUserStatusUI() {
    if (!window.userStatus) return;
    
    // Update tier badges
    const tierBadges = document.querySelectorAll('[data-user-tier]');
    tierBadges.forEach(badge => {
        badge.textContent = window.userStatus.tier.toUpperCase();
        badge.className = `tier-badge ${window.userStatus.tier}`;
    });
    
    // Update trial status
    const trialStatus = document.querySelectorAll('[data-trial-status]');
    trialStatus.forEach(element => {
        if (window.userStatus.trial_active) {
            element.textContent = `Trial Active (${window.userStatus.trial_hours_remaining}h remaining)`;
            element.style.color = '#ffd700';
        } else {
            element.textContent = 'No active trial';
            element.style.color = '#94a3b8';
        }
    });
    
    // Update usage indicators
    updateUsageIndicators();
}

/**
 * Update feature usage indicators
 */
function updateUsageIndicators() {
    if (!window.userStatus || !window.userStatus.features) return;
    
    Object.entries(window.userStatus.features).forEach(([feature, data]) => {
        const indicators = document.querySelectorAll(`[data-usage-feature="${feature}"]`);
        
        indicators.forEach(indicator => {
            const bar = indicator.querySelector('.usage-fill');
            const text = indicator.querySelector('.usage-text');
            
            if (bar && data.limit > 0) {
                const percentage = Math.min((data.used / data.limit) * 100, 100);
                bar.style.width = `${percentage}%`;
                
                // Color coding
                if (percentage >= 90) {
                    bar.className = 'usage-fill danger';
                } else if (percentage >= 75) {
                    bar.className = 'usage-fill warning';
                } else {
                    bar.className = 'usage-fill';
                }
            }
            
            if (text) {
                text.textContent = `${data.used}/${data.limit} uses today`;
            }
        });
    });
}

/**
 * Refresh user status (call after feature usage)
 */
async function refreshUserStatus() {
    console.log('Refreshing user status...');
    await initializeTierSystem();
}

/**
 * Check if feature is available for use
 */
function canUseFeature(feature) {
    if (!window.userStatus || !window.userStatus.features || !window.userStatus.features[feature]) {
        return false;
    }
    
    const featureData = window.userStatus.features[feature];
    return featureData.used < featureData.limit;
}

/**
 * Start trial for eligible users
 */
async function startTrial() {
    try {
        const response = await fetch('/v1/trial/start', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to start trial: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Refresh user status to reflect trial activation
            await refreshUserStatus();
            
            // Show success message
            showNotification('Trial activated! You now have access to Silver and Gold features for 5 hours.', 'success');
        } else {
            showNotification(result.message || 'Failed to start trial', 'error');
        }
        
    } catch (error) {
        console.error('Error starting trial:', error);
        showNotification('Failed to start trial. Please try again.', 'error');
    }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 20px',
        borderRadius: '8px',
        color: '#fff',
        fontWeight: '600',
        zIndex: '10000',
        maxWidth: '400px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });
    
    // Set color based on type
    const colors = {
        success: '#22c55e',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#22d3ee'
    };
    notification.style.background = colors[type] || colors.info;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after delay
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Initialize tier system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTierSystem);
} else {
    initializeTierSystem();
}

// Expose functions globally for use by other scripts
window.TierSystem = {
    refresh: refreshUserStatus,
    canUse: canUseFeature,
    startTrial: startTrial,
    userStatus: () => window.userStatus
};