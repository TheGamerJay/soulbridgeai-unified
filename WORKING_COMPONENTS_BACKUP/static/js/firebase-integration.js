/**
 * SoulBridge AI - Firebase Chat Integration
 * Integrates Firebase with the existing chat system
 */

// Firebase Integration for SoulBridge Chat
class SoulBridgeChatSync {
    constructor() {
        this.isFirebaseReady = false;
        this.currentUserID = null;
        this.unsubscribeRealtimeSync = null;
        
        // Wait for Firebase to be ready
        this.waitForFirebase();
    }

    async waitForFirebase() {
        // Check if Firebase is loaded
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait
        
        const checkFirebase = () => {
            if (window.SoulBridgeFirebase && window.SoulBridgeFirebase.currentUser !== undefined) {
                this.isFirebaseReady = true;
                this.initializeChatSync();
                console.log("🔥 Firebase chat sync initialized");
            } else if (attempts < maxAttempts) {
                attempts++;
                setTimeout(checkFirebase, 100);
            } else {
                console.warn("⚠️ Firebase not available, using local storage only");
                this.isFirebaseReady = false;
            }
        };
        
        checkFirebase();
    }

    async initializeChatSync() {
        if (!this.isFirebaseReady) return;

        try {
            // Try to sign in anonymously if no user
            if (!window.SoulBridgeFirebase.currentUser) {
                await window.SoulBridgeFirebase.signInAnonymously();
            }

            this.currentUserID = window.SoulBridgeFirebase.currentUser?.uid;
            
            if (this.currentUserID) {
                // Load existing chat history
                await this.loadChatHistoryFromFirebase();
                
                // Setup real-time sync
                this.setupRealtimeSync();
                
                console.log("💬 Chat sync ready for user:", this.currentUserID);
            }
        } catch (error) {
            console.error("❌ Failed to initialize chat sync:", error);
        }
    }

    // Enhanced sendMessage function with Firebase sync
    async sendMessageWithSync(message, character = 'Blayzo') {
        if (!message.trim()) return;

        try {
            // Show typing indicator
            this.showTypingIndicator();

            // Send to your existing AI endpoint
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    character: character
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Display the message in chat
                this.displayUserMessage(message);
                this.displayAIMessage(result.response, character);

                // Save to Firebase if available
                if (this.isFirebaseReady && this.currentUserID) {
                    try {
                        await window.SoulBridgeFirebase.saveChatMessage(message, result.response);
                        console.log("💾 Message saved to Firebase");
                    } catch (error) {
                        console.error("❌ Failed to save to Firebase:", error);
                    }
                }

                // Also save to local storage as backup
                this.saveToLocalStorage(message, result.response, character);

            } else {
                this.displayErrorMessage(result.error || 'Failed to send message');
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.displayErrorMessage('Connection error. Please try again.');
        } finally {
            this.hideTypingIndicator();
        }
    }

    async loadChatHistoryFromFirebase() {
        if (!this.isFirebaseReady || !this.currentUserID) return;

        try {
            const chatHistory = await window.SoulBridgeFirebase.loadChatHistory(50);
            
            if (chatHistory && chatHistory.length > 0) {
                // Clear current chat display
                this.clearChatDisplay();
                
                // Display each message
                chatHistory.forEach(msg => {
                    this.displayUserMessage(msg.userMessage, msg.timestamp);
                    this.displayAIMessage(msg.aiResponse, null, msg.timestamp);
                });

                console.log(`📚 Loaded ${chatHistory.length} messages from Firebase`);
            }
        } catch (error) {
            console.error("❌ Failed to load chat history:", error);
        }
    }

    setupRealtimeSync() {
        if (!this.isFirebaseReady || !this.currentUserID) return;

        // Listen for real-time updates
        this.unsubscribeRealtimeSync = window.SoulBridgeFirebase.setupRealtimeSync();

        // Listen for data updates
        window.addEventListener('soulbridge:dataUpdate', (event) => {
            const userData = event.detail;
            if (userData.chatHistory) {
                this.handleRealtimeUpdate(userData.chatHistory);
            }
        });
    }

