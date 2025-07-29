/**
 * CHAT PAGE - CLEAN JAVASCRIPT
 * Extracted from 8,204 lines of bloated mess for performance and maintainability
 */

// Global variables
let currentCharacter = null;
let isProcessing = false;
let chatHistory = [];

// Initialize chat on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 SoulBridge AI Chat Page Loaded');
    initializeChat();
});

function initializeChat() {
    console.log('💬 Initializing chat system...');
    
    // Load character info
    loadCharacterInfo();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load chat history
    loadChatHistory();
    
    // Show welcome message
    showWelcomeMessage();
    
    // Setup auto-resize for textarea
    setupTextareaResize();
    
    console.log('✅ Chat system initialized');
}

function loadCharacterInfo() {
    // Get character from URL params, server-side template, or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const urlCharacter = urlParams.get('companion');
    const serverCharacter = document.querySelector('[data-character]')?.dataset.character;
    const storageCharacter = localStorage.getItem('selectedCharacter');
    
    // Priority: URL > Server > Storage
    if (urlCharacter) {
        currentCharacter = urlCharacter.charAt(0).toUpperCase() + urlCharacter.slice(1);
        localStorage.setItem('selectedCharacter', currentCharacter);
        console.log('🔄 Character loaded from URL:', currentCharacter);
    } else {
        currentCharacter = serverCharacter || storageCharacter || 'AI Assistant';
        console.log('🤖 Character loaded from storage/server:', currentCharacter);
    }
    
    // Update UI with character info
    updateCharacterDisplay();
    
    // Show trial banner if this is a trial session
    if (urlParams.get('trial') === 'true') {
        checkTrialStatus();
    }
    
    // Show selection success message
    const selectionTime = localStorage.getItem('companionSelectionTime');
    if (selectionTime && Date.now() - parseInt(selectionTime) < 5000) {
        setTimeout(() => {
            showNotification(`Welcome! You're now chatting with ${currentCharacter}`, 'success');
        }, 500);
        localStorage.removeItem('companionSelectionTime');
    }
}

function updateCharacterDisplay() {
    const characterName = document.querySelector('.character-details h2');
    const characterAvatar = document.querySelector('.character-avatar');
    
    if (characterName) {
        characterName.textContent = currentCharacter;
    }
    
    if (characterAvatar) {
        // Set character avatar based on character name
        const avatarMap = {
            'GamerJay': '/static/logos/GamerJay Free companion.png',
            'Sky': '/static/logos/Sky a primum companion.png',
            'Crimson': '/static/logos/Crimson a Max companion.png',
            'Violet': '/static/logos/Violet a max companion.png',
            'Blayzo': '/static/logos/Blayzo.png'
        };
        
        characterAvatar.src = avatarMap[currentCharacter] || '/static/logos/IntroLogo.png';
        characterAvatar.alt = currentCharacter;
    }
}

function setupEventListeners() {
    // Send button click
    const sendButton = document.querySelector('.send-button');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Enter key in textarea
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Update send button state based on input
        messageInput.addEventListener('input', updateSendButtonState);
    }
    
    // Quick response buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('quick-response')) {
            const message = e.target.textContent;
            sendQuickResponse(message);
        }
    });
}

function setupTextareaResize() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

function updateSendButtonState() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.querySelector('.send-button');
    
    if (messageInput && sendButton) {
        const hasContent = messageInput.value.trim().length > 0;
        sendButton.disabled = !hasContent || isProcessing;
    }
}

function showWelcomeMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    // Check if welcome message already exists
    if (messagesContainer.querySelector('.welcome-message')) return;
    
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
        <h3>👋 Welcome to SoulBridge AI!</h3>
        <p>I'm ${currentCharacter}, your AI companion. I'm here to listen, support, and help you on your wellness journey. Feel free to share what's on your mind or ask me anything!</p>
    `;
    
    messagesContainer.appendChild(welcomeDiv);
    scrollToBottom();
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput || isProcessing) return;
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    console.log('📤 Sending message:', message);
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    updateSendButtonState();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        isProcessing = true;
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                character: currentCharacter
            })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        hideTypingIndicator();
        
        if (data.success && data.response) {
            console.log('📥 Received response:', data.response);
            addMessage(data.response, 'assistant');
        } else {
            console.error('❌ API error:', data.error);
            addMessage('I apologize, but I encountered an error. Please try again.', 'assistant', true);
        }
        
    } catch (error) {
        console.error('❌ Network error:', error);
        hideTypingIndicator();
        addMessage('I\'m having trouble connecting. Please check your internet connection and try again.', 'assistant', true);
    } finally {
        isProcessing = false;
        updateSendButtonState();
    }
}

function sendQuickResponse(message) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = message;
        sendMessage();
    }
}

function addMessage(content, sender, isError = false) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content ${isError ? 'error' : ''}">
            ${content}
            <div class="message-timestamp">${timestamp}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    
    // Store in chat history
    chatHistory.push({
        content: content,
        sender: sender,
        timestamp: new Date().toISOString(),
        isError: isError
    });
    
    scrollToBottom();
    saveChatHistory();
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    // Remove existing typing indicator
    hideTypingIndicator();
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <span>${currentCharacter} is typing...</span>
    `;
    
    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function loadChatHistory() {
    try {
        const saved = localStorage.getItem(`chatHistory_${currentCharacter}`);
        if (saved) {
            chatHistory = JSON.parse(saved);
            
            // Restore messages to UI
            const messagesContainer = document.getElementById('chatMessages');
            if (messagesContainer && chatHistory.length > 0) {
                chatHistory.forEach(msg => {
                    if (!msg.isWelcome) { // Don't restore welcome messages
                        addMessageToUI(msg.content, msg.sender, msg.isError, msg.timestamp);
                    }
                });
            }
        }
    } catch (error) {
        console.warn('⚠️ Error loading chat history:', error);
        chatHistory = [];
    }
}

