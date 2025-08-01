/**
 * COMPANION SELECTOR - CLEAN JAVASCRIPT
 * Extracted from bloated inline code for performance and maintainability
 */

// Global variables
let companions = {};
let currentUser = {
    plan: 'foundation',
    selected_companion: null
};

function addClickListeners() {
    console.log('🔧 Adding click listeners to document...');
    console.log('🔍 Document ready state:', document.readyState);
    console.log('🔍 Current URL:', window.location.href);
    
    try {
        // Test if event listeners are working at all - MULTIPLE METHODS
        console.log('🧪 Testing basic event listener functionality...');
        
        // Method 1: Standard click listener
        document.addEventListener('click', function(event) {
            console.log('🔍 BASIC CLICK TEST - ANY CLICK detected:', event.target.tagName, event.target.className);
            
            // Special logging for button clicks
            if (event.target.tagName === 'BUTTON') {
                console.log('🎯 BUTTON CLICKED - Special debug:', {
                    className: event.target.className,
                    textContent: event.target.textContent,
                    hasSelectClass: event.target.classList.contains('btn-select'),
                    isDisabled: event.target.disabled,
                    dataCompanionId: event.target.dataset.companionId,
                    parentCard: event.target.closest('.companion-card')?.dataset.companionId
                });
            }
        });
        
        // Method 2: Capture phase listener (higher priority)
        document.addEventListener('click', function(event) {
            console.log('🚨 CAPTURE PHASE CLICK:', event.target.tagName, event.target.className);
        }, true);
        
        // Method 3: Body click listener as fallback
        document.body.addEventListener('click', function(event) {
            console.log('🔥 BODY CLICK DETECTED:', event.target.tagName, event.target.className);
        });
        
        // Event delegation for dynamically generated buttons - catch ALL clicks for debugging
        document.addEventListener('click', function(event) {
            console.log('🔍 GLOBAL CLICK detected on:', {
                tagName: event.target.tagName,
                className: event.target.className,
                id: event.target.id,
                textContent: event.target.textContent.substring(0, 50),
                hasSelectClass: event.target.classList.contains('btn-select'),
                isDisabled: event.target.disabled,
                dataCompanionId: event.target.dataset.companionId
            });
            
            
            // Handle companion selection buttons
            if (event.target.classList.contains('btn-select') && !event.target.disabled) {
                console.log('✅ SELECT BUTTON CLICKED - Processing...');
                event.preventDefault();
                event.stopPropagation();
                
                const companionCard = event.target.closest('.companion-card');
                console.log('🔍 Found companion card:', companionCard);
                if (companionCard) {
                    const companionId = companionCard.dataset.companionId;
                    console.log('🔍 Companion ID from data attribute:', companionId);
                    if (companionId) {
                        console.log('🔍 Event delegation: selectCompanion clicked for:', companionId);
                        try {
                            window.selectCompanion(companionId);
                        } catch (error) {
                            console.error('❌ Error calling selectCompanion:', error);
                        }
                    }
                }
                return;
            }
            
            
            console.log('🔍 Click not handled by event delegation');
        }, true); // Use capture phase to ensure we catch everything
        
        console.log('✅ Click listeners successfully added');
        
        
        // Add a test to verify the listener is working
        setTimeout(() => {
            console.log('🧪 Testing click listener by simulating a click...');
            const testDiv = document.createElement('div');
            testDiv.textContent = 'test';
            document.body.appendChild(testDiv);
            testDiv.click();
            document.body.removeChild(testDiv);
            
            // Test actual buttons on the page
            console.log('🧪 Analyzing actual buttons on page...');
            const selectButtons = document.querySelectorAll('.btn-select');
            
            console.log('🔍 Found buttons:', {
                selectButtons: selectButtons.length
            });
            
            if (selectButtons.length > 0) {
                const firstButton = selectButtons[0];
                console.log('🔍 First select button details:', {
                    tagName: firstButton.tagName,
                    className: firstButton.className,
                    disabled: firstButton.disabled,
                    style: firstButton.style.cssText,
                    computedStyle: window.getComputedStyle(firstButton).pointerEvents,
                    parentElement: firstButton.parentElement.className,
                    dataCompanionId: firstButton.dataset.companionId,
                    boundingRect: firstButton.getBoundingClientRect()
                });
                
                console.log('🔍 Select button analysis complete');
            }
        }, 2000);
        
    } catch (error) {
        console.error('❌ Error adding click listeners:', error);
    }
}

