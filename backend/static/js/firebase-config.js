/**
 * SoulBridge AI - Firebase Integration
 * Real-time data sync and cloud storage for user data and chat history
 */

// Firebase Configuration (Replace with your actual config)
const firebaseConfig = {
    apiKey: "YOUR_API_KEY_HERE",
    authDomain: "soulbridge-ai.firebaseapp.com", 
    projectId: "soulbridge-ai",
    storageBucket: "soulbridge-ai.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Initialize Firebase
let app, db, auth;
try {
    app = firebase.initializeApp(firebaseConfig);
    db = firebase.firestore();
    auth = firebase.auth();
    console.log("✅ Firebase initialized successfully");
} catch (error) {
    console.error("❌ Firebase initialization failed:", error);
}

// SoulBridge Firebase Manager
class SoulBridgeFirebase {
    constructor() {
        this.currentUser = null;
        this.isOnline = navigator.onLine;
        this.setupConnectionMonitoring();
        this.setupAuthStateListener();
    }

    // ===== AUTHENTICATION =====
    
    setupAuthStateListener() {
        auth.onAuthStateChanged((user) => {
            this.currentUser = user;
            if (user) {
                console.log("🔑 User authenticated:", user.uid);
                this.syncUserData();
            } else {
                console.log("🚪 User signed out");
            }
        });
    }

    async signInAnonymously() {
        try {
            const result = await auth.signInAnonymously();
            console.log("👤 Anonymous sign-in successful:", result.user.uid);
            return result.user;
        } catch (error) {
            console.error("❌ Anonymous sign-in failed:", error);
            throw error;
        }
    }

    async signInWithEmail(email, password) {
        try {
            const result = await auth.signInWithEmailAndPassword(email, password);
            console.log("📧 Email sign-in successful:", result.user.uid);
            return result.user;
        } catch (error) {
            console.error("❌ Email sign-in failed:", error);
            throw error;
        }
    }

    async createUserWithEmail(email, password) {
        try {
            const result = await auth.createUserWithEmailAndPassword(email, password);
            console.log("👤 User created successfully:", result.user.uid);
            
            // Initialize user data in Firestore
            await this.initializeUserData(result.user.uid, email);
            return result.user;
        } catch (error) {
            console.error("❌ User creation failed:", error);
            throw error;
        }
    }

    async signOut() {
        try {
            await auth.signOut();
            console.log("🚪 Sign-out successful");
        } catch (error) {
            console.error("❌ Sign-out failed:", error);
            throw error;
        }
    }

    // ===== USER DATA MANAGEMENT =====

    async initializeUserData(userID, email, companion = "Blayzo") {
        const userData = {
            userID: userID,
            email: email,
            subscriptionStatus: "free",
            companion: companion,
            chatHistory: [],
            settings: {
                colorPalette: this.getCompanionColor(companion),
                voiceEnabled: true,
                historySaving: true
            },
            createdDate: firebase.firestore.FieldValue.serverTimestamp(),
            lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
        };

        try {
            await db.collection("users").doc(userID).set(userData);
            console.log("✅ User data initialized in Firebase");
            return userData;
        } catch (error) {
            console.error("❌ Failed to initialize user data:", error);
            throw error;
        }
    }

    async getUserData(userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        try {
            const doc = await db.collection("users").doc(uid).get();
            if (doc.exists) {
                console.log("📄 User data retrieved from Firebase");
                return doc.data();
            } else {
                console.log("👤 No user data found, creating new user");
                return null;
            }
        } catch (error) {
            console.error("❌ Failed to get user data:", error);
            throw error;
        }
    }

    async updateUserData(updates, userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        try {
            const updateData = {
                ...updates,
                lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
            };
            
            await db.collection("users").doc(uid).update(updateData);
            console.log("✅ User data updated in Firebase");
            return true;
        } catch (error) {
            console.error("❌ Failed to update user data:", error);
            throw error;
        }
    }

    async updateSubscription(subscriptionStatus, userID = null) {
        return this.updateUserData({ subscriptionStatus }, userID);
    }

    async changeCompanion(companion, userID = null) {
        const updates = {
            companion: companion,
            'settings.colorPalette': this.getCompanionColor(companion)
        };
        return this.updateUserData(updates, userID);
    }

    // ===== CHAT HISTORY MANAGEMENT =====

    async saveChatMessage(userMessage, aiResponse, userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        const messageData = {
            messageID: this.generateMessageID(),
            timestamp: firebase.firestore.FieldValue.serverTimestamp(),
            userMessage: userMessage,
            aiResponse: aiResponse
        };

        try {
            // Add to chat history array
            await db.collection("users").doc(uid).update({
                chatHistory: firebase.firestore.FieldValue.arrayUnion(messageData),
                lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
            });

            console.log("💬 Chat message saved to Firebase");
            return messageData;
        } catch (error) {
            console.error("❌ Failed to save chat message:", error);
            throw error;
        }
    }

    async loadChatHistory(limit = 50, userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        try {
            const userData = await this.getUserData(uid);
            if (userData && userData.chatHistory) {
                // Return most recent messages (limited)
                const history = userData.chatHistory.slice(-limit);
                console.log(`📚 Loaded ${history.length} chat messages from Firebase`);
                return history;
            }
            return [];
        } catch (error) {
            console.error("❌ Failed to load chat history:", error);
            throw error;
        }
    }

    async clearChatHistory(userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        try {
            await db.collection("users").doc(uid).update({
                chatHistory: [],
                lastUpdated: firebase.firestore.FieldValue.serverTimestamp()
            });
            console.log("🗑️ Chat history cleared in Firebase");
            return true;
        } catch (error) {
            console.error("❌ Failed to clear chat history:", error);
            throw error;
        }
    }

    // ===== SETTINGS MANAGEMENT =====

    async updateSettings(settings, userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        const updates = {};
        for (const [key, value] of Object.entries(settings)) {
            updates[`settings.${key}`] = value;
        }
        updates.lastUpdated = firebase.firestore.FieldValue.serverTimestamp();

        try {
            await db.collection("users").doc(uid).update(updates);
            console.log("⚙️ Settings updated in Firebase");
            return true;
        } catch (error) {
            console.error("❌ Failed to update settings:", error);
            throw error;
        }
    }

    async getSettings(userID = null) {
        const userData = await this.getUserData(userID);
        return userData?.settings || {};
    }

    // ===== REAL-TIME SYNC =====

    setupRealtimeSync(userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) return;

        // Listen for real-time updates
        return db.collection("users").doc(uid).onSnapshot((doc) => {
            if (doc.exists) {
                console.log("🔄 Real-time data update received");
                this.onDataUpdate(doc.data());
            }
        }, (error) => {
            console.error("❌ Real-time sync error:", error);
        });
    }

    onDataUpdate(userData) {
        // Override this method to handle real-time updates
        console.log("📡 User data updated:", userData);
        
        // Trigger custom events for UI updates
        window.dispatchEvent(new CustomEvent('soulbridge:dataUpdate', {
            detail: userData
        }));
    }

    // ===== OFFLINE SUPPORT =====

    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log("🌐 Connection restored - syncing data");
            this.syncUserData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log("📴 Connection lost - offline mode");
        });
    }

    async syncUserData() {
        if (!this.isOnline || !this.currentUser) return;

        try {
            // Sync any pending local data with Firebase
            console.log("🔄 Syncing user data with Firebase");
            
            // You can implement local storage sync here
            // For example, sync any messages stored locally while offline
            
        } catch (error) {
            console.error("❌ Data sync failed:", error);
        }
    }

    // ===== UTILITY METHODS =====

    generateMessageID() {
        return 'msg' + Math.random().toString(36).substr(2, 9);
    }

    getCompanionColor(companion) {
        const colors = {
            "Blayzo": "cyan",
            "Blayzion": "galaxy", 
            "Crimson": "blood-orange",
            "Blayzica": "red",
            "Blayzia": "galaxy",
            "Violet": "violet"
        };
        return colors[companion] || "cyan";
    }

    // ===== ANALYTICS & STATS =====

    async getUserStats() {
        try {
            const snapshot = await db.collection("users").get();
            const stats = {
                totalUsers: snapshot.size,
                subscriptionCounts: { free: 0, plus: 0, galaxy: 0 },
                companionCounts: {},
                totalMessages: 0
            };

            snapshot.forEach(doc => {
                const data = doc.data();
                
                // Count subscriptions
                stats.subscriptionCounts[data.subscriptionStatus || 'free']++;
                
                // Count companions
                const companion = data.companion || 'Blayzo';
                stats.companionCounts[companion] = (stats.companionCounts[companion] || 0) + 1;
                
                // Count messages
                stats.totalMessages += (data.chatHistory || []).length;
            });

            return stats;
        } catch (error) {
            console.error("❌ Failed to get user stats:", error);
            throw error;
        }
    }

    // ===== BACKUP & EXPORT =====

    async exportUserData(userID = null) {
        const uid = userID || this.currentUser?.uid;
        if (!uid) throw new Error("No user ID provided");

        try {
            const userData = await this.getUserData(uid);
            const exportData = {
                exportDate: new Date().toISOString(),
                userData: userData
            };

            // Create downloadable JSON file
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `soulbridge-backup-${uid}-${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            console.log("📦 User data exported successfully");
            
        } catch (error) {
            console.error("❌ Failed to export user data:", error);
            throw error;
        }
    }
}

// Initialize Firebase Manager
const soulbridgeFirebase = new SoulBridgeFirebase();

// Make it globally available
window.SoulBridgeFirebase = soulbridgeFirebase;

console.log("🔥 SoulBridge Firebase integration loaded successfully");