function saveChatHistory() {
    try {
        localStorage.setItem(`chatHistory_${currentCharacter}`, JSON.stringify(chatHistory));
    } catch (error) {
        console.warn('⚠️ Error saving chat history:', error);
    }
}

function addMessageToUI(content, sender, isError, timestamp) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const displayTime = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 
                       new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content ${isError ? 'error' : ''}">
            ${content}
            <div class="message-timestamp">${displayTime}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}

function clearChat() {
    if (confirm('Are you sure you want to clear this conversation?')) {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        chatHistory = [];
        saveChatHistory();
        showWelcomeMessage();
        
        console.log('🗑️ Chat cleared');
    }
}

function switchCharacter() {
    if (confirm('Switch to a different AI companion? This will take you to the selection page.')) {
        // Clear current selection but preserve chat history
        localStorage.removeItem('selectedCharacter');
        localStorage.removeItem('companionSelectionTime');
        localStorage.setItem('switchingFromChat', 'true');
        
        showNotification('Switching companions...', 'info');
        setTimeout(() => {
            window.location.href = '/companion-selection';
        }, 600);
    }
}

function showQuickResponses() {
    const inputArea = document.querySelector('.chat-input-area');
    if (!inputArea) return;
    
    // Check if quick responses already exist
    if (inputArea.querySelector('.quick-responses')) return;
    
    const quickResponsesDiv = document.createElement('div');
    quickResponsesDiv.className = 'quick-responses';
    
    const responses = [
        'How are you today?',
        'I need some advice',
        'Tell me something inspiring',
        'Help me with stress',
        'What should I do?'
    ];
    
    responses.forEach(response => {
        const button = document.createElement('button');
        button.className = 'quick-response';
        button.textContent = response;
        quickResponsesDiv.appendChild(button);
    });
    
    inputArea.insertBefore(quickResponsesDiv, inputArea.querySelector('.input-container'));
}

// Initialize quick responses after a short delay
setTimeout(showQuickResponses, 2000);

// Trial system integration
function checkTrialStatus() {
    const trialActive = localStorage.getItem('trialActive') === 'true';
    const trialExpiry = localStorage.getItem('trialExpiry');
    
    if (trialActive && trialExpiry) {
        const timeRemaining = parseInt(trialExpiry) - Date.now();
        if (timeRemaining > 0) {
            showTrialBanner(timeRemaining);
        } else {
            // Trial expired
            localStorage.removeItem('trialActive');
            localStorage.removeItem('trialExpiry');
        }
    }
}

function showTrialBanner(timeRemaining) {
    const header = document.querySelector('.chat-header');
    if (!header || header.querySelector('.trial-banner')) return;
    
    const banner = document.createElement('div');
    banner.className = 'trial-banner';
    
    const updateTimer = () => {
        const remaining = parseInt(localStorage.getItem('trialExpiry')) - Date.now();
        if (remaining <= 0) {
            banner.remove();
            return;
        }
        
        const hours = Math.floor(remaining / (1000 * 60 * 60));
        const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
        
        banner.innerHTML = `
            ⭐ Premium Trial Active - Time Remaining: 
            <span class="trial-timer">${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}</span>
        `;
    };
    
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
    
    // Clean up timer when banner is removed
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.removedNodes.forEach((node) => {
                if (node === banner) {
                    clearInterval(timerInterval);
                    observer.disconnect();
                }
            });
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    header.parentNode.insertBefore(banner, header);
}

// Initialize trial status check
checkTrialStatus();

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        max-width: 300px;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        ${type === 'success' ? 'background: linear-gradient(135deg, #4CAF50, #45a049);' : ''}
        ${type === 'error' ? 'background: linear-gradient(135deg, #f44336, #d32f2f);' : ''}
        ${type === 'info' ? 'background: linear-gradient(135deg, #2196F3, #1976D2);' : ''}
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.style.transform = 'translateX(0)', 100);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}

// Export functions for testing
window.testSendMessage = sendMessage;
window.clearChat = clearChat;
window.switchCharacter = switchCharacter;