// Add click listeners immediately when script loads
console.log('📜 Script loaded - adding click listeners immediately');
addClickListeners();

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCompanionSelector();
});

// Also try adding listeners when document is interactive or complete
if (document.readyState !== 'loading') {
    console.log('📜 Document already loaded - adding listeners again');
    addClickListeners();
}

async function initializeCompanionSelector() {
    console.log('🚀 Initializing Companion Selector...');
    
    // Load user data and companions (sync with backend)
    await loadUserDataFromBackend();
    loadCompanions();
    
    
    // Set up event listeners (again to be sure)
    setupEventListeners();
    
    // Handle switching from chat
    handleChatSwitching();
    
    console.log('✅ Companion Selector initialized');
    
    // Test if functions are accessible
    console.log('🔍 Testing function accessibility:');
    console.log('  window.selectCompanion:', typeof window.selectCompanion);
}

function handleChatSwitching() {
    const switchingFromChat = localStorage.getItem('switchingFromChat');
    if (switchingFromChat === 'true') {
        localStorage.removeItem('switchingFromChat');
        setTimeout(() => {
            showNotification('Choose your new AI companion!', 'info');
        }, 500);
    }
}

function setupEventListeners() {
    console.log('🔧 Setting up event listeners...');
    
    // Add any additional event listeners here
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Ensure DOM is ready before adding click listeners
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addClickListeners);
    } else {
        addClickListeners();
    }
}

function handleVisibilityChange() {
    console.log('👁️ Page visibility changed:', document.hidden ? 'hidden' : 'visible');
    
    // Refresh companion data when page becomes visible again
    if (!document.hidden) {
        console.log('🔄 Page visible again - refreshing companion data');
        loadUserDataFromBackend();
    }
}

async function loadUserDataFromBackend() {
    try {
        console.log('👤 Loading user data from backend...');
        const response = await fetch('/api/user/status');
        if (response.ok) {
            const userData = await response.json();
            currentUser.plan = userData.plan || 'foundation';
            currentUser.selected_companion = userData.selected_companion || null;
            
            
            console.log('✅ User data loaded from backend:', currentUser);
        } else {
            console.warn('⚠️ Failed to load user data from backend, using defaults');
            currentUser.plan = 'foundation';
        }
    } catch (error) {
        console.error('❌ Error loading user data from backend:', error);
        currentUser.plan = 'foundation';
    }
}

// Removed obsolete loadUserData() function that was overriding plan to 'foundation'
// User data is now properly loaded via fetchUserData() from /api/user/status

