/**
 * SoulBridge AI - Training Consent System (Frontend Helper)
 * Simple JavaScript implementation for managing user training consent
 */

class ConsentManager {
    constructor(apiBase = '') {
        this.apiBase = apiBase;
        this.cache = null;
        this.cacheExpiry = 0;
    }

    /**
     * Get current consent status
     * @returns {Promise<{status: string, ts?: number, content_types?: string[]}>}
     */
    async getConsent() {
        // Use cache if still valid (1 minute cache)
        if (this.cache && Date.now() < this.cacheExpiry) {
            return this.cache;
        }

        try {
            const response = await fetch(`${this.apiBase}/api/consent/get`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.cache = {
                status: data.status || 'opt_out',
                ts: data.ts,
                content_types: data.content_types || ['lyrics', 'poems', 'stories', 'scripts', 'articles', 'letters']
            };
            this.cacheExpiry = Date.now() + 60000; // 1 minute cache
            return this.cache;

        } catch (error) {
            console.warn('Failed to get consent status:', error);
            return { status: 'opt_out', content_types: [] };
        }
    }

    /**
     * Set consent status
     * @param {string} status - 'opt_in' or 'opt_out'
     * @param {string[]} contentTypes - Types of content to consent for
     * @returns {Promise<boolean>} Success status
     */
    async setConsent(status, contentTypes = ['lyrics', 'poems', 'stories', 'scripts', 'articles', 'letters']) {
        try {
            const response = await fetch(`${this.apiBase}/api/consent/set`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: status,
                    content_types: contentTypes
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            // Clear cache to force refresh
            this.cache = null;
            this.cacheExpiry = 0;

            const result = await response.json();
            return result.ok === true;

        } catch (error) {
            console.error('Failed to set consent status:', error);
            return false;
        }
    }

    /**
     * Check if user has consented for a specific content type
     * @param {string} contentType - 'lyrics', 'poems', 'stories', etc.
     * @returns {Promise<boolean>}
     */
    async hasConsent(contentType) {
        try {
            const consent = await this.getConsent();
            return consent.status === 'opt_in' && 
                   (!consent.content_types || consent.content_types.includes(contentType));
        } catch (error) {
            console.warn('Failed to check consent:', error);
            return false;
        }
    }

    /**
     * Show consent confirmation dialog and update status
     * @param {boolean} enable - Enable or disable consent
     * @returns {Promise<boolean>} Whether user confirmed and operation succeeded
     */
    async showConsentDialog(enable) {
        if (enable) {
            const confirmed = confirm(
                "Enable draft sharing?\\n\\n" +
                "• FUTURE drafts will be saved to improve the system.\\n" +
                "• Turning OFF later stops new saves, but past contributions remain.\\n" +
                "• Your exact text is never shown to others.\\n\\n" +
                "See Terms & Policy for details."
            );
            
            if (!confirmed) return false;
            return await this.setConsent('opt_in');
            
        } else {
            const confirmed = confirm(
                "Turn OFF draft sharing?\\n\\n" +
                "• This stops saving FUTURE drafts.\\n" +
                "• Anything already saved will remain in the contribution pool."
            );
            
            if (!confirmed) return false;
            return await this.setConsent('opt_out');
        }
    }

    /**
     * Create a consent toggle element
     * @param {Object} options - Configuration options
     * @returns {HTMLElement}
     */
    createToggleElement(options = {}) {
        const {
            label = 'Share drafts to improve the model',
            containerId = 'consent-toggle-container',
            className = 'consent-toggle'
        } = options;

        const container = document.createElement('div');
        container.id = containerId;
        container.className = className;
        container.innerHTML = `
            <div style="margin-bottom: 8px;">
                <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer;">
                    <input type="checkbox" id="consent-checkbox" disabled>
                    <span>${label}</span>
                </label>
            </div>
            <div style="font-size: 11px; color: #666; line-height: 1.4;">
                Draft sharing saves your <strong>future</strong> drafts to help improve the system.<br>
                Turning OFF stops new saves; <strong>past contributions remain</strong>. 
                Your exact text is never shown to others.
                <a href="/profile#terms" style="text-decoration: underline;">Terms &amp; Policy</a>
            </div>
        `;

        const checkbox = container.querySelector('#consent-checkbox');
        
        // Load current status
        this.getConsent().then(consent => {
            checkbox.checked = consent.status === 'opt_in';
            checkbox.disabled = false;
        });

        // Handle changes
        checkbox.addEventListener('change', async (e) => {
            checkbox.disabled = true;
            
            try {
                const success = await this.showConsentDialog(e.target.checked);
                if (success) {
                    // Update UI to reflect new state
                    const newConsent = await this.getConsent();
                    checkbox.checked = newConsent.status === 'opt_in';
                } else {
                    // Revert checkbox if user cancelled or operation failed
                    checkbox.checked = !e.target.checked;
                }
            } finally {
                checkbox.disabled = false;
            }
        });

        return container;
    }
}

// Global instance
window.consentManager = new ConsentManager();

/**
 * Helper function to make POST requests with automatic consent inclusion
 * @param {string} url - API endpoint URL
 * @param {Object} data - Request payload
 * @returns {Promise<Response>}
 */
async function postWithConsent(url, data) {
    const hasConsent = await window.consentManager.hasConsent('lyrics'); // Default check
    
    return fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ...data,
            contribute: hasConsent
        })
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ConsentManager, postWithConsent };
}