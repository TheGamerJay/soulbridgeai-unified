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

// Re-initialize character display when returning to page
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        console.log('🔄 Page became visible, refreshing character display');
        // Ensure character info is loaded before updating display
        if (!currentCharacter) {
            loadCharacterInfo();
        } else {
            updateCharacterDisplay();
        }
    }
});

// Also handle when window gets focus (for better compatibility)
window.addEventListener('focus', function() {
    console.log('🔄 Window focused, refreshing character display');
    // Ensure character info is loaded before updating display
    if (!currentCharacter) {
        loadCharacterInfo();
    } else {
        updateCharacterDisplay();
    }
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
        'gamerjay_free': 'GamerJay',
        'gamerjay_bronze': 'GamerJay Bronze',
        'blayzo_bronze': 'Blayzo Bronze',
        'blayzica_bronze': 'Blayzica',
        'claude_bronze': 'Claude',
        'blayzia_bronze': 'Blayzia',
        'blayzion_bronze': 'Blayzion',
        'lumen_bronze': 'Lumen',
        'blayzo2_bronze': 'Blayzo.2',
        'gamerjay': 'GamerJay',
        'blayzia_free': 'Blayzia',
        'blayzion_free': 'Blayzion',
        'claude_free': 'Claude',
        'lumen_free': 'Lumen',
        'blayzo2_free': 'Blayzo.2',
        'companion_sky': 'Sky',
        'blayzo_growth': 'Blayzo Pro',
        'blayzica_growth': 'Blayzica Pro',
        'companion_gamerjay_premium': 'GamerJay Premium',
        'gamerjay_premium': 'GamerJay Premium',  // Missing mapping!
        'blayzo_premium': 'Blayzo Pro',  // Missing mapping!
        'watchdog_growth': 'WatchDog',
        'crimson_growth': 'Crimson',
        'violet_growth': 'Violet',
        'claude_growth': 'Claude Growth',
        'sky_silver': 'Sky',
        'gamerjay_silver': 'GamerJay Silver',
        'claude_silver': 'Claude Growth', 
        'blayzo_silver': 'Blayzo Pro',
        'blayzica_silver': 'Blayzica Pro',
        'watchdog_silver': 'WatchDog',
        'rozia_silver': 'Rozia',
        'lumen_silver': 'Lumen',
        'companion_crimson': 'Crimson Max',
        'companion_violet': 'Violet Max',
        'royal_max': 'Royal',
        'watchdog_max': 'WatchDog Max',
        'ven_blayzica': 'Ven Blayzica',
        'ven_sky': 'Ven Sky',
        'claude_max': 'Claude Max',
        'crimson_gold': 'Crimson Max',
        'violet_gold': 'Violet Max',
        'claude_gold': 'Claude Max',
        'royal_gold': 'Royal',
        'ven_blayzica_gold': 'Ven Blayzica',
        'ven_sky_gold': 'Ven Sky',
        'watchdog_gold': 'WatchDog Max',
        'violet2_gold': 'Violet Max',
        'blayzo': 'Blayzo Champion',
        'blayzike': 'Blayzike',
        'blazelian': 'Blazelian',
        'claude_referral': 'Claude Referral',
        'blayzo_skin': 'Blayzo Special Skin',  // Missing referral companion!
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
        // Clean immediately to prevent race condition glitches
        currentCharacter = cleanCharacterName(currentCharacter);
        localStorage.setItem('selectedCharacter', currentCharacter);
        console.log('🔄 Character loaded from URL:', currentCharacter);
    } else {
        currentCharacter = serverCharacter || storageCharacter || 'AI Assistant';
        // Clean immediately to prevent race condition glitches  
        currentCharacter = cleanCharacterName(currentCharacter);
        console.log('🤖 Character loaded from storage/server:', currentCharacter);
    }
    
    // Update UI with character info
    updateCharacterDisplay();
    
    // Apply companion-specific theme
    applyCompanionTheme();
    
    // Show voice chat button for Growth+ companions
    showVoiceChatButton();
    
    
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
    // Ensure we have a current character
    if (!currentCharacter) {
        console.log('⚠️ No current character set, loading character info...');
        loadCharacterInfo();
        return;
    }
    
    const characterName = document.querySelector('.character-details h2');
    const characterAvatar = document.querySelector('.character-avatar');
    
    if (characterName) {
        characterName.textContent = currentCharacter;
        console.log('📝 Updated character name to:', currentCharacter);
    }
    
    if (characterAvatar) {
        // Map display names to their actual image files
        const avatarMap = {
            // BRONZE TIER (Display Names)
            'GamerJay': '/static/logos/GamerJay_Free_companion.png', // URL-safe filename
            'GamerJay Bronze': '/static/logos/GamerJay_Free_companion.png', // URL-safe filename
            'Blayzo Bronze': '/static/logos/Blayzo.png',
            'Claude': '/static/logos/Claude_Free.png', // URL-safe filename
            'Blayzica': '/static/logos/Blayzica.png',
            'Blayzia': '/static/logos/Blayzia.png',
            'Blayzion': '/static/logos/Blayzion.png', 
            'Lumen': '/static/logos/Lumen_Bronze.png',
            'Blayzo.2': '/static/logos/blayzo_free_tier.png',
            
            // BRONZE TIER (Backend IDs)
            'gamerjay_bronze': '/static/logos/GamerJay_Free_companion.png',
            'blayzo_bronze': '/static/logos/Blayzo.png',
            'blayzica_bronze': '/static/logos/Blayzica.png',
            'claude_bronze': '/static/logos/Claude_Free.png',
            'blayzia_bronze': '/static/logos/Blayzia.png',
            'blayzion_bronze': '/static/logos/Blayzion.png',
            'lumen_bronze': '/static/logos/Lumen_Bronze.png',
            'blayzo2_bronze': '/static/logos/blayzo_free_tier.png',
            
            // SILVER TIER (Display Names)
            'Sky': '/static/logos/Sky_a_premium_companion.png', // URL-safe filename
            'Sky Silver': '/static/logos/Sky_a_premium_companion.png', // URL-safe filename
            'GamerJay Silver': '/static/logos/GamerJay_premium_companion.png', // URL-safe filename
            'Blayzo': '/static/logos/Blayzo.png',
            'Blayzo Pro': '/static/logos/Blayzo_premium_companion.png', // URL-safe filename
            'Blayzo Champion': '/static/logos/Blayzo_Referral.png', // URL-safe filename
            'Blayzica': '/static/logos/Blayzica.png', // Free version
            'Blayzica Pro': '/static/logos/Blayzica_Pro.png', // Using correct Pro image
            'GamerJay Premium': '/static/logos/GamerJay_premium_companion.png', // URL-safe filename
            'Claude Growth': '/static/logos/Claude_Growth.png', // URL-safe filename
            'WatchDog': '/static/logos/WatchDog_a_Premium_companion.png', // URL-safe filename
            'Rozia': '/static/logos/Rozia_Silver.png',
            
            // SILVER TIER (Backend IDs)
            'sky_silver': '/static/logos/Sky_a_premium_companion.png',
            'gamerjay_silver': '/static/logos/GamerJay_premium_companion.png',
            'claude_silver': '/static/logos/Claude_Growth.png',
            'blayzo_silver': '/static/logos/Blayzo_premium_companion.png',
            'blayzica_silver': '/static/logos/Blayzica_Pro.png',
            'watchdog_silver': '/static/logos/WatchDog_a_Premium_companion.png',
            'rozia_silver': '/static/logos/Rozia_Silver.png',
            'lumen_silver': '/static/logos/Lumen_Silver.png',
            'gamerjay_premium': '/static/logos/GamerJay_premium_companion.png', // Backend companion ID format
            
            // GOLD TIER (Display Names)
            'Crimson': '/static/logos/Crimson.png',
            'Crimson Max': '/static/logos/Crimson_a_Max_companion.png', // URL-safe filename
            'Violet': '/static/logos/Violet.png',
            'Violet Max': '/static/logos/Violet_a_Max_companion.png', // URL-safe filename
            'WatchDog Max': '/static/logos/WatchDog_a_Max_Companion.png', // URL-safe filename
            'Royal': '/static/logos/Royal_a_Max_companion.png', // URL-safe filename
            'Ven Blayzica': '/static/logos/Ven_Blayzica_a_Max_companion.png', // URL-safe filename
            'Ven Sky': '/static/logos/Ven_Sky_a_Max_companion.png', // URL-safe filename
            'Claude Max': '/static/logos/Claude_Max.png', // URL-safe filename
            
            // GOLD TIER (Backend IDs)
            'crimson_gold': '/static/logos/Crimson_a_Max_companion.png',
            'violet_gold': '/static/logos/Violet_a_Max_companion.png',
            'claude_gold': '/static/logos/Claude_Max.png',
            'royal_gold': '/static/logos/Royal_a_Max_companion.png',
            'ven_blayzica_gold': '/static/logos/Ven_Blayzica_a_Max_companion.png',
            'ven_sky_gold': '/static/logos/Ven_Sky_a_Max_companion.png',
            'watchdog_gold': '/static/logos/WatchDog_a_Max_Companion.png',
            'violet2_gold': '/static/logos/Violet_a_Max_companion.png',
            'companion_crimson': '/static/logos/Crimson_a_Max_companion.png', // Backend ID
            'companion_violet': '/static/logos/Violet_a_Max_companion.png', // Backend ID
            'watchdog_max': '/static/logos/WatchDog_a_Max_Companion.png', // Backend ID
            'royal_max': '/static/logos/Royal_a_Max_companion.png', // Backend ID
            'ven_blayzica': '/static/logos/Ven_Blayzica_a_Max_companion.png', // Backend ID
            'ven_sky': '/static/logos/Ven_Sky_a_Max_companion.png', // Backend ID
            'claude_max': '/static/logos/Claude_Max.png', // Backend ID
            
            // REFERRAL TIER
            'Blayzia': '/static/logos/Blayzia.png',
            'Blayzion': '/static/logos/Blayzion.png',
            'Blayzike': '/static/logos/Blayzike.png',
            'Blazelian': '/static/logos/Blazelian.png',
            'Claude Referral': '/static/logos/Claude_Referral.png', // URL-safe filename
            'Blayzo Special Skin': '/static/referral/blayzo_skin.png', // Missing referral companion!
            'blayzo_skin': '/static/referral/blayzo_skin.png', // Backend ID format
            'Sapphire': '/static/logos/Sapphire.png'
        };
        
        // Try both the display name and the original character ID for lookup
        const avatarSrc = avatarMap[currentCharacter] || avatarMap[currentCharacter.toLowerCase()] || '/static/logos/IntroLogo.png';
        characterAvatar.src = avatarSrc;
        characterAvatar.alt = currentCharacter;
        console.log('🖼️ Updated character avatar to:', avatarSrc);
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
    
    // Emit message start event for ad pause system
    window.dispatchEvent(new Event('soulbridge:message:start'));
    
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
        
        // DEBUG: Log what character we're sending to API
        console.log('🐛 DEBUG: Sending character to API:', currentCharacter);
        
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
            
            // Show ad after AI response for bronze users
            await handlePostResponseAd(data);
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
        
        // Emit message complete event for ad resume system
        window.dispatchEvent(new Event('soulbridge:message:complete'));
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
        
        // Direct redirect without delay to prevent flash
        window.location.href = '/companion-selection';
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
    // Trial status is now handled by new_trial_system.js exclusively
}

function showTrialBanner(timeRemaining) {
    // Hide old banner if it exists
    const existingBanner = document.querySelector('.trial-banner');
    if (existingBanner) {
        existingBanner.remove();
    }
    
    // Don't show banner - use the new circular timer instead
    console.log('🚫 OLD: Trial banner disabled - using new circular timer system');
    
    // Initialize new timer system
    if (typeof initializeNewTrialTimer === 'function') {
        console.log('✅ Initializing new circular timer system');
        initializeNewTrialTimer();
    } else {
        console.log('⚠️ New timer system not available, loading it...');
        // Add the new timer HTML if not present
        if (!document.getElementById('trial-timer-container')) {
            const timerHTML = `
                <div id="trial-timer-container" style="display:none; position: fixed; top: 20px; right: 20px; z-index: 1500; background: rgba(0,0,0,0.9); padding: 15px; border-radius: 15px; border: 2px solid #00cc66;">
                    <svg id="trial-timer-circle" width="120" height="120">
                        <circle cx="60" cy="60" r="50" stroke="#333" stroke-width="4" fill="none"/>
                        <circle id="progress-ring" cx="60" cy="60" r="50" stroke="#00cc66" stroke-width="4" fill="none" 
                                stroke-dasharray="314.16" stroke-dashoffset="314.16" 
                                style="transform: rotate(-90deg); transform-origin: 50% 50%; transition: stroke-dashoffset 1s linear;"/>
                    </svg>
                    <div id="trial-time-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #00cc66; font-size: 14px; font-weight: bold;">
                        <div id="time-remaining">00:00</div>
                        <div style="font-size: 10px; color: #888;">TRIAL</div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', timerHTML);
            
            // Start new timer
            startNewTrialTimer();
        }
    }
}

// New circular timer system for chat page
function startNewTrialTimer() {
    const container = document.getElementById('trial-timer-container');
    const progressRing = document.getElementById('progress-ring');
    const timeText = document.getElementById('time-remaining');
    
    if (!container || !progressRing || !timeText) {
        console.log('❌ New timer elements not found');
        return;
    }
    
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    
    function updateNewTimer() {
        // Timer logic handled by new_trial_system.js
        return;
        
        if (remaining <= 0) {
            container.style.display = 'none';
            console.log('⏰ NEW: Trial expired - hiding timer');
            return;
        }
        
        // Show timer
        container.style.display = 'block';
        
        // Calculate time
        const totalMinutes = Math.floor(remaining / (1000 * 60));
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;
        
        // Update display
        timeText.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        
        // Calculate progress (assume 24 hour trial for progress bar)
        const totalTrialTime = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        const elapsed = totalTrialTime - remaining;
        const progress = Math.min(elapsed / totalTrialTime, 1);
        
        const offset = circumference - (progress * circumference);
        progressRing.style.strokeDashoffset = offset;
        
        console.log('🔄 NEW: Timer updated -', `${hours}:${minutes.toString().padStart(2, '0')}`);
    }
    
    updateNewTimer();
    const newTimerInterval = setInterval(updateNewTimer, 60000); // Update every minute
    
    console.log('✅ NEW: Circular trial timer started');
}


// Companion-tier display logic
function updateTierDisplay() {
    fetch("/api/tier-limits")
        .then(res => res.json())
        .then(data => {
            const companionId = data.companion_id || "default";
            const companionTier = data.companion_tier || "bronze";
            const limits = data.limits || {};
            const usage = data.usage || {};
            
            console.log(`🎯 COMPANION-TIER UPDATE: companion_id=${companionId}, companion_tier=${companionTier}`, limits, usage);
            
            // Update tier limit displays with companion-specific data
            updateTierLimitDisplays(limits, usage);
        })
        .catch(err => {
            console.error("Failed to update companion tier display:", err);
        });
}

function updateTierLimitDisplays(limits, usage) {
    // Update decoder limits
    const decoderLimit = document.getElementById('decoderLimit');
    if (decoderLimit && limits.decoder !== undefined) {
        const decoderUsage = usage.decoder || 0;
        const decoderMax = limits.decoder;
        decoderLimit.textContent = `${decoderUsage}/${decoderMax === 'unlimited' ? '∞' : decoderMax}`;
    }
    
    // Update fortune limits
    const fortuneLimit = document.getElementById('fortuneLimit');
    if (fortuneLimit && limits.fortune !== undefined) {
        const fortuneUsage = usage.fortune || 0;
        const fortuneMax = limits.fortune;
        fortuneLimit.textContent = `${fortuneUsage}/${fortuneMax === 'unlimited' ? '∞' : fortuneMax}`;
    }
    
    // Update horoscope limits
    const horoscopeLimit = document.getElementById('horoscopeLimit');
    if (horoscopeLimit && limits.horoscope !== undefined) {
        const horoscopeUsage = usage.horoscope || 0;
        const horoscopeMax = limits.horoscope;
        horoscopeLimit.textContent = `${horoscopeUsage}/${horoscopeMax === 'unlimited' ? '∞' : horoscopeMax}`;
    }
}

// DISABLED: Server-side template now handles tier display correctly
// document.addEventListener('DOMContentLoaded', updateTierDisplay);

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
    // DISABLED: Voice chat button visibility now controlled by HTML template based on companion tier
    // This prevents JavaScript from overriding tier-specific companion feature restrictions
    
    console.log(`🔍 Voice chat visibility now handled by template for companion tier logic`);
    
    // NOTE: Voice chat visibility is now handled in chat.html template using companion_tier logic
    // to ensure Bronze companions don't show voice chat, but Silver/Gold companions do
    // (while still respecting user's actual access permissions)
}

let isVoiceChatActive = false;
let mediaRecorder = null;
let audioChunks = [];

function toggleVoiceChat() {
    console.log('🎤 Voice chat toggle clicked', { isVoiceChatActive, currentCharacter });
    
    try {
        if (!isVoiceChatActive) {
            startVoiceChat();
        } else {
            stopVoiceChat();
        }
    } catch (error) {
        console.error('❌ Voice chat toggle error:', error);
        showNotification('Voice chat error occurred', 'error');
    }
}

async function startVoiceChat() {
    console.log('🎤 Starting voice chat...');
    
    try {
        // Check if browser supports the required APIs
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Browser does not support voice recording');
        }
        
        if (!window.MediaRecorder) {
            throw new Error('Browser does not support MediaRecorder');
        }
        
        console.log('🎤 Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('🎤 Microphone access granted');
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            console.log('🎤 Audio data available:', event.data.size);
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            console.log('🎤 Recording stopped, processing audio...');
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendVoiceMessage(audioBlob);
        };
        
        mediaRecorder.onerror = (error) => {
            console.error('🎤 MediaRecorder error:', error);
            showNotification('Recording error occurred', 'error');
        };
        
        mediaRecorder.start();
        isVoiceChatActive = true;
        
        // Update button appearance
        const voiceBtn = document.getElementById('voiceChatBtn');
        if (voiceBtn) {
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Stop';
            voiceBtn.classList.add('recording');
        }
        
        showNotification('Voice recording started...', 'info');
        console.log('🎤 Voice recording started successfully');
        
    } catch (error) {
        console.error('❌ Voice chat start error:', error);
        
        let errorMessage = 'Voice chat failed to start';
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
        } else if (error.name === 'NotFoundError') {
            errorMessage = 'No microphone found. Please connect a microphone and try again.';
        } else if (error.name === 'NotSupportedError') {
            errorMessage = 'Voice chat is not supported in this browser';
        }
        
        showNotification(errorMessage, 'error');
        isVoiceChatActive = false;
    }
}

function stopVoiceChat() {
    console.log('🎤 Stopping voice chat...');
    
    try {
        if (mediaRecorder && isVoiceChatActive) {
            console.log('🎤 Stopping media recorder...');
            mediaRecorder.stop();
            
            // Stop all audio tracks to release the microphone
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => {
                    console.log('🎤 Stopping audio track:', track.kind);
                    track.stop();
                });
            }
            
            isVoiceChatActive = false;
            
            // Update button appearance
            const voiceBtn = document.getElementById('voiceChatBtn');
            if (voiceBtn) {
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Voice';
                voiceBtn.classList.remove('recording');
            }
            
            showNotification('Processing voice message...', 'info');
            console.log('🎤 Voice recording stopped successfully');
        } else {
            console.warn('⚠️ No active voice recording to stop');
        }
    } catch (error) {
        console.error('❌ Error stopping voice chat:', error);
        showNotification('Error stopping voice recording', 'error');
        
        // Force reset state
        isVoiceChatActive = false;
        const voiceBtn = document.getElementById('voiceChatBtn');
        if (voiceBtn) {
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Voice';
            voiceBtn.classList.remove('recording');
        }
    }
}

async function sendVoiceMessage(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'voice_message.wav');
        formData.append('character', currentCharacter);
        
        const response = await fetch('/api/voice-chat/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log('🎤 Voice response received:', data);
        
        if (data.success) {
            console.log('✅ Voice processing successful');
            // Add transcribed message as user message
            if (data.transcript) {
                console.log('📝 Adding transcript:', data.transcript);
                addMessage(data.transcript, 'user');
            }
            
            // Add AI response
            if (data.response) {
                console.log('🤖 Adding AI response:', data.response);
                addMessage(data.response, 'assistant');
                
                // Play voice response if available
                if (data.audio_url) {
                    playVoiceResponse(data.audio_url);
                }
            }
        } else {
            console.log('❌ Voice processing failed:', data.error);
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
            tier: 'bronze',
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
            tier: 'bronze',
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
            tier: 'bronze',
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
            tier: 'bronze',
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
            tier: 'bronze',
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
            tier: 'bronze',
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
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15, // messages
                personality_depth: 'advanced',
                special_abilities: ['spiritual_guidance', 'meditation', 'energy_healing', 'voice_chat', 'color_presets'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false,
                color_presets: [
                    {name: 'Ocean Breeze', bg: '#0f172a', accent: '#22d3ee', text: '#e2e8f0'}, 
                    {name: 'Sunset Warmth', bg: '#1a1a2e', accent: '#ff6b6b', text: '#f8f9fa'}, 
                    {name: 'Forest Calm', bg: '#0d1b2a', accent: '#2d5016', text: '#e0e7df'}
                ] // 3 preset palettes for Growth users
            }
        },
        'Blayzo Pro': {
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['creative_coaching', 'inspiration', 'artistic_guidance', 'voice_chat', 'color_presets'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'Blayzica Pro': {
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['empathy_healing', 'emotional_support', 'relationship_guidance', 'voice_chat', 'color_presets'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'GamerJay Premium': {
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['strategic_thinking', 'advanced_coaching', 'tactical_solutions', 'voice_chat', 'color_presets'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'Claude Growth': {
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['advanced_analysis', 'strategic_planning', 'professional_guidance', 'voice_chat', 'color_presets'],
                response_length: 'medium',
                emotional_intelligence: 'advanced',
                voice_enabled: true,
                priority_processing: false
            }
        },
        'WatchDog': {
            tier: 'silver',
            features: {
                response_quality: 'enhanced',
                context_memory: 15,
                personality_depth: 'advanced',
                special_abilities: ['protection_guidance', 'security_advice', 'crisis_support', 'voice_chat', 'color_presets'],
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
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30, // messages
                personality_depth: 'masterful',
                special_abilities: ['trauma_healing', 'transformation_coaching', 'crisis_support', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Crimson Max': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['trauma_healing', 'transformation_coaching', 'crisis_support', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Violet': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['creative_mastery', 'art_therapy', 'inspiration_sessions', 'advanced_voice_ai', 'custom_personality_modes', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Violet Max': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['creative_mastery', 'art_therapy', 'inspiration_sessions', 'advanced_voice_ai', 'custom_personality_modes', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'WatchDog Max': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ultimate_protection', 'advanced_security', 'crisis_management', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Royal': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['wisdom_mastery', 'leadership_guidance', 'strategic_excellence', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Ven Blayzica': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['master_healing', 'emotional_alchemy', 'spiritual_restoration', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Ven Sky': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ascended_consciousness', 'cosmic_wisdom', 'spiritual_awakening', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
                response_length: 'comprehensive',
                emotional_intelligence: 'masterful',
                voice_enabled: true,
                priority_processing: true,
                advanced_voice_ai: true
            }
        },
        'Claude Max': {
            tier: 'gold',
            features: {
                response_quality: 'premium',
                context_memory: 30,
                personality_depth: 'masterful',
                special_abilities: ['ultimate_analysis', 'strategic_excellence', 'professional_mastery', 'advanced_voice_ai', 'priority_response', 'voice_journaling', 'ai_image_generation', 'emotional_meditations', 'relationship_profiles', 'full_color_customization'],
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
    
    // Return features for the character, default to bronze tier if not found
    return companionTiers[characterName] || companionTiers['GamerJay'];
}

// Save conversation to library function
function saveConversationToLibrary() {
    if (chatHistory.length === 0) {
        showNotification('No conversation to save', 'info');
        return;
    }
    
    const conversationTitle = generateConversationTitle();
    const currentDate = new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Create conversation data
    const conversationData = {
        title: conversationTitle,
        character: currentCharacter,
        date: currentDate,
        content: formatConversationForLibrary(),
        timestamp: Date.now()
    };
    
    try {
        // Get existing conversations
        const savedConversations = JSON.parse(localStorage.getItem('savedConversations') || '[]');
        
        // Add new conversation
        savedConversations.unshift(conversationData); // Add to beginning of array
        
        // Limit to 50 conversations to prevent storage overflow
        if (savedConversations.length > 50) {
            savedConversations.splice(50);
        }
        
        // Save back to localStorage
        localStorage.setItem('savedConversations', JSON.stringify(savedConversations));
        
        console.log('💾 Conversation saved to library:', conversationTitle);
        showNotification(`Conversation "${conversationTitle}" saved to library!`, 'success');
        
    } catch (error) {
        console.error('❌ Error saving conversation to library:', error);
        showNotification('Failed to save conversation', 'error');
    }
}

function generateConversationTitle() {
    // Try to extract a meaningful title from the first user message
    const firstUserMessage = chatHistory.find(msg => msg.sender === 'user');
    
    if (firstUserMessage) {
        const content = firstUserMessage.content.trim();
        
        // Take first 40 characters and truncate at word boundary
        if (content.length <= 40) {
            return content;
        } else {
            const truncated = content.substring(0, 40);
            const lastSpace = truncated.lastIndexOf(' ');
            return (lastSpace > 20 ? truncated.substring(0, lastSpace) : truncated) + '...';
        }
    }
    
    // Fallback to companion name + timestamp
    const now = new Date();
    return `Chat with ${currentCharacter} - ${now.toLocaleDateString()}`;
}

function formatConversationForLibrary() {
    // Convert chat history to HTML format for library display
    let formattedContent = '';
    
    chatHistory.forEach(msg => {
        if (!msg.isError) { // Don't include error messages in saved conversations
            const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
            const senderLabel = msg.sender === 'user' ? 'You' : currentCharacter;
            
            formattedContent += `
                <div class="saved-message ${msg.sender}">
                    <div class="sender-label">${senderLabel}</div>
                    <div class="message-content">${msg.content}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        }
    });
    
    return formattedContent;
}

