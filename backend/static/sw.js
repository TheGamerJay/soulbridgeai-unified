// Service Worker for Push Notifications and PWA functionality
const CACHE_NAME = 'soulbridge-ai-v1';
const urlsToCache = [
    '/',
    '/chat',
    '/static/css/base.css',
    '/static/css/components.css',
    '/static/css/animations.css',
    '/static/css/themes.css',
    '/static/js/app.js',
    '/static/logos/SoulBridgeAI.png'
];

// Install service worker and cache resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Service Worker: Caching files');
                return cache.addAll(urlsToCache);
            })
            .catch(err => console.log('Service Worker: Cache failed', err))
    );
});

// Activate service worker and clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Clearing old cache');
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }
        )
    );
});

// Push event - handle incoming push notifications
self.addEventListener('push', event => {
    console.log('Service Worker: Push received', event);

    let notificationData = {
        title: 'SoulBridge AI',
        body: 'You have a new message from your companion!',
        icon: '/static/logos/notification-icon.png',
        badge: '/static/logos/badge-icon.png',
        tag: 'soulbridge-notification',
        data: {
            url: '/chat'
        },
        actions: [
            {
                action: 'open_chat',
                title: '💬 Open Chat',
                icon: '/static/icons/chat-icon.png'
            },
            {
                action: 'dismiss',
                title: '✖️ Dismiss',
                icon: '/static/icons/dismiss-icon.png'
            }
        ],
        requireInteraction: false,
        silent: false,
        vibrate: [200, 100, 200, 100, 200, 100, 200],
        timestamp: Date.now()
    };

    // Parse push data if available
    if (event.data) {
        try {
            const pushData = event.data.json();
            notificationData = { ...notificationData, ...pushData };
        } catch (err) {
            console.log('Service Worker: Failed to parse push data', err);
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Notification click event
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification clicked', event);

    event.notification.close();

    const action = event.action;
    const notificationData = event.notification.data || {};
    
    if (action === 'dismiss') {
        return;
    }

    let targetUrl = '/chat';
    
    if (action === 'open_chat') {
        targetUrl = '/chat';
    } else if (action === 'view_premium') {
        targetUrl = '/subscription';
    } else if (action === 'quick_reply') {
        targetUrl = '/chat#quick-reply';
    } else if (notificationData.url) {
        targetUrl = notificationData.url;
    }

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Check if app is already open
                for (let client of clientList) {
                    if (client.url.includes(self.location.origin)) {
                        // Focus existing window and navigate
                        client.focus();
                        return client.navigate(targetUrl);
                    }
                }
                // Open new window
                return clients.openWindow(targetUrl);
            })
    );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync', event.tag);

    if (event.tag === 'background-sync-messages') {
        event.waitUntil(syncPendingMessages());
    }
});

// Sync pending messages when back online
function syncPendingMessages() {
    return new Promise((resolve, reject) => {
        // Get pending messages from IndexedDB
        const request = indexedDB.open('SoulBridgeAI', 1);
        
        request.onsuccess = event => {
            const db = event.target.result;
            const transaction = db.transaction(['pendingMessages'], 'readonly');
            const store = transaction.objectStore('pendingMessages');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                const pendingMessages = getAllRequest.result;
                
                // Send each pending message
                const promises = pendingMessages.map(message => {
                    return fetch('/api/chat/send', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(message.data)
                    }).then(response => {
                        if (response.ok) {
                            // Remove from pending messages
                            const deleteTransaction = db.transaction(['pendingMessages'], 'readwrite');
                            const deleteStore = deleteTransaction.objectStore('pendingMessages');
                            return deleteStore.delete(message.id);
                        }
                    });
                });
                
                Promise.all(promises).then(resolve).catch(reject);
            };
        };
        
        request.onerror = reject;
    });
}

// Periodic background sync for user engagement
self.addEventListener('periodicsync', event => {
    if (event.tag === 'user-engagement-check') {
        event.waitUntil(checkUserEngagement());
    }
});

function checkUserEngagement() {
    // Check if user has been inactive and send retention notifications
    return fetch('/api/notifications/check-engagement', {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            return response.json();
        }
    }).then(data => {
        if (data && data.shouldNotify) {
            return self.registration.showNotification(data.title, data.options);
        }
    }).catch(err => {
        console.log('Service Worker: Engagement check failed', err);
    });
}

// Message event for communication with main thread
self.addEventListener('message', event => {
    console.log('Service Worker: Message received', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data.type === 'REQUEST_NOTIFICATION_PERMISSION') {
        // Request notification permission
        Notification.requestPermission().then(permission => {
            event.ports[0].postMessage({ permission });
        });
    } else if (event.data.type === 'SCHEDULE_NOTIFICATION') {
        // Schedule a local notification
        const { title, body, delay } = event.data;
        setTimeout(() => {
            self.registration.showNotification(title, {
                body,
                icon: '/static/logos/notification-icon.png',
                badge: '/static/logos/badge-icon.png',
                tag: 'scheduled-notification'
            });
        }, delay);
    }
});

// Handle fetch errors gracefully
self.addEventListener('fetch', event => {
    // Only handle GET requests
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // Return offline page for navigation requests
                        if (event.request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                    });
            })
    );
});