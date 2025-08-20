/**
 * Circular Trial Timer - Vanilla JavaScript
 * Beautiful circular countdown timer with progress ring
 * Converted from React component for SoulBridge AI
 */

class CircularTrialTimer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`CircularTrialTimer: Container "${containerId}" not found`);
            return;
        }

        // Configuration
        this.options = {
            size: options.size || 80,
            stroke: options.stroke || 6,
            trialDurationMs: options.trialDurationMs || (5 * 60 * 60 * 1000), // 5 hours default
            onExpire: options.onExpire || (() => {}),
            showLabel: options.showLabel !== false, // default true
            className: options.className || '',
            ...options
        };

        this.trialExpiresAt = null;
        this.remaining = 0;
        this.timerInterval = null;
        this.isActive = false;

        this.init();
    }

    init() {
        this.render();
        this.setupGlobalCleanup();
    }

    setupGlobalCleanup() {
        // Prevent multiple timers by storing reference globally
        if (window.circularTrialTimer) {
            window.circularTrialTimer.stop();
        }
        window.circularTrialTimer = this;
    }

    render() {
        const { size, stroke } = this.options;
        const radius = (size - stroke) / 2;
        const circumference = 2 * Math.PI * radius;

        this.container.innerHTML = `
            <div class="circular-trial-timer ${this.options.className}" 
                 style="display: none; align-items: center; gap: 8px;">
                
                <!-- Circular Progress Ring -->
                <div class="timer-ring" style="position: relative; width: ${size}px; height: ${size}px;">
                    <svg width="${size}" height="${size}" style="transform: rotate(-90deg);">
                        <!-- Background ring -->
                        <circle 
                            cx="${size / 2}" 
                            cy="${size / 2}" 
                            r="${radius}"
                            stroke="rgba(255, 255, 255, 0.15)"
                            stroke-width="${stroke}"
                            fill="none" />
                        
                        <!-- Progress ring -->
                        <circle 
                            class="progress-ring"
                            cx="${size / 2}" 
                            cy="${size / 2}" 
                            r="${radius}"
                            stroke="#22d3ee"
                            stroke-width="${stroke}"
                            fill="none"
                            stroke-linecap="round"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${circumference}"
                            style="transition: stroke-dashoffset 1s ease, stroke 0.3s ease;" />
                    </svg>
                    
                    <!-- Digital time display -->
                    <div style="position: absolute; inset: 0; display: grid; place-items: center;">
                        <span class="timer-text" 
                              style="font-family: 'Courier New', monospace; 
                                     font-size: ${size > 60 ? '12px' : '10px'}; 
                                     letter-spacing: 1px; 
                                     color: white; 
                                     user-select: none;">
                            --:--:--
                        </span>
                    </div>
                </div>

                ${this.options.showLabel ? `
                <!-- Label pill -->
                <div class="timer-label" 
                     style="padding: 4px 12px; 
                            border-radius: 12px; 
                            background: rgba(255, 255, 255, 0.05); 
                            color: rgba(255, 255, 255, 0.8); 
                            font-size: 12px;">
                    Trial
                </div>
                ` : ''}
            </div>
        `;

        // Store references to elements we'll update
        this.timerElement = this.container.querySelector('.circular-trial-timer');
        this.progressRing = this.container.querySelector('.progress-ring');
        this.timerText = this.container.querySelector('.timer-text');
        
        // Calculate circumference for progress updates
        this.circumference = 2 * Math.PI * radius;
    }

    start(trialExpiresAt) {
        if (!trialExpiresAt) {
            console.warn('CircularTrialTimer: No expiration time provided');
            return;
        }

        this.trialExpiresAt = trialExpiresAt;
        this.isActive = true;
        
        // Show the timer
        if (this.timerElement) {
            this.timerElement.style.display = 'flex';
        }

        // Start the countdown
        this.updateTimer();
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        this.timerInterval = setInterval(() => this.updateTimer(), 1000);
    }

    stop() {
        this.isActive = false;
        
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        // Hide the timer
        if (this.timerElement) {
            this.timerElement.style.display = 'none';
        }
    }

    updateTimer() {
        if (!this.isActive || !this.trialExpiresAt) {
            return;
        }

        // Calculate remaining time
        let expireMs;
        if (typeof this.trialExpiresAt === 'number') {
            expireMs = this.trialExpiresAt;
        } else if (typeof this.trialExpiresAt === 'string') {
            // Handle ISO string with or without Z
            const normalizedTime = this.trialExpiresAt.replace(/Z$/, '+00:00');
            expireMs = new Date(normalizedTime).getTime();
        } else {
            expireMs = new Date(this.trialExpiresAt).getTime();
        }

        if (isNaN(expireMs)) {
            console.error('CircularTrialTimer: Invalid expiration time');
            this.stop();
            return;
        }

        const now = Date.now();
        this.remaining = Math.max(0, expireMs - now);

        if (this.remaining <= 0) {
            // Timer expired
            this.handleExpiration();
            return;
        }

        // Update display
        this.updateDisplay();
        this.updateProgress();
    }

    updateDisplay() {
        if (!this.timerText) return;

        const hours = Math.floor(this.remaining / (1000 * 60 * 60));
        const minutes = Math.floor((this.remaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((this.remaining % (1000 * 60)) / 1000);

        const timeString = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        this.timerText.textContent = timeString;
    }

    updateProgress() {
        if (!this.progressRing) return;

        // Calculate progress (0 to 1)
        const totalDuration = this.options.trialDurationMs;
        const elapsed = totalDuration - this.remaining;
        const progress = Math.min(1, Math.max(0, elapsed / totalDuration));

        // Update stroke color based on time remaining
        const remainingMinutes = this.remaining / (1000 * 60);
        let strokeColor = '#22d3ee'; // cyan (default)
        
        if (remainingMinutes < 10) {
            strokeColor = '#ef4444'; // red (critical)
        } else if (remainingMinutes < 30) {
            strokeColor = '#f59e0b'; // amber (warning)
        }

        // Update the progress ring
        const offset = this.circumference * (1 - progress);
        this.progressRing.style.strokeDashoffset = offset;
        this.progressRing.style.stroke = strokeColor;
    }

    handleExpiration() {
        this.isActive = false;
        
        if (this.timerText) {
            this.timerText.textContent = '00:00:00';
        }
        
        if (this.progressRing) {
            this.progressRing.style.stroke = '#ef4444';
            this.progressRing.style.strokeDashoffset = '0';
        }

        // Call expiration callback
        if (typeof this.options.onExpire === 'function') {
            this.options.onExpire();
        }

        // Auto-hide after 2 seconds
        setTimeout(() => {
            this.stop();
        }, 2000);
    }

    // Public methods
    isRunning() {
        return this.isActive && this.timerInterval !== null;
    }

    getRemainingTime() {
        return this.remaining;
    }

    destroy() {
        this.stop();
        if (this.container) {
            this.container.innerHTML = '';
        }
        if (window.circularTrialTimer === this) {
            window.circularTrialTimer = null;
        }
    }
}

// Global helper function for easy integration
window.createCircularTrialTimer = function(containerId, options = {}) {
    return new CircularTrialTimer(containerId, options);
};

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.circularTrialTimer) {
        window.circularTrialTimer.destroy();
    }
});