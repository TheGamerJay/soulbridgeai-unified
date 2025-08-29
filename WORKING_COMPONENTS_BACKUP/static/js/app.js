// SoulBridge AI - Login/Register System
console.log('SoulBridge AI Loading...');

// Simple toast notification system (shared)
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

// Password toggle function DISABLED - Universal Button Fix handles this
// function togglePassword(inputId = 'password') {
//     // Disabled to prevent conflicts with Universal Button Fix
//     console.log('app.js togglePassword disabled - Universal Button Fix handling');
// }

// togglePassword function moved to Universal Button Fix to prevent conflicts

// Trial and message limit management
function initializeMessageLimit() {
    let messageLimit = 5;
    let lastMessageReset = localStorage.getItem("soulbridgeai_lastReset");
    const now = new Date().toDateString();
    
    if (lastMessageReset !== now) {
        localStorage.setItem("soulbridgeai_lastReset", now);
        messageLimit = 5;
        localStorage.setItem("soulbridgeai_messageLimit", messageLimit);
    } else {
        const storedLimit = localStorage.getItem("soulbridgeai_messageLimit");
        if (storedLimit !== null) {
            messageLimit = parseInt(storedLimit);
        }
    }
    
    return messageLimit;
}

function updateMessageCount(limit) {
    const messageCountDisplay = document.getElementById("messageCount");
    if (messageCountDisplay) {
        messageCountDisplay.textContent = limit;
    }
}

function checkTrialStatus() {
    // REMOVED: localStorage-based trial logic
    // Trial status is now controlled by backend and new_trial_system.js
    console.log('⚠️ OLD checkTrialStatus() called - trial logic moved to backend');
    return false; // Always return false since this is legacy
}

function legacyStartTrial() {
    // LEGACY: This is the old implementation, kept for compatibility
    console.log('⚠️ LEGACY startTrial() called - trial logic moved to tiers.js');
    showToast('Trial system has been updated. Please use the new trial buttons.', 'warning');
}

// Only assign to window.startTrial if it doesn't already exist (preserve tiers.js implementation)
if (typeof window.startTrial === 'undefined') {
    window.startTrial = legacyStartTrial;
}

// Chat functionality for dashboard
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('chatMessages');
    
    const message = input?.value?.trim();
    if (!message || sendBtn?.disabled) return;
    
    // Check message limit for non-premium users
    const isPremium = localStorage.getItem('isPremium') === 'true';
    const isTrialActive = false; // Legacy - always false since trial is backend-driven
    
    if (!isPremium && !isTrialActive) {
        let messageLimit = parseInt(localStorage.getItem("soulbridgeai_messageLimit")) || 0;
        if (messageLimit <= 0) {
            showToast("Message limit reached. Please subscribe to SoulBridge Plus or start a trial.", 'warning');
            return;
        }
        messageLimit--;
        localStorage.setItem("soulbridgeai_messageLimit", messageLimit);
        updateMessageCount(messageLimit);
    }
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'message user-message';
    const userLabel = document.createElement('strong');
    userLabel.textContent = 'You: ';
    userDiv.appendChild(userLabel);
    userDiv.appendChild(document.createTextNode(message));
    messagesContainer.appendChild(userDiv);
    
    // Clear input and disable button
    input.value = '';
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',  // ✅ Include session cookies
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        const aiDiv = document.createElement('div');
        aiDiv.className = 'message ai-message';
        
        const aiLabel = document.createElement('strong');
        aiLabel.textContent = 'SoulBridge AI: ';
        aiDiv.appendChild(aiLabel);
        
        if (data.success) {
            aiDiv.appendChild(document.createTextNode(data.response));
        } else {
            aiDiv.appendChild(document.createTextNode('Sorry, I encountered an error.'));
        }
        
        messagesContainer.appendChild(aiDiv);
        
    } catch (error) {
        console.error('Chat error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message ai-message';
        errorDiv.innerHTML = `<strong>SoulBridge AI:</strong> Connection error. Please try again.`;
        messagesContainer.appendChild(errorDiv);
    }
    
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    input.focus();
}

// Logout function
async function logout() {
    try {
        const response = await fetch('/logout', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
}

// Make functions global
window.sendMessage = sendMessage;
window.logout = logout;
// window.startTrial is handled by tiers.js - don't override it
window.checkTrialStatus = checkTrialStatus;
window.initializeMessageLimit = initializeMessageLimit;
window.updateMessageCount = updateMessageCount;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - Setting up SoulBridge AI');
    
    // Initialize message limits (trial logic removed - handled by backend)
    const messageLimit = initializeMessageLimit();
    updateMessageCount(messageLimit);
    // REMOVED: checkTrialStatus() - trial logic moved to backend
    
    // Password toggle initialization DISABLED - Universal Button Fix handles this
    // const passwordToggles = document.querySelectorAll('.password-toggle');
    console.log('Password toggle handling moved to Universal Button Fix');
    
    // Focus management
    const usernameInput = document.getElementById('username') || document.getElementById('username_or_email');
    if (usernameInput) {
        usernameInput.focus();
    }
    
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.focus();
        // Enter key to send
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    console.log('SoulBridge AI setup complete');
});

console.log('SoulBridge AI Simple Auth System Loaded! 🌉');