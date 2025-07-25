// Push Notifications Manager
class NotificationManager {
    constructor() {
        this.swRegistration = null;
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.isSubscribed = false;
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.log('Push notifications not supported');
            return;
        }

        try {
            // Register service worker
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('Service Worker registered successfully');

            // Check if already subscribed
            const subscription = await this.swRegistration.pushManager.getSubscription();
            this.isSubscribed = !(subscription === null);
            
            if (this.isSubscribed) {
                console.log('User is already subscribed to push notifications');
            }

            // Add notification request UI
            this.addNotificationUI();

        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }

    addNotificationUI() {
        // Add notification permission request to chat interface
        const chatInterface = document.getElementById('chatInterface');
        if (chatInterface && !this.isSubscribed && Notification.permission === 'default') {
            this.showNotificationPrompt();
        }
    }

    showNotificationPrompt() {
        // Create notification prompt
        const prompt = document.createElement('div');
        prompt.id = 'notificationPrompt';
        prompt.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, rgba(34, 211, 238, 0.95), rgba(8, 145, 178, 0.95));
                color: #000;
                padding: 1rem;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(34, 211, 238, 0.3);
                max-width: 300px;
                z-index: 1000;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(34, 211, 238, 0.3);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">🔔</span>
                    <strong>Stay Connected!</strong>
                </div>
                <p style="margin: 0.5rem 0; font-size: 0.9rem;">
                    Get notified when your companion misses you or has something special to share!
                </p>
                <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                    <button onclick="notificationManager.requestPermission()" style="
                        background: rgba(0, 0, 0, 0.8);
                        color: #22d3ee;
                        border: 1px solid #22d3ee;
                        padding: 0.5rem 1rem;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 0.8rem;
                        font-weight: 600;
                    ">Enable</button>
                    <button onclick="notificationManager.dismissPrompt()" style="
                        background: transparent;
                        color: rgba(0, 0, 0, 0.7);
                        border: 1px solid rgba(0, 0, 0, 0.3);
                        padding: 0.5rem 1rem;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 0.8rem;
                    ">Maybe Later</button>
                </div>
            </div>
        `;

        document.body.appendChild(prompt);

        // Auto-dismiss after 30 seconds
        setTimeout(() => {
            this.dismissPrompt();
        }, 30000);
    }

    dismissPrompt() {
        const prompt = document.getElementById('notificationPrompt');
        if (prompt) {
            prompt.remove();
        }
    }

    async requestPermission() {
        try {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('Notification permission granted');
                await this.subscribeUser();
                this.dismissPrompt();
                
                // Show success message
                this.showMessage('🎉 Notifications enabled! Your companion can now reach out to you.', 'success');
            } else {
                console.log('Notification permission denied');
                this.showMessage('📱 You can enable notifications later in your browser settings.', 'info');
                this.dismissPrompt();
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            this.showMessage('❌ Failed to enable notifications. Please try again.', 'error');
        }
    }

    async subscribeUser() {
        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlB64ToUint8Array('YOUR_VAPID_PUBLIC_KEY') // You'll need to generate VAPID keys
            });

            console.log('User is subscribed:', subscription);

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            
            this.isSubscribed = true;

            // Schedule welcome notification
            setTimeout(() => {
                this.sendLocalNotification(
                    'Welcome to SoulBridge AI! 🌟',
                    'Your companion is excited to start this journey with you.'
                );
            }, 3000);

        } catch (error) {
            console.error('Failed to subscribe user:', error);
        }
    }

    async sendSubscriptionToServer(subscription) {
        try {
            const userEmail = localStorage.getItem('userEmail') || 'anonymous';
            const companion = localStorage.getItem('selectedCharacter') || 'Blayzo';

            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    subscription: subscription,
                    userEmail: userEmail,
                    companion: companion
                })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('Subscription sent to server successfully');
            } else {
                console.error('Failed to send subscription to server:', data.error);
            }
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }

    sendLocalNotification(title, body, options = {}) {
        if (!this.swRegistration) return;

        const notificationOptions = {
            body: body,
            icon: '/static/logos/notification-icon.png',
            badge: '/static/logos/badge-icon.png',
            tag: 'soulbridge-local',
            requireInteraction: false,
            ...options
        };

        this.swRegistration.showNotification(title, notificationOptions);
    }

    async scheduleRetentionNotifications() {
        try {
            const userEmail = localStorage.getItem('userEmail') || 'anonymous';
            const companion = localStorage.getItem('selectedCharacter') || 'Blayzo';

            // Schedule daily check-in notification (if user doesn't return)
            await fetch('/api/notifications/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userEmail: userEmail,
                    type: 'daily_checkin',
                    delayMinutes: 1440, // 24 hours
                    userData: {
                        selectedCharacter: companion
                    }
                })
            });

            // Schedule companion missing notification (if user doesn't return)
            await fetch('/api/notifications/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userEmail: userEmail,
                    type: 'companion_missing',
                    delayMinutes: 4320, // 3 days
                    userData: {
                        selectedCharacter: companion
                    }
                })
            });

            console.log('Retention notifications scheduled');
        } catch (error) {
            console.error('Error scheduling retention notifications:', error);
        }
    }

    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 1rem;
            border-radius: 8px;
            max-width: 300px;
            z-index: 1001;
            font-size: 0.9rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            ${type === 'success' ? 'background: rgba(34, 197, 94, 0.9); color: white;' : ''}
            ${type === 'error' ? 'background: rgba(239, 68, 68, 0.9); color: white;' : ''}
            ${type === 'info' ? 'background: rgba(34, 211, 238, 0.9); color: #000;' : ''}
        `;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }

    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    // Called when user starts chatting
    onUserEngaged() {
        // Cancel any pending retention notifications
        // In a real implementation, you'd call an API to cancel scheduled notifications
        console.log('User engaged - retention notifications may be cancelled');
    }

    // Called when user becomes inactive
    onUserInactive() {
        // Schedule retention notifications
        if (this.isSubscribed) {
            this.scheduleRetentionNotifications();
        }
    }

    async testNotification() {
        if (!this.isSubscribed) {
            this.showMessage('Please enable notifications first', 'info');
            return;
        }

        try {
            const userEmail = localStorage.getItem('userEmail') || 'anonymous';
            const companion = localStorage.getItem('selectedCharacter') || 'Blayzo';

            const response = await fetch('/api/notifications/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userEmail: userEmail,
                    type: 'companion_missing',
                    userData: {
                        selectedCharacter: companion
                    }
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showMessage('🔔 Test notification sent!', 'success');
            } else {
                this.showMessage('❌ Failed to send test notification', 'error');
            }
        } catch (error) {
            console.error('Error sending test notification:', error);
            this.showMessage('❌ Error sending test notification', 'error');
        }
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

// Track user activity for retention notifications
let userActivityTimer;
let isUserActive = true;

function resetActivityTimer() {
    clearTimeout(userActivityTimer);
    isUserActive = true;
    
    // Set user as inactive after 30 minutes of no activity
    userActivityTimer = setTimeout(() => {
        isUserActive = false;
        notificationManager.onUserInactive();
    }, 30 * 60 * 1000); // 30 minutes
}

// Listen for user activity
['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'].forEach(event => {
    document.addEventListener(event, resetActivityTimer, true);
});

// Initialize activity timer
resetActivityTimer();

// Expose for testing
window.notificationManager = notificationManager;