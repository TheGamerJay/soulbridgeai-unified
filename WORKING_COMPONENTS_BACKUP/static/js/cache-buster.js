// Cache buster utility for fixing 502 deployment issues
class CacheBuster {
    constructor() {
        this.cacheVersion = Date.now();
    }
    
    // Force unregister all service workers
    async unregisterServiceWorkers() {
        if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            console.log(`Found ${registrations.length} service worker registrations`);
            
            for (let registration of registrations) {
                console.log('Unregistering service worker:', registration.scope);
                await registration.unregister();
            }
            
            console.log('All service workers unregistered');
        }
    }
    
    // Clear all caches
    async clearAllCaches() {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            console.log(`Found ${cacheNames.length} caches to clear`);
            
            for (let cacheName of cacheNames) {
                console.log('Deleting cache:', cacheName);
                await caches.delete(cacheName);
            }
            
            console.log('All caches cleared');
        }
    }
    
    // Force refresh critical resources
    async refreshCriticalResources() {
        const criticalResources = [
            '/static/css/animations.css',
            '/static/css/themes.css', 
            '/static/css/components.css',
            '/static/js/mini-assistant-modal.js',
            '/static/logos/New IntroLogo.png'
        ];
        
        console.log('Refreshing critical resources...');
        
        for (let resource of criticalResources) {
            try {
                const response = await fetch(resource + `?v=${this.cacheVersion}`, {
                    cache: 'reload',
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                });
                console.log(`Refreshed ${resource}: ${response.status}`);
            } catch (error) {
                console.warn(`Failed to refresh ${resource}:`, error);
            }
        }
    }
    
    // Complete cache bust and reload
    async performFullCacheBust() {
        console.log('🔄 Starting full cache bust...');
        
        try {
            await this.unregisterServiceWorkers();
            await this.clearAllCaches();
            await this.refreshCriticalResources();
            
            // Clear browser storage
            if (localStorage) {
                localStorage.clear();
                console.log('LocalStorage cleared');
            }
            
            if (sessionStorage) {
                sessionStorage.clear();
                console.log('SessionStorage cleared');
            }
            
            console.log('✅ Cache bust complete - reloading page...');
            
            // Force a hard reload
            window.location.reload(true);
            
        } catch (error) {
            console.error('❌ Cache bust failed:', error);
        }
    }
}

// Auto-run cache buster if URL has ?cachebust parameter
if (window.location.search.includes('cachebust=true')) {
    const buster = new CacheBuster();
    buster.performFullCacheBust();
}

// Expose globally for manual use
window.CacheBuster = CacheBuster;

// Add cache buster button to page
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/login' || window.location.search.includes('debug=true')) {
        const button = document.createElement('button');
        button.innerHTML = '🔄 Clear Cache & Reload';
        button.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;background:#ff4444;color:white;border:none;padding:10px;border-radius:5px;cursor:pointer;font-size:12px;';
        button.onclick = () => {
            const buster = new CacheBuster();
            buster.performFullCacheBust();
        };
        document.body.appendChild(button);
    }
});