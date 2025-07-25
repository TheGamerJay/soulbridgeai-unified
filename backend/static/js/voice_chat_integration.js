// === Voice Chat Integration Example ===
// Use this code to integrate premium voice chat gating in your chat interface

class VoiceChatManager {
    constructor() {
        this.currentCompanion = null;
        this.isPaid = false;
        this.hasUnlockedPremium = false;
        this.voicePreviewTimeRemaining = 0;
    }

    // Initialize from localStorage or session
    initialize() {
        // Check if user has premium subscription
        this.isPaid = localStorage.getItem('soulbridge_payment_confirmed') === 'true';
        this.hasUnlockedPremium = localStorage.getItem('soulbridge_subscription') === 'plus';
        
        // Get voice preview time from localStorage (if implemented)
        this.voicePreviewTimeRemaining = parseInt(localStorage.getItem('voice_preview_time') || '0');
        
        console.log('Voice Chat Manager initialized:', {
            isPaid: this.isPaid,
            hasUnlockedPremium: this.hasUnlockedPremium,
            voicePreviewTimeRemaining: this.voicePreviewTimeRemaining
        });
    }

    // Check voice chat access for current companion
    async checkVoiceChatAccess(companion) {
        this.currentCompanion = companion;
        
        try {
            const response = await fetch('/api/check-voice-chat-access', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    companion: companion,
                    is_paid: this.isPaid,
                    has_unlocked_premium: this.hasUnlockedPremium,
                    voice_preview_time_remaining: this.voicePreviewTimeRemaining
                })
            });

            const result = await response.json();
            console.log('Voice chat access result:', result);
            
            // Handle different access levels
            this.handleVoiceChatAccess(result);
            
            return result;
            
        } catch (error) {
            console.error('Error checking voice chat access:', error);
            return {
                voice_chat: 'error',
                access: false,
                message: 'Error checking voice chat access'
            };
        }
    }

    // Handle voice chat access response
    handleVoiceChatAccess(result) {
        const voiceButton = document.getElementById('voice-chat-button');
        const voiceStatus = document.getElementById('voice-status');
        
        if (!voiceButton || !voiceStatus) {
            console.warn('Voice chat UI elements not found');
            return;
        }

        switch (result.voice_chat) {
            case 'unlimited':
                voiceButton.disabled = false;
                voiceButton.textContent = '🎤 Voice Chat';
                voiceButton.className = 'voice-btn unlimited';
                voiceStatus.textContent = 'Unlimited voice chat available';
                voiceStatus.className = 'voice-status success';
                break;

            case 'preview':
                voiceButton.disabled = false;
                voiceButton.textContent = `🎤 Voice Chat (${result.time_remaining}min)`;
                voiceButton.className = 'voice-btn preview';
                voiceStatus.textContent = result.message;
                voiceStatus.className = 'voice-status warning';
                break;

            case 'locked':
                voiceButton.disabled = true;
                voiceButton.textContent = '🔒 Voice Chat Locked';
                voiceButton.className = 'voice-btn locked';
                voiceStatus.innerHTML = `
                    ${result.message}
                    <a href="${result.upgrade_url}" class="upgrade-link">Upgrade Now</a>
                `;
                voiceStatus.className = 'voice-status error';
                break;

            case 'disabled':
                voiceButton.disabled = true;
                voiceButton.textContent = '❌ Voice Chat Unavailable';
                voiceButton.className = 'voice-btn disabled';
                voiceStatus.textContent = result.message;
                voiceStatus.className = 'voice-status info';
                break;

            default:
                voiceButton.disabled = true;
                voiceButton.textContent = '⚠️ Voice Chat Error';
                voiceButton.className = 'voice-btn error';
                voiceStatus.textContent = result.message;
                voiceStatus.className = 'voice-status error';
        }
    }

    // Start voice chat (implement your actual voice chat logic here)
    async startVoiceChat() {
        if (!this.currentCompanion) {
            console.error('No companion selected');
            return;
        }

        // Check access first
        const access = await this.checkVoiceChatAccess(this.currentCompanion);
        
        if (!access.access) {
            alert(access.message);
            return;
        }

        // Start voice chat logic here
        console.log('Starting voice chat with', this.currentCompanion);
        
        // If using preview time, start countdown
        if (access.voice_chat === 'preview') {
            this.startPreviewCountdown(access.time_remaining);
        }
        
        // TODO: Implement actual voice chat functionality
        alert('Voice chat would start here!');
    }

    // Preview time countdown
    startPreviewCountdown(minutes) {
        let timeRemaining = minutes * 60; // Convert to seconds
        
        const countdown = setInterval(() => {
            timeRemaining--;
            
            if (timeRemaining <= 0) {
                clearInterval(countdown);
                this.voicePreviewTimeRemaining = 0;
                localStorage.setItem('voice_preview_time', '0');
                
                // Re-check access to update UI
                this.checkVoiceChatAccess(this.currentCompanion);
                
                alert('Voice chat preview time expired! Upgrade to continue.');
            } else {
                // Update remaining time
                this.voicePreviewTimeRemaining = Math.ceil(timeRemaining / 60);
                localStorage.setItem('voice_preview_time', this.voicePreviewTimeRemaining.toString());
            }
        }, 1000);
    }
}

// === Usage Example ===
// Initialize voice chat manager
const voiceChatManager = new VoiceChatManager();

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    voiceChatManager.initialize();
    
    // Example: Check access when companion is selected
    const companionSelect = document.getElementById('companion-select');
    if (companionSelect) {
        companionSelect.addEventListener('change', (e) => {
            const selectedCompanion = e.target.value;
            voiceChatManager.checkVoiceChatAccess(selectedCompanion);
        });
    }
    
    // Example: Start voice chat when button is clicked
    const voiceButton = document.getElementById('voice-chat-button');
    if (voiceButton) {
        voiceButton.addEventListener('click', () => {
            voiceChatManager.startVoiceChat();
        });
    }
});

// === HTML Example ===
/*
<div class="voice-chat-container">
    <select id="companion-select">
        <option value="">Select Companion</option>
        <option value="Blayzo">Blayzo (Free)</option>
        <option value="Blayzica">Blayzica (Free)</option>
        <option value="Blayzion">Blayzion (Premium)</option>
        <option value="Blayzia">Blayzia (Premium)</option>
        <option value="Crimson">Crimson (Premium)</option>
        <option value="Violet">Violet (Premium)</option>
    </select>
    
    <button id="voice-chat-button" class="voice-btn" disabled>
        Select Companion
    </button>
    
    <div id="voice-status" class="voice-status">
        Select a companion to check voice chat availability
    </div>
</div>
*/

// === CSS Example ===
/*
.voice-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.voice-btn.unlimited {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
}

.voice-btn.preview {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
}

.voice-btn.locked {
    background: #6b7280;
    color: #9ca3af;
    cursor: not-allowed;
}

.voice-btn.disabled {
    background: #374151;
    color: #6b7280;
    cursor: not-allowed;
}

.voice-status {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
}

.voice-status.success { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.voice-status.warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.voice-status.error { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.voice-status.info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }

.upgrade-link {
    color: #22d3ee;
    text-decoration: none;
    font-weight: 600;
    margin-left: 8px;
}
*/