    handleRealtimeUpdate(newChatHistory) {
        // Compare with current chat and add any new messages
        const currentMessages = this.getCurrentDisplayedMessages();
        const newMessages = newChatHistory.slice(currentMessages.length);

        newMessages.forEach(msg => {
            this.displayUserMessage(msg.userMessage, msg.timestamp);
            this.displayAIMessage(msg.aiResponse, null, msg.timestamp);
        });

        if (newMessages.length > 0) {
            console.log(`🔄 ${newMessages.length} new messages synced`);
        }
    }

    // UI Helper Methods
    displayUserMessage(message, timestamp = null) {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message';
        
        const time = timestamp ? new Date(timestamp.toDate()).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>You</strong>
                <span class="timestamp">${time}</span>
            </div>
            <div class="message-text">${this.escapeHtml(message)}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    displayAIMessage(message, character = 'AI', timestamp = null) {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message ai-message';
        
        const time = timestamp ? new Date(timestamp.toDate()).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${character || 'AI'}</strong>
                <span class="timestamp">${time}</span>
            </div>
            <div class="message-text">${this.escapeHtml(message)}</div>
        `;
        
        chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    displayErrorMessage(error) {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="error-content">
                <div class="error-title">⚠️ Error</div>
                <div class="error-text">${this.escapeHtml(error)}</div>
            </div>
            <div class="error-actions">
                <button class="error-btn retry-btn" onclick="this.parentElement.parentElement.remove()">
                    Dismiss
                </button>
            </div>
        `;
        
        chatContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <span class="typing-text">AI is typing</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        chatContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    clearChatDisplay() {
        const chatContainer = document.getElementById('chatMessages');
        if (chatContainer) {
            chatContainer.innerHTML = '';
        }
    }

    getCurrentDisplayedMessages() {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return [];

        const userMessages = chatContainer.querySelectorAll('.user-message');
        return Array.from(userMessages);
    }

    scrollToBottom() {
        const chatContainer = document.getElementById('chatMessages');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }

    saveToLocalStorage(userMessage, aiResponse, character) {
        try {
            const chatHistory = JSON.parse(localStorage.getItem('soulbridge_chat_history') || '[]');
            
            chatHistory.push({
                messageID: 'local_' + Date.now(),
                timestamp: new Date().toISOString(),
                userMessage: userMessage,
                aiResponse: aiResponse,
                character: character
            });

            // Keep only last 100 messages locally
            if (chatHistory.length > 100) {
                chatHistory.splice(0, chatHistory.length - 100);
            }

            localStorage.setItem('soulbridge_chat_history', JSON.stringify(chatHistory));
        } catch (error) {
            console.error('Failed to save to local storage:', error);
        }
    }

    // Public methods for external use
    async clearAllChatHistory() {
        // Clear Firebase
        if (this.isFirebaseReady && this.currentUserID) {
            try {
                await window.SoulBridgeFirebase.clearChatHistory();
                console.log("🗑️ Firebase chat history cleared");
            } catch (error) {
                console.error("❌ Failed to clear Firebase chat:", error);
            }
        }

        // Clear local storage
        localStorage.removeItem('soulbridge_chat_history');

        // Clear UI
        this.clearChatDisplay();

        console.log("🗑️ All chat history cleared");
    }

    async exportChatHistory() {
        if (this.isFirebaseReady && this.currentUserID) {
            try {
                await window.SoulBridgeFirebase.exportUserData();
            } catch (error) {
                console.error("❌ Failed to export from Firebase:", error);
                // Fallback to local export
                this.exportLocalHistory();
            }
        } else {
            this.exportLocalHistory();
        }
    }

    exportLocalHistory() {
        try {
            const chatHistory = JSON.parse(localStorage.getItem('soulbridge_chat_history') || '[]');
            const exportData = {
                exportDate: new Date().toISOString(),
                chatHistory: chatHistory
            };

            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `soulbridge-chat-backup-${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            console.log("📦 Local chat history exported");
        } catch (error) {
            console.error("❌ Failed to export local history:", error);
        }
    }
}

// Initialize the chat sync system
const chatSync = new SoulBridgeChatSync();

// Make it globally available
window.SoulBridgeChatSync = chatSync;

// Override the global sendMessage function if it exists
window.sendMessage = function(message, character) {
    return chatSync.sendMessageWithSync(message, character);
};

console.log("💬 SoulBridge Chat Firebase integration loaded");