// Ad-Gated Messaging System
async function handlePostResponseAd(responseData) {
    // Check if user is ad-free using server-injected flag
    if (window.__AD_FREE__ === true || window.__AD_FREE__ === 'true') {
        console.log('🚫 Skipping ad - user has ad-free subscription');
        return;
    }
    
    console.log('📺 Showing ad for non-ad-free user');
    disableMessageInput();
    await showAdBeforeNextMessage();
}

// Ad handling for creative writing
window.handleCreativeWritingAd = async function() {
    // Check if user is ad-free using server-injected flag
    if (window.__AD_FREE__ === true || window.__AD_FREE__ === 'true') {
        console.log('🚫 Skipping creative writing ad - user has ad-free subscription');
        return;
    }
    
    console.log('📺 Showing creative writing ad for non-ad-free user');
    await showCreativeWritingAd();
}

// Legacy functions removed - now using server-injected window.__AD_FREE__ flag
// This is more reliable and faster than API calls

function disableMessageInput() {
    const sendButton = document.querySelector('.send-button');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton) {
        sendButton.disabled = true;
        sendButton.innerHTML = '<i class="fas fa-clock"></i>';
        sendButton.title = 'Please watch the ad to continue';
    }
    
    if (messageInput) {
        messageInput.disabled = true;
        messageInput.placeholder = 'Please watch the ad to continue messaging...';
    }
}

