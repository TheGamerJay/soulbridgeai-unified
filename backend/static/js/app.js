// SoulBridge AI - Login/Register System
console.log('SoulBridge AI Loading...');

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
    let trialStatus = localStorage.getItem("soulbridgeai_trial");
    const trialStatusDisplay = document.getElementById("trialStatus");
    
        if (trialStatus) {
            // 5 hours in milliseconds
            const TRIAL_DURATION_MS = 5 * 60 * 60 * 1000;
            let timePassed = Date.now() - parseInt(trialStatus);
            if (timePassed < TRIAL_DURATION_MS) {
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
        if (messageLimit <= 0) {
    userDiv.innerHTML = `<strong>You:</strong> ${message}`;
    messagesContainer.appendChild(userDiv);
    
    // Clear input and disable button
    input.value = '';
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
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