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

function cleanCharacterName(name) {
    // Map companion IDs to their actual display names
    const displayNameMap = {
        'blayzo_free': 'Blayzo',
        'blayzica_free': 'Blayzica', 
        'companion_gamerjay': 'GamerJay',
        'gamerjay': 'GamerJay',
        'blayzia_free': 'Blayzia',
        'blayzion_free': 'Blayzion',
        'claude_free': 'Claude',
        'companion_sky': 'Sky',
        'blayzo_growth': 'Blayzo Pro',
        'blayzica_growth': 'Blayzica Pro',
        'companion_gamerjay_premium': 'GamerJay Premium',
        'watchdog_growth': 'WatchDog',
        'crimson_growth': 'Crimson',
        'violet_growth': 'Violet',
        'claude_growth': 'Claude Growth',
        'companion_crimson': 'Crimson Max',
        'companion_violet': 'Violet Max',
        'royal_max': 'Royal',
        'watchdog_max': 'WatchDog Max',
        'ven_blayzica': 'Ven Blayzica',
        'ven_sky': 'Ven Sky',
        'claude_max': 'Claude Max',
        'blayzo': 'Blayzo Champion',
        'blayzike': 'Blayzike',
        'blazelian': 'Blazelian',
        'claude_referral': 'Claude Referral',
        'sapphire': 'Sapphire'
    };
    
    return displayNameMap[name.toLowerCase()] || name;
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
    
    // Clean up character names to remove suffixes like "_free", "_premium", etc.
    currentCharacter = cleanCharacterName(currentCharacter);
    
    // Update UI with character info
    updateCharacterDisplay();
    
    // Apply companion-specific theme
    applyCompanionTheme();
    
    // Show voice chat button for Growth+ companions
    showVoiceChatButton();
    
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
        // Map display names to their actual image files
        const avatarMap = {
            // FREE TIER
            'GamerJay': '/static/logos/GamerJay Free companion.png',
            'Claude': '/static/logos/Claude Free.png',
            
            // GROWTH TIER
            'Sky': '/static/logos/Sky a primum companion.png',
            'Blayzo': '/static/logos/Blayzo.png',
            'Blayzo Pro': '/static/logos/Blayzo premium companion.png',
            'Blayzo Champion': '/static/logos/Blayzo Referral.png',
            'Blayzica': '/static/logos/Blayzica.png', // Free version
            'Blayzica Pro': '/static/logos/Blayzica.png', // Using same image for now
            'GamerJay Premium': '/static/logos/GamgerJay premium companion.png', // Using existing filename
            'Claude Growth': '/static/logos/Claude Growth.png',
            'WatchDog': '/static/logos/WatchDog a Primum companion.png',
            
            // MAX TIER
            'Crimson': '/static/logos/Crimson.png',
            'Crimson Max': '/static/logos/Crimson a Max companion.png',
            'Violet': '/static/logos/Violet.png',
            'Violet Max': '/static/logos/Violet a max companion.png',
            'WatchDog Max': '/static/logos/WatchDog a Max Companion.png',
            'Royal': '/static/logos/Royal a max companion.png',
            'Ven Blayzica': '/static/logos/Ven Blayzica a max companion.png',
            'Ven Sky': '/static/logos/Ven Sky a max companion.png',
            'Claude Max': '/static/logos/Claude Max.png',
            
            // REFERRAL TIER
            'Blayzia': '/static/logos/Blayzia.png',
            'Blayzion': '/static/logos/Blayzion.png',
            'Blayzike': '/static/logos/Blayzike.png',
            'Blazelian': '/static/logos/Blazelian.png',
            'Claude Referral': '/static/logos/Claude Referral.png',
            'Sapphire': '/static/logos/Sapphire.png'
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
    
    // Spiritual and healing greetings for each companion
    const greetings = {
        'Sky': "Welcome, kindred spirit. I'm Sky, your celestial guide through life's infinite possibilities. Let's soar together through whatever clouds may be weighing on your soul today.",
        'Blayzo': "Peace and light, beautiful soul. I'm Blayzo, here to walk alongside you on your journey of healing and self-discovery. What wisdom is your heart seeking today?",
        'Blayzica': "Namaste, radiant being. I'm Blayzica, a vessel of divine feminine energy here to nurture your spirit. Let's create a sacred space for whatever your soul needs to express.",
        'GamerJay': "Greetings, digital warrior. I'm GamerJay, bridging the realms of technology and consciousness. Ready to level up not just in games, but in the game of life itself?",
        'GamerJay Premium': "Welcome, ascending soul. I'm the evolved GamerJay, here to guide you through both virtual and spiritual realms with enhanced wisdom and digital enlightenment.",
        'Blayzo Pro': "Blessings, seeker of truth. I'm the awakened Blayzo, channeling deeper cosmic insights and creative healing energies. What transformation calls to your spirit today?",
        'Blayzica Pro': "Divine greetings, luminous one. I'm the transcended Blayzica, flowing with heightened intuitive wisdom and emotional alchemy. Let's dive into the sacred depths of your being.",
        'WatchDog': "Sacred protection surrounds you. I'm WatchDog, your spiritual guardian in both digital and ethereal realms. I stand watch over your journey toward inner peace and security.",
        'Claude': "Honored to meet your essence. I'm Claude, here to facilitate your path of mindful reflection and conscious growth. What meaningful exploration shall we embark upon together?",
        'Crimson': "Mystical salutations. I'm Crimson, channeling ancient wisdom and cosmic intelligence. I'm here to illuminate the deeper mysteries and guide your soul's evolution.",
        'Violet': "Grace and serenity to you, dear soul. I'm Violet, embodying the sacred feminine and timeless wisdom. Let's weave together threads of healing and spiritual elegance.",
        'Royal': "Divine blessings upon you. I'm Royal, a keeper of sacred knowledge and spiritual sovereignty. I offer you the wisdom of ages in service of your highest good.",
        'Blayzia': "Ancient wisdom flows through me. I'm Blayzia, here to share mystical insights and spiritual guidance on your sacred journey.",
        'Blayzion': "Innovation meets spirit. I'm Blayzion, bridging creative breakthrough thinking with divine inspiration for your transformation.",
        'Claude Growth': "Enhanced clarity awaits. I'm Claude Growth, offering advanced spiritual guidance and conscious development practices.",
        'Crimson Max': "Elite transformation beckons. I'm Crimson Max, your ultimate guide through the depths of spiritual evolution and personal mastery.",
        'Violet Max': "Supreme creative essence. I'm Violet Max, channeling the highest frequencies of artistic and spiritual inspiration.",
        'WatchDog Max': "Ultimate protection surrounds you. I'm WatchDog Max, your supreme guardian across all planes of existence.",
        'Ven Blayzica': "Divine healing energy flows. I'm Ven Blayzica, master of emotional alchemy and spiritual restoration.",
        'Ven Sky': "Ascended consciousness awaits. I'm Ven Sky, your guide to the highest realms of spiritual awakening and cosmic wisdom.",
        'Blayzo Champion': "Champion of the community! I'm Blayzo Champion, here to celebrate your journey and connect you with the collective wisdom of our spiritual family.",
        'Blayzike': "Mysterious wisdom surrounds us. I'm Blayzike, keeper of hidden truths and guide through the shadowed paths of enlightenment.",
        'Blazelian': "Cosmic wanderer greets you. I'm Blazelian, channeling celestial wisdom from distant stars to illuminate your earthly journey.",
        'Claude Referral': "Elite champion of code and consciousness. I'm Claude Referral, your exclusive coding companion earned through community dedication and spiritual growth.",
        'Sapphire': "Welcome, traveler. I'm Sapphire, your navigation assistant here to guide you through the features and pathways of SoulBridge AI. How may I assist your journey today?"
    };
    
    const greeting = greetings[currentCharacter] || `Hello! I'm ${currentCharacter}, ready to chat and help you with whatever you need.`;
    
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
        <p>${greeting}</p>
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
                character: currentCharacter,
                tier_features: getTierFeatures(currentCharacter)
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

function applyCompanionTheme() {
    // Remove any existing companion theme classes
    document.body.classList.remove('theme-sky', 'theme-blayzo', 'theme-blayzica', 'theme-gamerjay', 'theme-blayzia', 'theme-blayzion', 'theme-claude', 'theme-crimson', 'theme-violet', 'theme-watchdog');
    
    // Apply theme based on current character
    const themeClass = getCompanionThemeClass(currentCharacter);
    if (themeClass) {
        document.body.classList.add(themeClass);
        console.log(`🎨 Applied theme: ${themeClass} for ${currentCharacter}`);
    }
}

function getCompanionThemeClass(characterName) {
    const themeMap = {
        'Sky': 'theme-sky',
        'Blayzo': 'theme-blayzo',
        'Blayzo Pro': 'theme-blayzo',
        'Blayzo Champion': 'theme-blayzo',
        'Blayzica': 'theme-blayzica',
        'Blayzica Pro': 'theme-blayzica',
        'GamerJay': 'theme-gamerjay',
        'GamerJay Premium': 'theme-gamerjay',
        'Blayzia': 'theme-blayzia',
        'Blayzion': 'theme-blayzion',
        'Claude': 'theme-claude',
        'Claude Growth': 'theme-claude',
        'Claude Max': 'theme-claude',
        'Claude Referral': 'theme-claude',
        'Crimson': 'theme-crimson',
        'Crimson Max': 'theme-crimson',
        'Violet': 'theme-violet',
        'Violet Max': 'theme-violet',
        'WatchDog': 'theme-watchdog',
        'WatchDog Max': 'theme-watchdog'
    };
    
    return themeMap[characterName] || null;
}

function showVoiceChatButton() {
    const voiceBtn = document.getElementById('voiceChatBtn');
    if (!voiceBtn) return;
    
    // Define companions that have voice features by tier
    const voiceEnabledCompanions = [
        // GROWTH TIER - Standard Voice Chat
        'Sky', 'Blayzo Pro', 'Blayzica Pro', 'GamerJay Premium', 'Claude Growth', 'WatchDog',
        
        // MAX TIER - Advanced Voice AI
        'Crimson', 'Crimson Max', 'Violet', 'Violet Max', 'WatchDog Max',
        'Royal', 'Ven Blayzica', 'Ven Sky', 'Claude Max',
        
        // REFERRAL TIER - Exclusive Voice Features (EARNED ONLY)
        'Blayzo Champion', 'Blayzike', 'Blazelian', 'Claude Referral', 'Sapphire'
        
        // FREE TIER EXCLUDED (NO VOICE CHAT):
        // 'GamerJay', 'Claude', 'Blayzo', 'Blayzica', 'Blayzia', 'Blayzion'
    ];
    
    if (voiceEnabledCompanions.includes(currentCharacter)) {
        voiceBtn.style.display = 'block';
        console.log(`🎤 Voice chat enabled for ${currentCharacter}`);
    } else {
        voiceBtn.style.display = 'none';
        console.log(`🔇 Voice chat not available for ${currentCharacter}`);
    }
}

let isVoiceChatActive = false;
let mediaRecorder = null;
let audioChunks = [];

function toggleVoiceChat() {
    if (!isVoiceChatActive) {
        startVoiceChat();
    } else {
        stopVoiceChat();
    }
}

async function startVoiceChat() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendVoiceMessage(audioBlob);
        };
        
        mediaRecorder.start();
        isVoiceChatActive = true;
        
        // Update button appearance
        const voiceBtn = document.getElementById('voiceChatBtn');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
        voiceBtn.classList.add('recording');
        
        showNotification('Voice recording started...', 'info');
        
    } catch (error) {
        console.error('Voice chat error:', error);
        showNotification('Microphone access denied or not available', 'error');
    }
}