function enableMessageInput() {
    const sendButton = document.querySelector('.send-button');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton) {
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendButton.title = 'Send message';
    }
    
    if (messageInput) {
        messageInput.disabled = false;
        messageInput.placeholder = 'Type your message here or click the microphone to speak...';
    }
}

async function showAdBeforeNextMessage() {
    return new Promise((resolve) => {
        // Create ad container
        const adContainer = document.createElement('div');
        adContainer.className = 'ad-container';
        adContainer.innerHTML = `
            <div class="ad-header">
                <span class="ad-label">Advertisement</span>
                <span class="ad-timer">Please wait <span id="adTimer">15</span> seconds...</span>
            </div>
            <div class="ad-content" id="adContent">
                <!-- AdSense ad will be inserted here -->
                <div class="ad-placeholder">
                    <div class="ad-placeholder-content">
                        <i class="fas fa-ad"></i>
                        <p>Loading advertisement...</p>
                        <p class="ad-placeholder-note">Support SoulBridge AI by viewing this ad</p>
                    </div>
                </div>
            </div>
        `;
        
        // Insert ad after the last message
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.appendChild(adContainer);
        scrollToBottom();
        
        // Start countdown timer
        let timeLeft = 15;
        const timerElement = document.getElementById('adTimer');
        
        const countdown = setInterval(() => {
            timeLeft--;
            if (timerElement) {
                timerElement.textContent = timeLeft;
            }
            
            if (timeLeft <= 0) {
                clearInterval(countdown);
                completeAdViewing(adContainer, resolve);
            }
        }, 1000);
        
        // Load actual AdSense ad (placeholder for now)
        loadAdSenseAd('adContent');
    });
}