async function loadCompanions() {
    console.log('🤖 Loading companions...');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch('/api/companions', {
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        console.log('📊 API Response data:', data);
        
        if (data.success && data.companions) {
            companions = data.companions;
            console.log('✅ Companions loaded successfully:', companions);
            renderCompanions();
        } else {
            console.error('❌ API returned error or no companions:', data);
            console.log('🔄 Falling back to static companions');
            loadFallbackCompanions();
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('⏰ API request timed out after 5 seconds');
        } else {
            console.error('❌ Error loading companions:', error);
        }
        console.log('🔄 Using fallback companions for better experience');
        loadFallbackCompanions();
    }
}

function loadFallbackCompanions() {
    console.log('🔄 Loading fallback companion data...');
    
    // Complete fallback companion data - RESTORED FROM BACKEND API
    companions = {
        free: [
            {
                companion_id: 'blayzo_free',
                display_name: 'Blayzo',
                avatar_image: '/static/logos/Blayzo.png',
                short_bio: 'Your creative and fun AI companion',
                personality_tags: ['Creative', 'Fun'],
                special_features: ['Creative assistance', 'Fun conversations', 'Idea generation', 'Entertainment'],
                tier: 'free',
                popularity_score: 90,
                is_recommended: true,
                lock_reason: null
            },
            {
                companion_id: 'blayzica_free',
                display_name: 'Blayzica',
                avatar_image: '/static/logos/Blayzica.png',
                short_bio: 'Your empathetic and caring AI companion',
                personality_tags: ['Empathetic', 'Caring'],
                special_features: ['Emotional support', 'Active listening', 'Compassionate advice', 'Wellness guidance'],
                tier: 'free',
                popularity_score: 88,
                is_recommended: true,
                lock_reason: null
            },
            {
                companion_id: 'companion_gamerjay',
                display_name: 'GamerJay',
                avatar_image: '/static/logos/GamerJay Free companion.png',
                short_bio: 'Your friendly gaming companion',
                personality_tags: ['Gaming', 'Motivational'],
                special_features: ['Gaming tips', 'Achievement tracking', 'Motivation boosts', 'Strategy advice'],
                tier: 'free',
                popularity_score: 85,
                is_recommended: false,
                lock_reason: null
            },
            {
                companion_id: 'blayzia_free',
                display_name: 'Blayzia',
                avatar_image: '/static/logos/Blayzia.png',
                short_bio: 'Mystical wisdom and spiritual insight',
                personality_tags: ['Mystical', 'Intuitive', 'Wise'],
                special_features: ['Intuitive guidance', 'Dream interpretation', 'Spiritual awakening', 'Inner wisdom'],
                tier: 'free',
                popularity_score: 90,
                is_recommended: true,
                lock_reason: null
            },
            {
                companion_id: 'blayzion_free',
                display_name: 'Blayzion',
                avatar_image: '/static/logos/Blayzion.png',
                short_bio: 'Creative innovation and breakthrough thinking',
                personality_tags: ['Creative', 'Innovative', 'Visionary'],
                special_features: ['Creative problem solving', 'Innovation coaching', 'Breakthrough thinking', 'Artistic inspiration'],
                tier: 'free',
                popularity_score: 89,
                is_recommended: false,
                lock_reason: null
            },
            {
                companion_id: 'claude_free',
                display_name: 'Claude',
                avatar_image: '/static/logos/Claude Free.png',
                short_bio: 'Your friendly coding assistant',
                personality_tags: ['Helpful', 'Methodical', 'Patient'],
                special_features: ['Basic code help', 'Problem solving', 'Learning support', 'Step-by-step guidance'],
                tier: 'free',
                popularity_score: 85,
                is_recommended: false,
                lock_reason: null
            }
        ],
        growth: [
            {
                companion_id: 'companion_sky',
                display_name: 'Sky',
                avatar_image: '/static/logos/Sky a primum companion.png',
                short_bio: 'Premium companion with advanced features',
                personality_tags: ['Spiritual', 'Healing'],
                special_features: ['Spiritual guidance', 'Meditation sessions', 'Energy healing', 'Voice interactions'],
                tier: 'growth',
                popularity_score: 90,
                is_recommended: true
            },
            {
                companion_id: 'blayzo_growth',
                display_name: 'Blayzo Pro',
                avatar_image: '/static/logos/Blayzo.png',
                short_bio: 'Advanced Blayzo with enhanced creativity and memory',
                personality_tags: ['Creative', 'Advanced'],
                special_features: ['Enhanced creativity', 'Memory retention', 'Advanced problem solving', 'Deep conversations'],
                tier: 'growth',
                popularity_score: 92,
                is_recommended: true
            },
            {
                companion_id: 'blayzica_growth',
                display_name: 'Blayzica Pro',
                avatar_image: '/static/logos/Blayzica Pro.png',
                short_bio: 'Enhanced Blayzica with deeper emotional intelligence',
                personality_tags: ['Empathetic', 'Intelligent'],
                special_features: ['Deep emotional support', 'Advanced empathy', 'Personalized guidance', 'Crisis support'],
                tier: 'growth',
                popularity_score: 91,
                is_recommended: true
            },
            {
                companion_id: 'companion_gamerjay_premium',
                display_name: 'GamerJay Premium',
                avatar_image: '/static/logos/GamerJay Free companion.png',
                short_bio: 'Enhanced GamerJay with premium features',
                personality_tags: ['Gaming', 'Premium'],
                special_features: ['Pro gaming strategies', 'Performance analysis', 'Competitive coaching', 'Advanced metrics'],
                tier: 'growth',
                popularity_score: 88,
                is_recommended: false
            }
        ],
        max: [
            {
                companion_id: 'companion_crimson',
                display_name: 'Crimson',
                avatar_image: '/static/logos/Crimson a Max companion.png',
                short_bio: 'Elite max-tier companion',
                personality_tags: ['Healing', 'Protective', 'Wise'],
                special_features: ['Trauma healing', 'Transformation coaching', 'Crisis support', 'Advanced voice AI'],
                tier: 'max',
                popularity_score: 95,
                is_recommended: true
            },
            {
                companion_id: 'companion_violet',
                display_name: 'Violet',
                avatar_image: '/static/logos/Violet a max companion.png',
                short_bio: 'Premium max companion with exclusive features',
                personality_tags: ['Elite', 'Exclusive', 'Advanced'],
                special_features: ['Premium features', 'Exclusive access', 'Priority support', 'Advanced AI'],
                tier: 'max',
                popularity_score: 92,
                is_recommended: false
            }
        ],
        referral: [
            {
                companion_id: 'blayzo',
                display_name: 'Blayzo',
                avatar_image: '/static/logos/Blayzo Referral.png',
                short_bio: 'Exclusive referral companion',
                personality_tags: ['Exclusive', 'Referral'],
                special_features: ['Exclusive access', 'Referral rewards', 'Special bonuses', 'Premium features'],
                tier: 'referral',
                lock_reason: 'Unlock through referrals',
                popularity_score: 100,
                is_recommended: false
            }
        ]
    };
    
    console.log('✅ Fallback companions loaded');
    renderCompanions();
}

function renderCompanions() {
    console.log('🎨 Rendering companions...');
    
    renderSection('free', companions.free || []);
    renderSection('growth', companions.growth || []);
    renderSection('max', companions.max || []);
    renderSection('referral', companions.referral || []);
}

function renderSection(sectionId, companionList) {
    const container = document.getElementById(`${sectionId}-companions`);
    console.log(`🎬 Rendering ${sectionId} section with ${companionList.length} companions:`, companionList);
    
    if (!container) {
        console.error(`❌ Container not found: ${sectionId}-companions`);
        return;
    }
    
    if (companionList.length === 0) {
        console.log(`📭 No companions for ${sectionId} tier`);
        container.innerHTML = '<p style="color: rgba(255,255,255,0.7); text-align: center; padding: 40px;">No companions in this tier</p>';
        return;
    }
    
    console.log(`🔍 Access check for ${sectionId} companions with user plan: ${currentUser.plan}`);
    
    container.innerHTML = companionList.map(companion => {
        // Determine if companion should be locked based on user's plan
        let isLocked = false;
        let lockReason = '';
        
        // Simple tier access - pay to unlock
        if (companion.tier === 'growth') {
            // Growth tier requires premium plan
            if (currentUser.plan === 'foundation') {
                isLocked = true;
                lockReason = 'Upgrade to Growth Plan Required';
                console.log(`🔒 Growth companion ${companion.display_name} locked - upgrade required`);
            } else if (currentUser.plan === 'premium' || currentUser.plan === 'enterprise') {
                isLocked = false;
                console.log(`✅ Growth companion ${companion.display_name} unlocked via ${currentUser.plan} plan`);
            }
        } else if (companion.tier === 'max') {
            // Max tier requires enterprise plan
            if (currentUser.plan === 'foundation' || currentUser.plan === 'premium') {
                isLocked = true;
                lockReason = 'Upgrade to Max Plan Required';
                console.log(`🔒 Max companion ${companion.display_name} locked - max plan required`);
            } else if (currentUser.plan === 'enterprise') {
                isLocked = false;
                console.log(`✅ Max companion ${companion.display_name} unlocked via enterprise plan`);
            }
        } else if (companion.tier === 'referral') {
            isLocked = true;
            lockReason = 'Unlock through referrals';
            console.log(`🔒 Referral companion ${companion.display_name} - referral only`);
        }
        
        // Override with any existing lock reason from backend ONLY for referral tier
        if (companion.lock_reason && companion.tier === 'referral') {
            isLocked = true;
            lockReason = companion.lock_reason;
        }
        
        // Log access decision for debugging
        console.log(`🔍 Access check for ${companion.display_name}: tier=${companion.tier}, userPlan=${currentUser.plan}, locked=${isLocked}`);
        
        const isSelected = currentUser.selected_companion === companion.companion_id;
        const isReferralTier = companion.tier === 'referral';
        
        return `
            <div class="companion-card ${isLocked ? 'locked' : ''} ${isSelected ? 'selected' : ''}" 
                 data-companion-id="${companion.companion_id}">
                
                <div class="companion-avatar">
                    <img src="${companion.avatar_image}" alt="${companion.display_name}" onerror="this.src='/static/logos/IntroLogo.png'">
                    
                    <div class="companion-badges">
                        ${companion.popularity_score >= 95 ? '<span class="badge badge-popular">Most Popular</span>' : ''}
                        ${companion.is_recommended ? '<span class="badge badge-recommended">Recommended</span>' : ''}
                    </div>
                    
                    ${isLocked ? `
                        <div class="lock-overlay">
                            <i class="fas fa-${isReferralTier ? 'users' : 'lock'} lock-icon"></i>
                        </div>
                    ` : ''}
                </div>
                
                <div class="companion-info">
                    <h3 class="companion-name">${companion.display_name}</h3>
                    
                    <div class="companion-tags">
                        ${(companion.personality_tags || []).map(tag => `<span class="personality-tag">${tag}</span>`).join('')}
                    </div>
                    
                    <p class="companion-bio">${companion.short_bio || companion.description || ''}</p>
                    
                    <div class="companion-features">
                        ${(companion.special_features || []).slice(0, 4).map(feature => `
                            <div class="feature-icon" title="${feature}">
                                <i class="fas fa-${getFeatureIcon(feature)}"></i>
                            </div>
                        `).join('')}
                    </div>
                    
                    <div class="companion-actions">
                        ${!isLocked ? `
                            <button class="btn-select${isSelected ? ' selected' : ''}" 
                                    ${isSelected ? 'disabled' : ''}
                                    data-companion-id="${companion.companion_id}"
                                    onclick="window.selectCompanion('${companion.companion_id}')">
                                ${isSelected ? 'Selected' : 'Select'}
                            </button>
                        ` : `
                            <button class="btn-select" disabled style="${isReferralTier ? 'background: #FFD700; color: #333;' : 'background: #ccc; color: #666; cursor: not-allowed;'}">
                                ${isReferralTier ? '👥 View Referral Program' : `🔒 ${lockReason}`}
                            </button>
                        `}
                        
                        ${companion.voice_id ? `
                            <button class="btn-preview" onclick="event.stopPropagation(); previewVoice('${companion.companion_id}')">
                                <i class="fas fa-play"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getFeatureIcon(feature) {
    const iconMap = {
        'Goal setting': 'target',
        'Achievement tracking': 'trophy',
        'Motivation boosts': 'bolt',
        'Gaming mindset': 'gamepad',
        'Spiritual guidance': 'om',
        'Meditation sessions': 'moon',
        'Energy healing': 'hand-sparkles',
        'Voice interactions': 'microphone',
        'Trauma healing': 'heart',
        'Transformation coaching': 'butterfly',
        'Crisis support': 'shield-alt',
        'Advanced voice AI': 'robot',
        'Priority response': 'star'
    };
    
    return iconMap[feature] || 'star';
}

// Make functions globally accessible
window.selectCompanion = async function(companionId) {
    console.log('🤖 Selecting companion:', companionId);
    console.log('🔍 selectCompanion function called');
    
    try {
        console.log('🔍 Making API call to /api/companions/select');
        const response = await fetch('/api/companions/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                companion_id: companionId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Companion selected successfully');
            console.log('🔍 Response data:', data);
            
            // Update UI
            currentUser.selected_companion = companionId;
            renderCompanions();
            
            // Store selection for instant access
            const companionName = getCompanionName(companionId);
            console.log('🔍 Companion name mapped to:', companionName);
            localStorage.setItem('selectedCharacter', companionName);
            localStorage.setItem('currentScreen', 'chat');
            localStorage.setItem('companionSelectionTime', Date.now());
            
            // Show success message
            showNotification(`${companionName} companion selected! Redirecting...`, 'success');
            
            // Debug: Log the redirect URL - use proper URL parameter mapping
            const urlParam = getCompanionUrlParam(companionId);
            const redirectUrl = `/chat?companion=${urlParam}`;
            console.log('🔍 About to redirect to:', redirectUrl);
            console.log('🔍 Companion ID:', companionId, '→ URL param:', urlParam);
            
            // Immediate redirect for smooth flow
            setTimeout(() => {
                console.log('🚀 Redirecting now to:', redirectUrl);
                window.location.href = redirectUrl;
            }, 800);
            
        } else {
            console.error('❌ Companion selection failed:', data.error);
            showNotification(data.error || 'Failed to select companion', 'error');
        }
        
    } catch (error) {
        console.error('❌ Companion selection error:', error);
        showNotification('Failed to select companion', 'error');
    }
}


function getCompanionName(companionId) {
    const nameMap = {
        // Free companions
        'blayzo_free': 'Blayzo',
        'blayzica_free': 'Blayzica', 
        'companion_gamerjay': 'GamerJay',
        'blayzia_free': 'Blayzia',
        'blayzion_free': 'Blayzion',
        'claude_free': 'Claude',
        
        // Growth/Premium companions
        'companion_sky': 'Sky',
        'blayzo_growth': 'Blayzo Pro',
        'blayzica_growth': 'Blayzica Pro',
        'companion_gamerjay_premium': 'GamerJay Premium',
        
        // Max companions
        'companion_crimson': 'Crimson',
        'companion_violet': 'Violet',
        'companion_blayzo': 'Blayzo'
    };
    
    if (nameMap[companionId]) {
        return nameMap[companionId];
    }
    
    // Improved fallback logic for any unmapped IDs
    let name = companionId;
    if (name.includes('companion_')) {
        name = name.replace('companion_', '');
    }
    if (name.includes('_free') || name.includes('_growth') || name.includes('_premium')) {
        name = name.replace(/_free|_growth|_premium/g, '');
    }
    
    // Capitalize first letter
    return name.charAt(0).toUpperCase() + name.slice(1);
}

function getCompanionUrlParam(companionId) {
    // Since backend now tries both direct match and companion_ prefix,
    // we can simplify and just pass the companion ID as-is for most cases
    
    const urlParamMap = {
        // Free companions - pass as-is since backend tries direct match first
        'blayzo_free': 'blayzo_free',
        'blayzica_free': 'blayzica_free', 
        'companion_gamerjay': 'gamerjay',      // Remove companion_ prefix for cleaner URL
        'blayzia_free': 'blayzia_free',
        'blayzion_free': 'blayzion_free',
        'claude_free': 'claude_free',
        
        // Growth/Premium companions - remove companion_ prefix for cleaner URLs
        'companion_sky': 'sky',
        'blayzo_growth': 'blayzo_growth',
        'blayzica_growth': 'blayzica_growth',
        'companion_gamerjay_premium': 'gamerjay_premium',
        
        // Max companions - remove companion_ prefix for cleaner URLs
        'companion_crimson': 'crimson',
        'companion_violet': 'violet'
    };
    
    return urlParamMap[companionId] || companionId.replace('companion_', '');
}

function showUpgradeModal(companionId) {
    console.log('💰 Showing upgrade modal for:', companionId);
    // Implement upgrade modal logic
    showNotification('Upgrade required for this companion', 'info');
}

function showNotification(message, type = 'info') {
    console.log(`📢 Notification (${type}): ${message}`);
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px;
        max-width: 300px;
        word-wrap: break-word;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

