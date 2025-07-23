// SoulBridge AI - Login/Register System
console.log('SoulBridge AI Loading...');

// Enhanced password toggle function
function togglePassword(inputId = 'password') {
    console.log('Toggle password called for:', inputId);
    
    const input = document.getElementById(inputId);
    if (!input) {
        console.log('Input not found:', inputId);
        return;
    }
    
    // Find the toggle button that's in the same container as this input
    const container = input.closest('.password-container');
    const toggleBtn = container ? container.querySelector('.password-toggle') : null;
    
    if (!toggleBtn) {
        console.log('Toggle button not found for input:', inputId);
        return;
    }
    
    if (input.type === 'password') {
        input.type = 'text';
        toggleBtn.innerHTML = '🙈'; // Closed eye
        toggleBtn.setAttribute('aria-label', 'Hide password');
        console.log('Password shown for:', inputId);
    } else {
        input.type = 'password';
        toggleBtn.innerHTML = '👁️'; // Open eye
        toggleBtn.setAttribute('aria-label', 'Show password');
        console.log('Password hidden for:', inputId);
    }
}

// Make function global
window.togglePassword = togglePassword;

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
    let trialStatus = localStorage.getItem("soulbridgeai_trial");
    const trialStatusDisplay = document.getElementById("trialStatus");
    
    if (trialStatus) {
        let timePassed = Date.now() - parseInt(trialStatus);
        if (timePassed < 86400000) { // 24 hours
            if (trialStatusDisplay) trialStatusDisplay.innerText = "Trial Status: Active";
            return true;
        } else {
            localStorage.removeItem("soulbridgeai_trial");
            if (trialStatusDisplay) trialStatusDisplay.innerText = "Trial Status: Expired";
            return false;
        }
    } else {
        if (trialStatusDisplay) trialStatusDisplay.innerText = "Trial Status: None";
        return false;
    }
}

function startTrial() {
    let trialStatus = localStorage.getItem("soulbridgeai_trial");
    if (trialStatus) {
        alert("Trial already used.");
        return;
    }
    localStorage.setItem("soulbridgeai_trial", Date.now());
    alert("1-Day Free Trial Activated!");
    const trialStatusDisplay = document.getElementById("trialStatus");
    if (trialStatusDisplay) trialStatusDisplay.innerText = "Trial Status: Active";
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
    const isTrialActive = checkTrialStatus();
    
    if (!isPremium && !isTrialActive) {
        let messageLimit = parseInt(localStorage.getItem("soulbridgeai_messageLimit")) || 0;
        if (messageLimit <= 0) {
            alert("Message limit reached. Please subscribe to SoulBridge Plus or start a trial.");
            return;
        }
        messageLimit--;
        localStorage.setItem("soulbridgeai_messageLimit", messageLimit);
        updateMessageCount(messageLimit);
    }
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.className = 'message user-message';
    userDiv.innerHTML = `<strong>You:</strong> ${message}`;
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
        
        if (data.success) {
            aiDiv.innerHTML = `<strong>SoulBridge AI:</strong> ${data.response}`;
        } else {
            aiDiv.innerHTML = `<strong>SoulBridge AI:</strong> Sorry, I encountered an error.`;
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
window.startTrial = startTrial;
window.checkTrialStatus = checkTrialStatus;
window.initializeMessageLimit = initializeMessageLimit;
window.updateMessageCount = updateMessageCount;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - Setting up SoulBridge AI');
    
    // Initialize trial and message limits
    const messageLimit = initializeMessageLimit();
    updateMessageCount(messageLimit);
    checkTrialStatus();
    
    // Initialize password toggle buttons
    const passwordToggles = document.querySelectorAll('.password-toggle');
    console.log('Found', passwordToggles.length, 'password toggle buttons');
    
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