async function showCreativeWritingAd() {
    return new Promise((resolve) => {
        // Create ad container
        const adContainer = document.createElement('div');
        adContainer.className = 'ad-container';
        adContainer.innerHTML = `
            <div class="ad-header">
                <span class="ad-label">Advertisement</span>
                <span class="ad-timer">Please wait <span id="creativeAdTimer">15</span> seconds...</span>
            </div>
            <div class="ad-content" id="creativeAdContent">
                <!-- AdSense ad will be inserted here -->
                <div class="ad-placeholder">
                    <div class="ad-placeholder-content">
                        <i class="fas fa-ad"></i>
                        <p>Loading advertisement...</p>
                        <p class="ad-placeholder-note">Support SoulBridge AI by viewing this ad</p>
                    </div>
                </div>
            </div>
            <button class="ad-skip-button" id="creativeAdSkip" disabled>Continue (15s)</button>
        `;
        
        // Insert ad in the creative writing modal
        const writingOutput = document.getElementById('writingOutput');
        if (writingOutput) {
            writingOutput.appendChild(adContainer);
            
            // Scroll to ad within modal
            adContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // Start countdown timer
        let timeLeft = 15;
        const timerElement = document.getElementById('creativeAdTimer');
        const skipButton = document.getElementById('creativeAdSkip');
        
        const countdown = setInterval(() => {
            timeLeft--;
            if (timerElement) {
                timerElement.textContent = timeLeft;
            }
            if (skipButton) {
                skipButton.textContent = `Continue (${timeLeft}s)`;
            }
            
            if (timeLeft <= 0) {
                clearInterval(countdown);
                if (skipButton) {
                    skipButton.disabled = false;
                    skipButton.textContent = 'Continue';
                    skipButton.style.background = '#22d3ee';
                }
            }
        }, 1000);
        
        // Handle skip button click
        skipButton.addEventListener('click', () => {
            if (!skipButton.disabled) {
                adContainer.remove();
                resolve();
            }
        });
        
        // Load actual AdSense ad
        loadCreativeAdSenseAd('creativeAdContent');
    });
}

function loadCreativeAdSenseAd(containerId) {
    console.log('📺 Loading real AdSense ad into creative writing:', containerId);
    
    // Create a real AdSense ad unit
    try {
        const adContainer = document.getElementById(containerId);
        if (adContainer && window.adsbygoogle) {
            adContainer.innerHTML = `
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-3869471953521437"
                     data-ad-slot="1234567890"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
            `;
            
            // Initialize AdSense
            (adsbygoogle = window.adsbygoogle || []).push({});
            console.log('📺 Creative writing AdSense ad initialized');
        }
    } catch (error) {
        console.warn('⚠️ Failed to load creative writing AdSense ad:', error);
    }
}

function loadAdSenseAd(containerId) {
    console.log('📺 Loading real AdSense ad into:', containerId);
    
    const adContent = document.getElementById(containerId);
    if (adContent) {
        // Create responsive AdSense ad unit
        adContent.innerHTML = `
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-3869471953521437"
                 data-ad-slot="auto"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
        `;
        
        // Push the ad to AdSense
        try {
            (adsbygoogle = window.adsbygoogle || []).push({});
            console.log('✅ AdSense ad loaded successfully');
        } catch (error) {
            console.error('❌ AdSense ad failed to load:', error);
            // Fallback to placeholder ad
            adContent.innerHTML = `
                <div class="demo-ad">
                    <div class="demo-ad-content">
                        <h3>🧘‍♀️ Support SoulBridge AI</h3>
                        <p>Ad loading... Please wait or upgrade to ad-free!</p>
                        <button class="demo-ad-button" onclick="window.open('/subscription', '_blank')">Go Ad-Free $5/mo</button>
                    </div>
                </div>
            `;
        }
    }
}

function completeAdViewing(adContainer, resolve) {
    // Show completion message
    const adHeader = adContainer.querySelector('.ad-header');
    if (adHeader) {
        adHeader.innerHTML = `
            <span class="ad-label">Advertisement</span>
            <span class="ad-timer ad-complete">✅ Thank you! You can continue chatting</span>
        `;
    }
    
    // Re-enable messaging after brief delay
    setTimeout(() => {
        enableMessageInput();
        
        // Remove ad after another delay
        setTimeout(() => {
            if (adContainer.parentNode) {
                adContainer.remove();
            }
        }, 2000);
        
        resolve();
    }, 1000);
}

// Export functions for testing
window.testSendMessage = sendMessage;
window.clearChat = clearChat;
window.switchCharacter = switchCharacter;
window.toggleVoiceChat = toggleVoiceChat;
window.saveConversationToLibrary = saveConversationToLibrary;