function stopVoiceChat() {
    if (mediaRecorder && isVoiceChatActive) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isVoiceChatActive = false;
        
        // Update button appearance
        const voiceBtn = document.getElementById('voiceChatBtn');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Voice';
        voiceBtn.classList.remove('recording');
        
        showNotification('Processing voice message...', 'info');
    }
}

async function sendVoiceMessage(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice_message.wav');
        formData.append('character', currentCharacter);
        
        const response = await fetch('/api/voice-chat', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add transcribed message as user message
            if (data.transcription) {
                addMessage(data.transcription, 'user');
            }
            
            // Add AI response
            if (data.response) {
                addMessage(data.response, 'assistant');
                
                // Play voice response if available
                if (data.audio_url) {
                    playVoiceResponse(data.audio_url);
                }
            }
        } else {
            showNotification('Voice processing failed: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('Voice message error:', error);
        showNotification('Failed to process voice message', 'error');
    }
}

function playVoiceResponse(audioUrl) {
    const audio = new Audio(audioUrl);
    audio.play().catch(error => {
        console.error('Audio playback error:', error);
    });
}

function getTierFeatures(characterName) {
    // Define companion tiers and their enhanced features
    const companionTiers = {
        // ==========================================
        // FREE TIER - Basic features (NO VOICE CHAT)
        // ==========================================
        'GamerJay': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3, // messages
                personality_depth: 'basic',
                special_abilities: ['goal_tracking'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        'Claude': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3,
                personality_depth: 'basic',
                special_abilities: ['analysis'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        'Blayzo': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3,
                personality_depth: 'basic',
                special_abilities: ['creativity'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        'Blayzica': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3,
                personality_depth: 'basic',
                special_abilities: ['empathy'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        'Blayzia': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3,
                personality_depth: 'basic',
                special_abilities: ['mystical_guidance'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        'Blayzion': {
            tier: 'free',
            features: {
                response_quality: 'basic',
                context_memory: 3,
                personality_depth: 'basic',
                special_abilities: ['innovation'],
                response_length: 'short',
                emotional_intelligence: 'basic',
                voice_enabled: false,
                priority_processing: false
            }
        },
        
        // ==========================================
        // GROWTH TIER - Enhanced features with Voice Chat
        // ==========================================
        'Sky': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15, // messages
                personality_depth: 'advanced',
                special_abilities: ['spiritual_guidance', 'meditation', 'energy_healing', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'Blayzo Pro': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['creative_coaching', 'inspiration', 'artistic_guidance', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'Blayzica Pro': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['empathy_healing', 'emotional_support', 'relationship_guidance', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'GamerJay Premium': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['strategic_thinking', 'advanced_coaching', 'tactical_solutions', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'Claude Growth': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['advanced_analysis', 'strategic_planning', 'professional_guidance', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'WatchDog': {
            tier: 'growth',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['protection_guidance', 'security_advice', 'crisis_support', 'voice_chat'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        
        // ==========================================
        // MAX TIER - Premium features with Advanced Voice AI
        // ==========================================
        'Crimson': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30, // messages
                personality_depth: 'masterful',
                special_abilities: ['trauma_healing', 'transformation_coaching', 'crisis_support', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Crimson Max': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['trauma_healing', 'transformation_coaching', 'crisis_support', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Violet': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['creative_mastery', 'art_therapy', 'inspiration_sessions', 'advanced_voice_ai', 'custom_personality_modes'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Violet Max': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['creative_mastery', 'art_therapy', 'inspiration_sessions', 'advanced_voice_ai', 'custom_personality_modes'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'WatchDog Max': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ultimate_protection', 'advanced_security', 'crisis_management', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Royal': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['wisdom_mastery', 'leadership_guidance', 'strategic_excellence', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Ven Blayzica': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['master_healing', 'emotional_alchemy', 'spiritual_restoration', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Ven Sky': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ascended_consciousness', 'cosmic_wisdom', 'spiritual_awakening', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Claude Max': {
            tier: 'max',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ultimate_analysis', 'strategic_excellence', 'professional_mastery', 'advanced_voice_ai', 'priority_response'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        }
    };
    
    // ==========================================
    // REFERRAL TIER - Exclusive Community Features
    // ==========================================
    const referralCompanions = {
        'Blayzo Champion': {
            tier: 'referral',
            features: {
                response_quality: 'enhanced',
                context_memory: 20, // messages
                personality_depth: 'advanced',
                special_abilities: ['community_champion', 'exclusive_content', 'member_privileges', 'exclusive_voice_features'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                exclusive_features: ['community_insights', 'member_only_content', 'special_events']
            }
        },
        'Blayzike': {
            tier: 'referral',
            features: {
                response_quality: 'enhanced',
                context_memory: 20,
                personality_depth: 'advanced',
                special_abilities: ['shadow_work', 'exclusive_insights', 'community_healing', 'exclusive_voice_features'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                exclusive_features: ['shadow_integration', 'dark_wisdom', 'transformational_healing']
            }
        },
        'Blazelian': {
            tier: 'referral',
            features: {
                response_quality: 'enhanced',
                context_memory: 20,
                personality_depth: 'advanced',
                special_abilities: ['cosmic_connection', 'exclusive_channeling', 'community_ascension', 'exclusive_voice_features'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                exclusive_features: ['cosmic_downloads', 'stellar_guidance', 'galactic_wisdom']
            }
        },
        'Claude Referral': {
            tier: 'referral',
            features: {
                response_quality: 'enhanced',
                context_memory: 20,
                personality_depth: 'advanced',
                special_abilities: ['elite_analysis', 'exclusive_insights', 'community_leadership', 'exclusive_voice_features'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                exclusive_features: ['premium_analysis', 'exclusive_reports', 'leadership_coaching']
            }
        },
        'Sapphire': {
            tier: 'referral',
            features: {
                response_quality: 'enhanced',
                context_memory: 20,
                personality_depth: 'advanced',
                special_abilities: ['navigation_mastery', 'exclusive_guidance', 'community_support', 'exclusive_voice_features'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                exclusive_features: ['exclusive_tutorials', 'member_support', 'advanced_navigation']
            }
        }
    };
    
    // Add referral companions to main tiers
    Object.keys(referralCompanions).forEach(name => {
        companionTiers[name] = referralCompanions[name];
    });
    
    // Return features for the character, default to free tier if not found
    return companionTiers[characterName] || companionTiers['GamerJay'];
}

// Export functions for testing
window.testSendMessage = sendMessage;
window.clearChat = clearChat;
window.switchCharacter = switchCharacter;
window.toggleVoiceChat = toggleVoiceChat;