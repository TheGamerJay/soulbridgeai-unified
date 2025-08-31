/**
 * Tier-Locked UI Elements System
 * 
 * Provides tier-based access control for UI elements with upgrade prompts.
 * Works with Bronze/Silver/Gold tier system.
 */

class TierLockManager {
    constructor() {
        this.userAccess = null;
        this.initialized = false;
        this.loadUserAccess();
    }

    async loadUserAccess() {
        try {
            const response = await fetch('/api/me', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.userAccess = result.access;
                    this.userData = result.user;
                    this.trialData = result.trial;
                    this.initialized = true;
                    this.applyTierLocks();
                    console.log('🔒 Tier lock system initialized for', this.userData.plan, 'user');
                } else {
                    this.fallbackToGuestMode();
                }
            } else {
                this.fallbackToGuestMode();
            }
        } catch (error) {
            console.warn('🔒 Tier lock system: Using guest mode due to API error');
            this.fallbackToGuestMode();
        }
    }

    fallbackToGuestMode() {
        // Fallback for guests or API errors - assume Bronze access
        this.userAccess = {
            trial_live: false,
            unlocked_tiers: ['bronze'],
            accessible_companion_tiers: ['bronze'],
            limits: { decoder: 3, fortune: 3, horoscope: 3, creative_writer: 3 }
        };
        this.userData = { plan: 'bronze' };
        this.initialized = true;
        this.applyTierLocks();
    }

    applyTierLocks() {
        if (!this.initialized) return;

        // Find all tier-locked elements
        const tierElements = document.querySelectorAll('[data-tier-required]');
        
        tierElements.forEach(element => {
            const requiredTier = element.getAttribute('data-tier-required');
            const hasAccess = this.userAccess.unlocked_tiers.includes(requiredTier);
            
            if (hasAccess) {
                this.unlockElement(element);
            } else {
                this.lockElement(element, requiredTier);
            }
        });

        // Apply companion tier locks
        const companionElements = document.querySelectorAll('[data-companion-tier]');
        
        companionElements.forEach(element => {
            const requiredTier = element.getAttribute('data-companion-tier');
            const hasAccess = this.userAccess.accessible_companion_tiers.includes(requiredTier);
            
            if (hasAccess) {
                this.unlockCompanion(element);
            } else {
                this.lockCompanion(element, requiredTier);
            }
        });

        // Apply feature limit displays
        this.updateFeatureLimits();
    }

    unlockElement(element) {
        element.classList.remove('tier-locked');
        element.classList.add('tier-unlocked');
        
        // Remove any existing lock overlays
        const lockOverlay = element.querySelector('.tier-lock-overlay');
        if (lockOverlay) {
            lockOverlay.remove();
        }
        
        // Re-enable interactions
        element.style.pointerEvents = 'auto';
        element.style.opacity = '1';
    }

    lockElement(element, requiredTier) {
        element.classList.add('tier-locked');
        element.classList.remove('tier-unlocked');
        
        // Check if lock overlay already exists
        if (element.querySelector('.tier-lock-overlay')) {
            return;
        }
        
        // Create lock overlay
        const lockOverlay = this.createLockOverlay(requiredTier);
        
        // Position the overlay
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle.position === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(lockOverlay);
        
        // Disable interactions
        element.style.pointerEvents = 'auto'; // Keep auto so overlay can be clicked
        element.style.opacity = '0.7';
    }

    unlockCompanion(element) {
        element.classList.remove('companion-locked');
        element.classList.add('companion-unlocked');
        
        const lockBadge = element.querySelector('.companion-lock-badge');
        if (lockBadge) {
            lockBadge.remove();
        }
    }

    lockCompanion(element, requiredTier) {
        element.classList.add('companion-locked');
        element.classList.remove('companion-unlocked');
        
        // Add lock badge if not exists
        if (!element.querySelector('.companion-lock-badge')) {
            const lockBadge = this.createCompanionLockBadge(requiredTier);
            element.style.position = 'relative';
            element.appendChild(lockBadge);
        }
    }

    createLockOverlay(requiredTier) {
        const overlay = document.createElement('div');
        overlay.className = 'tier-lock-overlay';
        
        const tierInfo = this.getTierInfo(requiredTier);
        
        overlay.innerHTML = `
            <div class="lock-content">
                <div class="lock-icon">🔒</div>
                <div class="lock-title">${tierInfo.name} Required</div>
                <div class="lock-description">${tierInfo.description}</div>
                <button class="lock-upgrade-btn" onclick="TierLock.showUpgradeModal('${requiredTier}')">
                    Upgrade to ${tierInfo.name}
                </button>
            </div>
        `;
        
        return overlay;
    }

    createCompanionLockBadge(requiredTier) {
        const badge = document.createElement('div');
        badge.className = 'companion-lock-badge';
        
        const tierInfo = this.getTierInfo(requiredTier);
        
        badge.innerHTML = `
            <div class="lock-badge-icon">🔒</div>
            <div class="lock-badge-text">${tierInfo.name}</div>
        `;
        
        badge.onclick = () => this.showUpgradeModal(requiredTier);
        
        return badge;
    }

    getTierInfo(tier) {
        const tierData = {
            bronze: {
                name: 'Bronze',
                icon: '🥉',
                description: 'Basic features with ads',
                price: 'Free'
            },
            silver: {
                name: 'Silver',
                icon: '🥈', 
                description: 'Enhanced limits, 200 credits, no ads',
                price: '$12.99/month'
            },
            gold: {
                name: 'Gold',
                icon: '🥇',
                description: 'Unlimited features, 500 credits, Mini Studio',
                price: '$19.99/month'
            }
        };
        
        return tierData[tier] || tierData.bronze;
    }

    updateFeatureLimits() {
        const limitElements = document.querySelectorAll('[data-feature-limit]');
        
        limitElements.forEach(element => {
            const feature = element.getAttribute('data-feature-limit');
            const limit = this.userAccess.limits[feature];
            
            if (limit !== undefined) {
                const displayLimit = limit === Infinity ? '∞' : limit;
                element.textContent = `${displayLimit} daily`;
                
                // Add styling based on limit
                element.className = `feature-limit ${limit === Infinity ? 'unlimited' : limit > 10 ? 'high' : 'basic'}`;
            }
        });
    }

    showUpgradeModal(requiredTier) {
        const tierInfo = this.getTierInfo(requiredTier);
        const currentPlan = this.userData.plan || 'bronze';
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'tier-upgrade-modal';
        modal.innerHTML = `
            <div class="modal-backdrop" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.tier-upgrade-modal').remove()">×</button>
                
                <div class="modal-header">
                    <div class="tier-icon">${tierInfo.icon}</div>
                    <h2>Upgrade to ${tierInfo.name}</h2>
                    <p>${tierInfo.description}</p>
                </div>
                
                <div class="modal-body">
                    <div class="upgrade-reason">
                        <h3>🔓 Unlock This Feature</h3>
                        <p>This feature requires ${tierInfo.name} tier or higher. Upgrade now to get instant access plus all premium benefits.</p>
                    </div>
                    
                    <div class="tier-comparison">
                        <div class="current-tier">
                            <h4>Current: ${this.getTierInfo(currentPlan).name}</h4>
                            <div class="tier-price">${this.getTierInfo(currentPlan).price}</div>
                        </div>
                        <div class="upgrade-arrow">→</div>
                        <div class="target-tier">
                            <h4>Upgrade: ${tierInfo.name}</h4>
                            <div class="tier-price">${tierInfo.price}</div>
                        </div>
                    </div>
                </div>
                
                <div class="modal-actions">
                    <button class="upgrade-action-btn" onclick="window.location.href='/subscription'">
                        Upgrade to ${tierInfo.name}
                    </button>
                    <button class="modal-cancel" onclick="this.closest('.tier-upgrade-modal').remove()">
                        Maybe Later
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Track upgrade intent
        console.log(`🎯 Upgrade intent: ${currentPlan} → ${requiredTier}`);
    }

    // Public methods for manual control
    refreshAccess() {
        this.loadUserAccess();
    }

    checkAccess(tier) {
        return this.userAccess?.unlocked_tiers?.includes(tier) || false;
    }

    getCurrentPlan() {
        return this.userData?.plan || 'bronze';
    }
}

// Global instance
window.TierLock = new TierLockManager();

// Auto-apply locks when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for the API call to complete
    setTimeout(() => {
        if (window.TierLock.initialized) {
            window.TierLock.applyTierLocks();
        }
    }, 1000);
});

// Re-apply locks when user data might have changed
document.addEventListener('userDataUpdated', function() {
    window.TierLock.refreshAccess();
});