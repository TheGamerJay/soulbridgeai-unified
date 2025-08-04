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
        
        // Event delegation for all button clicks
        document.body.addEventListener('click', function(event) {
            console.log('🔍 BODY CLICK on:', event.target.tagName, event.target.className);
            
            // Handle all btn-select buttons
            if (event.target.classList.contains('btn-select')) {
                const companionId = event.target.dataset.companionId || event.target.getAttribute('data-companion-id');
                console.log('🔘 Button clicked for companion:', companionId);
                
                // Check if this is an upgrade/trial button with onclick handler
                if (event.target.classList.contains('btn-upgrade') && event.target.onclick) {
                    console.log('💎 UPGRADE/TRIAL BUTTON - Allowing onclick handler to execute');
                    // Don't call preventDefault() - let the onclick handler work
                    return;
                }
                
                // Handle regular select buttons (not upgrade buttons)
                if (companionId && !event.target.disabled && !event.target.classList.contains('btn-upgrade')) {
                    console.log('✅ SELECT BUTTON - Processing companion selection');
                    event.preventDefault();
                    window.selectCompanion(companionId);
                }
            }
        });
        
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
    
    // Check trial status on page load
    await checkTrialStatus();
    
    loadCompanions();
    
    // Set up event listeners (again to be sure)
    setupEventListeners();
    
    // Handle switching from chat
    handleChatSwitching();
    
    console.log('✅ Companion Selector initialized');
    
    // Test if functions are accessible
    console.log('🔍 Testing function accessibility:');
    console.log('  window.selectCompanion:', typeof window.selectCompanion);
    console.log('  checkTrialStatus:', typeof checkTrialStatus);
    console.log('  startPremiumTrial:', typeof startPremiumTrial);
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
        const res = await fetch('/api/companions');
        const data = await res.json();
        console.log('📊 API Response data:', data);

        const companions = data.companions || [];
        const trialActive = data.trial_active === true;
        const effectivePlan = data.effective_plan || 'foundation';

        // Store global state
        window.companionsData = companions;
        window.trialStatus = { 
            trial_active: trialActive,
            effective_plan: effectivePlan
        };

        // Hide trial button if active
        const trialBtn = document.getElementById('trial-button');
        if (trialActive && trialBtn) {
            trialBtn.style.display = 'none';
        }

        // Render companions using API response data
        renderCompanionsFromAPI(companions, trialActive);

    } catch (error) {
        console.error('❌ Failed to load companions:', error);
        // Fallback to static companions
        loadFallbackCompanions();
    }
}

function renderCompanionsFromAPI(companionsData, trialActive) {
    console.log('🎬 Rendering companions from API:', { companionsData, trialActive });
    
    // Store companion data globally for easy access
    window.companionDataStore = {};
    
    // Clear existing content
    const sections = ['free', 'growth', 'max', 'referral'];
    sections.forEach(tier => {
        const container = document.getElementById(`${tier}-companions`);
        if (container) {
            container.innerHTML = '';
        }
    });
    
    // Render each tier
    Object.keys(companionsData).forEach(tier => {
        const companions = companionsData[tier] || [];
        const container = document.getElementById(`${tier}-companions`);
        
        if (!container) {
            console.warn(`❌ Container not found for tier: ${tier}`);
            return;
        }
        
        companions.forEach(companion => {
            // Store companion data with tier info
            const companionWithTier = { ...companion, tier: tier };
            window.companionDataStore[companion.companion_id] = companionWithTier;
            
            const isLocked = companion.lock_reason !== null;
            const companionCard = createCompanionCard(companionWithTier, isLocked);
            container.appendChild(companionCard);
        });
    });
}

function createCompanionCard(companion, isLocked) {
    const card = document.createElement('div');
    card.className = 'companion-card';
    card.id = `companion-${companion.companion_id}`;
    
    const buttonClass = isLocked ? 'btn-select btn-upgrade' : 'btn-select';
    const buttonText = isLocked ? companion.lock_reason : 'Select';
    const buttonOnClick = isLocked ? `showTrialModalByID('${companion.companion_id}')` : '';
    
    card.innerHTML = `
        <div class="companion-avatar">
            <img src="${companion.avatar_image}" alt="${companion.display_name}" loading="lazy">
        </div>
        <div class="companion-info">
            <h3>${companion.display_name}</h3>
            <p>${companion.description}</p>
            <div class="companion-tier tier-${companion.tier}">${companion.tier.toUpperCase()}</div>
        </div>
        <div class="companion-actions">
            <button class="${buttonClass}" 
                    data-companion-id="${companion.companion_id}"
                    ${isLocked ? `onclick="${buttonOnClick}"` : `onclick="window.selectCompanion('${companion.companion_id}')"`}>
                ${buttonText}
            </button>
        </div>
    `;
    
    return card;
}

// Helper function to show trial modal using companion ID
function showTrialModalByID(companionId) {
    const companion = window.companionDataStore && window.companionDataStore[companionId];
    if (companion) {
        console.log('🎯 Found companion data:', companion);
        showTrialModal(companionId, companion.tier, companion.display_name);
    } else {
        console.error('❌ Companion not found in data store:', companionId);
        showTrialModal(companionId, 'unknown', 'Unknown Companion');
    }
}

// Expose the function globally
window.showTrialModalByID = showTrialModalByID;

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
            },
            {
                companion_id: 'watchdog_growth',
                display_name: 'WatchDog',
                avatar_image: '/static/logos/WatchDog a Primum companion.png',
                short_bio: 'Your protective guardian companion',
                personality_tags: ['Protective', 'Guardian'],
                special_features: ['Protection guidance', 'Security advice', 'Safety coaching', 'Risk assessment'],
                tier: 'growth',
                popularity_score: 78,
                is_recommended: false
            },
            {
                companion_id: 'crimson_growth',
                display_name: 'Crimson',
                avatar_image: '/static/logos/Crimson.png',
                short_bio: 'Motivational drive to overcome challenges',
                personality_tags: ['Motivational', 'Strong'],
                special_features: ['Challenge coaching', 'Motivation boosts', 'Strength building', 'Resilience training'],
                tier: 'growth',
                popularity_score: 87,
                is_recommended: true
            },
            {
                companion_id: 'violet_growth',
                display_name: 'Violet',
                avatar_image: '/static/logos/Violet.png',
                short_bio: 'Creative inspiration and artistic guidance',
                personality_tags: ['Creative', 'Artistic'],
                special_features: ['Creative guidance', 'Artistic inspiration', 'Design thinking', 'Innovation coaching'],
                tier: 'growth',
                popularity_score: 84,
                is_recommended: false
            },
            {
                companion_id: 'claude_growth',
                display_name: 'Claude Growth',
                avatar_image: '/static/logos/Claude Growth.png',
                short_bio: 'Advanced coding guidance and architecture',
                personality_tags: ['Technical', 'Advanced', 'Methodical'],
                special_features: ['Advanced coding', 'System architecture', 'Code optimization', 'Technical mentoring'],
                tier: 'growth',
                popularity_score: 93,
                is_recommended: true
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
            },
            {
                companion_id: 'royal_max',
                display_name: 'Royal',
                avatar_image: '/static/logos/Royal a max companion.png',
                short_bio: 'Majestic guide with sophisticated wisdom',
                personality_tags: ['Majestic', 'Wise', 'Sophisticated'],
                special_features: ['Royal guidance', 'Sophisticated advice', 'Leadership coaching', 'Elite wisdom'],
                tier: 'max',
                popularity_score: 95,
                is_recommended: false
            },
            {
                companion_id: 'watchdog_max',
                display_name: 'WatchDog Max',
                avatar_image: '/static/logos/WatchDog a Max Companion.png',
                short_bio: 'Ultimate guardian companion',
                personality_tags: ['Ultimate', 'Guardian', 'Elite'],
                special_features: ['Ultimate protection', 'Elite security', 'Advanced monitoring', 'Crisis management'],
                tier: 'max',
                popularity_score: 93,
                is_recommended: false
            },
            {
                companion_id: 'ven_blayzica',
                display_name: 'Ven Blayzica',
                avatar_image: '/static/logos/Ven Blayzica a max companion.png',
                short_bio: 'Enhanced healer with emotional mastery',
                personality_tags: ['Healer', 'Emotional', 'Master'],
                special_features: ['Emotional mastery', 'Healing guidance', 'Advanced empathy', 'Therapeutic support'],
                tier: 'max',
                popularity_score: 94,
                is_recommended: true
            },
            {
                companion_id: 'ven_sky',
                display_name: 'Ven Sky',
                avatar_image: '/static/logos/Ven Sky a max companion.png',
                short_bio: 'Ascended spiritual guide',
                personality_tags: ['Ascended', 'Spiritual', 'Guide'],
                special_features: ['Ascended wisdom', 'Spiritual mastery', 'Transcendent guidance', 'Higher consciousness'],
                tier: 'max',
                popularity_score: 96,
                is_recommended: true
            },
            {
                companion_id: 'claude_max',
                display_name: 'Claude Max',
                avatar_image: '/static/logos/Claude Max.png',
                short_bio: 'Elite coding mastery and system design',
                personality_tags: ['Elite', 'Master', 'Technical'],
                special_features: ['Elite coding mastery', 'System design', 'Architecture expertise', 'Advanced optimization'],
                tier: 'max',
                popularity_score: 97,
                is_recommended: true
            }
        ],
        referral: [
            {
                companion_id: 'blayzo',
                display_name: 'Blayzo Champion',
                avatar_image: '/static/logos/Blayzo Referral.png',
                short_bio: 'Exclusive community champion',
                personality_tags: ['Exclusive', 'Champion'],
                special_features: ['Exclusive access', 'Champion rewards', 'Community leadership', 'Premium features'],
                tier: 'referral',
                lock_reason: 'Unlock through referrals',
                popularity_score: 100,
                is_recommended: true
            },
            {
                companion_id: 'blayzike',
                display_name: 'Blayzike',
                avatar_image: '/static/logos/Blayzike.png',
                short_bio: 'Mysterious guide with hidden wisdom',
                personality_tags: ['Mysterious', 'Wise', 'Hidden'],
                special_features: ['Hidden wisdom', 'Mysterious guidance', 'Secret knowledge', 'Exclusive insights'],
                tier: 'referral',
                lock_reason: 'Unlock through referrals',
                popularity_score: 97,
                is_recommended: true
            },
            {
                companion_id: 'blazelian',
                display_name: 'Blazelian',
                avatar_image: '/static/logos/Blazelian.png',
                short_bio: 'Celestial wanderer with cosmic wisdom',
                personality_tags: ['Celestial', 'Cosmic', 'Wanderer'],
                special_features: ['Cosmic wisdom', 'Celestial guidance', 'Universal insights', 'Transcendent knowledge'],
                tier: 'referral',
                lock_reason: 'Unlock through referrals',
                popularity_score: 98,
                is_recommended: true
            },
            {
                companion_id: 'claude_referral',
                display_name: 'Claude Referral',
                avatar_image: '/static/logos/Claude Referral.png',
                short_bio: 'Elite coding companion for champions',
                personality_tags: ['Elite', 'Champion', 'Technical'],
                special_features: ['Elite coding mastery', 'Champion-level support', 'Exclusive techniques', 'Advanced mentoring'],
                tier: 'referral',
                lock_reason: 'Unlock through referrals',
                popularity_score: 100,
                is_recommended: true
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
    console.log(`🔍 Current user object:`, currentUser);
    
    container.innerHTML = companionList.map(companion => {
        // Use new access control function that considers trial status
        const hasAccess = hasAccessToCompanion(companion, currentUser, window.trialStatus);
        let isLocked = !hasAccess;
        
        let lockReason = '';
        if (isLocked) {
            if (companion.tier === 'growth') {
                lockReason = 'Upgrade to Growth Plan Required';
                console.log(`🔒 Growth companion ${companion.display_name} locked - upgrade required`);
            } else if (companion.tier === 'max') {
                lockReason = 'Upgrade to Max Plan Required';
                console.log(`🔒 Max companion ${companion.display_name} locked - max plan required`);
            } else if (companion.tier === 'referral') {
                lockReason = 'Unlock through referrals';
                console.log(`🔒 Referral companion ${companion.display_name} - referral only`);
            }
        } else {
            if (window.trialStatus?.trial_active && (companion.tier === 'growth' || companion.tier === 'max')) {
                console.log(`✅ ${companion.tier} companion ${companion.display_name} unlocked via ACTIVE TRIAL`);
            } else {
                console.log(`✅ Companion ${companion.display_name} unlocked via ${currentUser.plan} plan`);
            }
        }
        
        // Override with any existing lock reason from backend ONLY for referral tier
        if (companion.lock_reason && companion.tier === 'referral') {
            isLocked = true;
            lockReason = companion.lock_reason;
        }
        
        // Log access decision for debugging
        console.log(`🔍 Access check for ${companion.display_name}: tier=${companion.tier}, userPlan=${currentUser.plan}, locked=${isLocked}, lockReason=${lockReason}`);
        
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
                        ${(() => {
                            if (!isLocked) {
                                console.log(`🔘 Rendering SELECT button for ${companion.display_name} (unlocked)`);
                                return `
                                    <button class="btn-select${isSelected ? ' selected' : ''}" 
                                            ${isSelected ? 'disabled' : ''}
                                            data-companion-id="${companion.companion_id}"
                                            onclick="window.selectCompanion('${companion.companion_id}')">
                                        ${isSelected ? 'Selected' : 'Select'}
                                    </button>
                                `;
                            } else if (companion.tier === 'growth' || companion.tier === 'max') {
                                console.log(`🔘 Rendering TRIAL/UPGRADE buttons for ${companion.display_name} (${companion.tier} tier)`);
                                const canTrial = !window.trialStatus || !window.trialStatus.trial_used_permanently;
                                
                                // Check if this specific companion has an active trial
                                const hasActiveTrial = window.trialStatus?.trial_active === true;
                                
                                if (!isLocked) {
                                    // Companion is unlocked (via plan or trial) - show select button
                                    return `
                                        <button class="btn-select" 
                                                data-companion-id="${companion.companion_id}"
                                                onclick="window.selectCompanion('${companion.companion_id}')"
                                                style="background: linear-gradient(45deg, #22d3ee, #0891b2); color: white; border: none; font-weight: bold;">
                                            ${hasActiveTrial ? '🎯 Active Trial - Select' : 'Select'}
                                        </button>
                                    `;
                                } else if (canTrial) {
                                    // Show trial option first
                                    return `
                                        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                            <button class="btn-select btn-upgrade" 
                                                    data-companion-id="${companion.companion_id}"
                                                    onclick="showTrialModal('${companion.companion_id}', '${companion.tier}', '${companion.display_name}')"
                                                    style="background: linear-gradient(45deg, #22d3ee, #0891b2); color: white; border: none; font-weight: bold; flex: 1; min-width: 120px;">
                                                🎯 Try 5hr Free
                                            </button>
                                            <button class="btn-select btn-upgrade" 
                                                    data-companion-id="${companion.companion_id}"
                                                    onclick="showUpgradeModal('${companion.companion_id}', '${companion.tier}', '${companion.display_name}')"
                                                    style="background: linear-gradient(45deg, #4CAF50, #45a049); color: white; border: none; font-weight: bold; flex: 1; min-width: 120px;">
                                                💎 Upgrade Plan
                                            </button>
                                        </div>
                                    `;
                                } else {
                                    // Trial already used, show only upgrade
                                    return `
                                        <button class="btn-select btn-upgrade" 
                                                data-companion-id="${companion.companion_id}"
                                                onclick="showUpgradeModal('${companion.companion_id}', '${companion.tier}', '${companion.display_name}')"
                                                style="background: linear-gradient(45deg, #4CAF50, #45a049); color: white; border: none; font-weight: bold;">
                                            💎 Upgrade to ${companion.tier === 'growth' ? 'Growth' : 'Max'} Plan
                                        </button>
                                    `;
                                }
                            } else {
                                console.log(`🔘 Rendering LOCKED button for ${companion.display_name} (${companion.tier} tier)`);
                                return `
                                    <button class="btn-select" disabled style="${isReferralTier ? 'background: #FFD700; color: #333;' : 'background: #ccc; color: #666; cursor: not-allowed;'}">
                                        ${isReferralTier ? '👥 View Referral Program' : `🔒 ${lockReason}`}
                                    </button>
                                `;
                            }
                        })()}
                        
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

// ========================================
// ACCESS CONTROL FUNCTIONS
// ========================================

function hasAccessToCompanion(companion, user, trialStatus) {
    const tier = companion.tier; // free, growth, max, referral
    const userPlan = user.plan;

    console.log(`🔍 Access check for ${companion.display_name}: tier=${tier}, userPlan=${userPlan}, trialActive=${trialStatus?.trial_active}`);

    if (tier === 'free') return true;

    if (tier === 'growth') {
        const hasAccess = userPlan === 'growth' || userPlan === 'premium' || userPlan === 'enterprise' || 
               (trialStatus?.trial_active === true);
        console.log(`🔍 Growth access for ${companion.display_name}: ${hasAccess}`);
        return hasAccess;
    }

    if (tier === 'max') {
        const hasAccess = userPlan === 'max' || userPlan === 'enterprise' || 
               (trialStatus?.trial_active === true);
        console.log(`🔍 Max access for ${companion.display_name}: ${hasAccess} (trial_active=${trialStatus?.trial_active})`);
        return hasAccess;
    }

    if (tier === 'referral') {
        return user.unlocked_referrals?.includes(companion.companion_id);
    }

    return false;
}

// ========================================
// TRIAL SYSTEM FUNCTIONS
// ========================================

async function startPremiumTrial(companionId) {
    console.log('🎯 Starting premium trial for:', companionId);
    
    try {
        const response = await fetch('/start-trial', {
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
            console.log('✅ Trial started successfully:', data);
            
            // Close any open modals
            closeTrialModal();
            
            // Show success message
            showNotification(data.message || '🎉 5-hour trial started!', 'success');
            
            // Update trial status and refresh UI
            await checkTrialStatus();
            renderCompanions();
            
            // Redirect to the trial companion after a short delay
            setTimeout(() => {
                const urlParam = getCompanionUrlParam(companionId);
                window.location.href = `/chat?companion=${urlParam}`;
            }, 1500);
            
        } else {
            console.error('❌ Trial start failed:', data.error);
            showNotification(data.error || 'Failed to start trial', 'error');
        }
        
    } catch (error) {
        console.error('❌ Trial start error:', error);
        showNotification('Failed to start trial. Please try again.', 'error');
    }
}

async function checkTrialStatus() {
    console.log('🔍 Checking trial status...');
    
    try {
        const response = await fetch('/get-trial-status');
        const data = await response.json();
        
        console.log('📊 Trial status:', data);
        
        if (data.trial_active) {
            // Store trial info globally for UI updates
            window.trialStatus = {
                trial_active: true,
                trial_companion: data.trial_companion,
                time_remaining: data.time_remaining,
                trial_used_permanently: data.trial_used_permanently
            };
            
            console.log(`✅ Trial is active for ${data.trial_companion}, ${data.time_remaining} minutes remaining`);
            
            // Show trial timer if we have time remaining
            if (data.time_remaining > 0) {
                showTrialTimer(data.trial_companion, data.time_remaining);
            }
            
        } else {
            window.trialStatus = {
                trial_active: false,
                trial_used_permanently: data.trial_used_permanently || false
            };
            
            console.log('ℹ️ No active trial');
            
            // Hide trial timer if no active trial
            hideTrialTimer();
        }
        
        return data;
        
    } catch (error) {
        console.error('❌ Trial status check error:', error);
        window.trialStatus = { trial_active: false };
        return { trial_active: false };
    }
}

function showTrialTimer(companionName, minutesRemaining) {
    // Remove existing trial timer
    const existingTimer = document.getElementById('trialTimer');
    if (existingTimer && existingTimer.style.display === 'block') {
        // Timer already visible, just update the time
        updateTrialTimerDisplay(minutesRemaining);
        return;
    }
    
    // Use the existing timer element from the HTML template
    const timerElement = document.getElementById('trialTimer');
    if (timerElement) {
        timerElement.style.display = 'block';
        updateTrialTimerDisplay(minutesRemaining);
        
        console.log(`⏰ Trial timer displayed: ${minutesRemaining} minutes remaining`);
    } else {
        console.warn('⚠️ Trial timer element not found in HTML');
    }
}

function hideTrialTimer() {
    const timerElement = document.getElementById('trialTimer');
    if (timerElement) {
        timerElement.style.display = 'none';
        console.log('⏰ Trial timer hidden');
    }
}

function updateTrialTimerDisplay(minutesRemaining) {
    const timeDisplay = document.getElementById('trialTimeDisplay');
    if (timeDisplay) {
        const hours = Math.floor(minutesRemaining / 60);
        const minutes = minutesRemaining % 60;
        const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
        timeDisplay.textContent = formattedTime;
    }
}

async function refreshTrialUI() {
    console.log('🔄 Refreshing trial UI lock states...');
    
    try {
        const trialStatus = window.trialStatus || { active: false };
        const trialActive = trialStatus.active;
        const trialCompanion = trialStatus.companion;
        
        console.log('🔍 Current trial status for UI refresh:', trialStatus);
        
        // Update all companion cards based on trial status
        document.querySelectorAll('.companion-card').forEach(card => {
            const companionId = card.dataset.companionId;
            const tier = card.querySelector('.tier-badge')?.textContent?.toLowerCase() || 'free';
            
            // Only affect growth and max tier companions
            if (tier === 'growth' || tier === 'max') {
                const lockIcon = card.querySelector('.lock-icon');
                const buttons = card.querySelectorAll('.btn-select');
                
                if (trialActive && trialCompanion === companionId) {
                    // This companion has active trial - unlock it
                    if (lockIcon) lockIcon.style.display = 'none';
                    card.classList.remove('locked');
                    
                    // Update buttons to show "Active Trial - Select"
                    buttons.forEach(btn => {
                        if (btn.classList.contains('btn-upgrade')) {
                            btn.outerHTML = `
                                <button class="btn-select" 
                                        data-companion-id="${companionId}"
                                        onclick="window.selectCompanion('${companionId}')"
                                        style="background: linear-gradient(45deg, #22d3ee, #0891b2); color: white; border: none; font-weight: bold;">
                                    🎯 Active Trial - Select
                                </button>
                            `;
                        }
                    });
                    
                    console.log(`✅ Unlocked companion ${companionId} for active trial`);
                } else if (trialActive) {
                    // Trial is active but for different companion - still locked
                    if (lockIcon) lockIcon.style.display = 'block';
                    card.classList.add('locked');
                } else {
                    // No active trial - locked
                    if (lockIcon) lockIcon.style.display = 'block';
                    card.classList.add('locked');
                }
            }
        });
        
        console.log('✅ Trial UI refresh completed');
        
    } catch (error) {
        console.error('❌ Error refreshing trial UI:', error);
    }
}

function showTrialModal(companionId, tier, companionName) {
    console.log('🎯 Showing trial modal for:', companionId, 'tier:', tier, 'name:', companionName);
    
    // Check if trial was already used
    if (window.trialStatus && window.trialStatus.usedPermanently) {
        showUpgradeModal(companionId, tier, companionName);
        return;
    }
    
    // Define tier information
    const tierInfo = {
        growth: {
            name: 'Growth Plan',
            price: '$12.99/month',
            color: '#4CAF50'
        },
        max: {
            name: 'Max Plan', 
            price: '$19.99/month',
            color: '#9C27B0'
        }
    };
    
    const info = tierInfo[tier];
    if (!info) {
        showUpgradeModal(companionId, tier, companionName);
        return;
    }
    
    // Create trial modal HTML with inline styles to ensure it displays
    const modalHtml = `
        <div id="trialModal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        " onclick="closeTrialModal(event)">
            <div style="
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                border: 2px solid #374151;
                border-radius: 16px;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
                animation: slideIn 0.3s ease;
                color: #e2e8f0;
            " onclick="event.stopPropagation()">
                <div style="
                    padding: 25px;
                    border-bottom: 2px solid #374151;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h2 style="margin: 0; color: ${info.color};">🎯 Try ${companionName} Free!</h2>
                    <button onclick="closeTrialModal()" style="
                        background: none;
                        border: none;
                        font-size: 28px;
                        cursor: pointer;
                        color: #94a3b8;
                        padding: 0;
                        width: 35px;
                        height: 35px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        transition: all 0.2s ease;
                    ">&times;</button>
                </div>
                
                <div style="padding: 20px; text-align: center;">
                    <div style="
                        margin-bottom: 20px;
                        padding: 20px;
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid #374151;
                        border-radius: 12px;
                        backdrop-filter: blur(10px);
                    ">
                        <p><strong>Get a 5-hour free trial</strong> of <strong>${companionName}</strong></p>
                        <p style="font-size: 18px; color: #22d3ee; font-weight: bold; margin: 15px 0;">
                            ⏰ 5 Hours Free Access
                        </p>
                        <p style="color: #94a3b8; font-size: 14px;">
                            Experience premium features with no commitment
                        </p>
                    </div>
                    
                    <div style="margin-top: 25px;">
                        <button onclick="startPremiumTrial('${companionId}')" style="
                            background: linear-gradient(135deg, #22d3ee, #0891b2);
                            color: white;
                            border: none;
                            padding: 16px 32px;
                            border-radius: 8px;
                            font-size: 18px;
                            font-weight: bold;
                            cursor: pointer;
                            margin-right: 15px;
                            box-shadow: 0 4px 12px rgba(34, 211, 238, 0.3);
                        ">
                            🎯 Start 5-Hour Trial
                        </button>
                        <button onclick="showUpgradeModal('${companionId}', '${tier}', '${companionName}'); closeTrialModal();" style="
                            background: ${info.color};
                            color: white;
                            border: none;
                            padding: 14px 28px;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: bold;
                            cursor: pointer;
                            margin: 5px;
                        ">
                            🚀 Upgrade to ${info.name}
                        </button>
                        <br>
                        <button onclick="closeTrialModal()" style="
                            background: rgba(55, 65, 81, 0.5);
                            color: #94a3b8;
                            border: 2px solid #374151;
                            padding: 12px 24px;
                            border-radius: 8px;
                            font-size: 16px;
                            cursor: pointer;
                            margin-top: 10px;
                        ">
                            Maybe Later
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <style>
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes slideIn {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        </style>
    `;
    
    // Remove existing modals
    const existingModal = document.getElementById('trialModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    console.log('✅ Trial modal added to page');
}

function closeTrialModal(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const modal = document.getElementById('trialModal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => modal.remove(), 300);
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
        
        // Growth/Premium companions - ALL 8 companions  
        'companion_sky': 'Sky',
        'blayzo_growth': 'Blayzo Pro',
        'blayzica_growth': 'Blayzica Pro',
        'companion_gamerjay_premium': 'GamerJay Premium',
        'watchdog_growth': 'WatchDog',
        'crimson_growth': 'Crimson',
        'violet_growth': 'Violet',
        'claude_growth': 'Claude Growth',
        
        // Max companions - ALL 7 companions
        'companion_crimson': 'Crimson Max',
        'companion_violet': 'Violet Max',
        'royal_max': 'Royal',
        'watchdog_max': 'WatchDog Max',
        'ven_blayzica': 'Ven Blayzica',
        'ven_sky': 'Ven Sky',
        'claude_max': 'Claude Max',
        
        // Referral companions - ALL 4 companions
        'blayzo': 'Blayzo Champion',
        'blayzike': 'Blayzike',
        'blazelian': 'Blazelian',
        'claude_referral': 'Claude Referral'
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
        
        // Growth/Premium companions - ALL 8 companions
        'companion_sky': 'sky',                            // backend constructs companion_sky ✓
        'blayzo_growth': 'blayzo_growth',                  // direct match in backend tier mapping ✓
        'blayzica_growth': 'blayzica_growth',              // direct match in backend tier mapping ✓
        'companion_gamerjay_premium': 'gamerjay_premium',  // backend constructs companion_gamerjay_premium ✓
        'watchdog_growth': 'watchdog_growth',              // direct match in backend tier mapping ✓
        'crimson_growth': 'crimson_growth',                // direct match in backend tier mapping ✓
        'violet_growth': 'violet_growth',                  // direct match in backend tier mapping ✓
        'claude_growth': 'claude_growth',                  // direct match in backend tier mapping ✓
        
        // Max companions - ALL 7 companions
        'companion_crimson': 'crimson',      // backend constructs companion_crimson ✓
        'companion_violet': 'violet',        // backend constructs companion_violet ✓
        'royal_max': 'royal_max',            // direct match in backend tier mapping ✓
        'watchdog_max': 'watchdog_max',      // direct match in backend tier mapping ✓
        'ven_blayzica': 'ven_blayzica',      // direct match in backend tier mapping ✓
        'ven_sky': 'ven_sky',                // direct match in backend tier mapping ✓
        'claude_max': 'claude_max',          // direct match in backend tier mapping ✓
        
        // Referral companions - ALL 4 companions
        'blayzo': 'blayzo',                  // direct match in backend tier mapping ✓
        'blayzike': 'blayzike',              // direct match in backend tier mapping ✓ 
        'blazelian': 'blazelian',            // direct match in backend tier mapping ✓
        'claude_referral': 'claude_referral' // direct match in backend tier mapping ✓
    };
    
    return urlParamMap[companionId] || companionId.replace('companion_', '');
}

function showUpgradeModal(companionId, tier, companionName) {
    console.log('💰 Showing upgrade modal for:', companionId, 'tier:', tier, 'name:', companionName);
    
    // Define tier pricing and features
    const tierInfo = {
        growth: {
            name: 'Growth Plan',
            price: '$12.99/month',
            features: [
                '8 Growth tier companions including Sky, Blayzo Pro, Blayzica Pro',
                'Enhanced AI capabilities and memory retention',
                'Advanced conversation features',
                'Priority response times',
                'Extended context understanding'
            ],
            color: '#4CAF50'
        },
        max: {
            name: 'Max Plan', 
            price: '$19.99/month',
            features: [
                '7 Elite Max tier companions including Crimson Max, Violet Max',
                'Ultimate AI capabilities and advanced reasoning',
                'Voice interactions and premium features',
                'Trauma healing and transformation coaching',
                'Priority support and exclusive access'
            ],
            color: '#9C27B0'
        }
    };
    
    const info = tierInfo[tier];
    if (!info) {
        showNotification('Upgrade information not available', 'error');
        return;
    }
    
    // Create modal HTML
    const modalHtml = `
        <div class="upgrade-modal-overlay" id="upgradeModal" onclick="closeUpgradeModal(event)">
            <div class="upgrade-modal-content" onclick="event.stopPropagation()">
                <div class="upgrade-modal-header">
                    <h2 style="margin: 0; color: ${info.color};">💎 Unlock ${companionName}</h2>
                    <button class="upgrade-modal-close" onclick="closeUpgradeModal()">&times;</button>
                </div>
                
                <div class="upgrade-modal-body">
                    <div class="upgrade-companion-preview">
                        <p><strong>${companionName}</strong> is part of our <strong>${info.name}</strong></p>
                        <p class="upgrade-price" style="font-size: 24px; color: ${info.color}; font-weight: bold;">
                            ${info.price}
                        </p>
                    </div>
                    
                    <div class="upgrade-features">
                        <h3>What you'll get with ${info.name}:</h3>
                        <ul style="text-align: left; margin: 0; padding-left: 20px;">
                            ${info.features.map(feature => `<li style="margin: 8px 0;">${feature}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="upgrade-actions" style="margin-top: 20px;">
                        <button class="upgrade-btn-primary" onclick="redirectToUpgrade('${tier}')" 
                                style="background: ${info.color}; color: white; border: none; padding: 14px 30px; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; margin-right: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                            🚀 Upgrade to ${info.name}
                        </button>
                        <button class="upgrade-btn-secondary" onclick="closeUpgradeModal()" 
                                style="background: rgba(55, 65, 81, 0.5); color: #94a3b8; border: 2px solid #374151; padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer; transition: all 0.2s ease;">
                            Maybe Later
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal styles
    const modalStyles = `
        <style id="upgradeModalStyles">
            .upgrade-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            
            .upgrade-modal-content {
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                border: 2px solid #374151;
                border-radius: 16px;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
                animation: slideIn 0.3s ease;
                color: #e2e8f0;
            }
            
            .upgrade-modal-header {
                padding: 25px;
                border-bottom: 2px solid #374151;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .upgrade-modal-close {
                background: none;
                border: none;
                font-size: 28px;
                cursor: pointer;
                color: #94a3b8;
                padding: 0;
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s ease;
            }
            
            .upgrade-modal-close:hover {
                color: #e2e8f0;
                background: rgba(248, 113, 113, 0.2);
            }
            
            .upgrade-modal-body {
                padding: 20px;
                text-align: center;
            }
            
            .upgrade-companion-preview {
                margin-bottom: 20px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #374151;
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            
            .upgrade-features {
                margin: 20px 0;
            }
            
            .upgrade-features h3 {
                color: #e2e8f0;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }
            
            .upgrade-btn-primary:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }
            
            .upgrade-btn-secondary:hover {
                background: #374151;
                color: #e2e8f0;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideIn {
                from { transform: translateY(20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        </style>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('upgradeModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const existingStyles = document.getElementById('upgradeModalStyles');
    if (existingStyles) {
        existingStyles.remove();
    }
    
    // Add styles and modal to page
    document.head.insertAdjacentHTML('beforeend', modalStyles);
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    
    // Add keyboard support (ESC to close)
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeUpgradeModal();
        }
    });
}

function closeUpgradeModal(event) {
    // Only close if clicking overlay, not modal content
    if (event && event.target !== event.currentTarget) {
        return;
    }
    
    const modal = document.getElementById('upgradeModal');
    const styles = document.getElementById('upgradeModalStyles');
    
    if (modal) {
        modal.remove();
    }
    if (styles) {
        styles.remove();
    }
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    console.log('🔒 Upgrade modal closed');
}

function redirectToUpgrade(tier) {
    console.log('🚀 Redirecting to upgrade page for tier:', tier);
    
    // Close modal first
    closeUpgradeModal();
    
    // Show notification about redirect
    showNotification(`Redirecting to ${tier === 'growth' ? 'Growth' : 'Max'} Plan upgrade...`, 'info');
    
    // Redirect to subscription page with tier pre-selected
    setTimeout(() => {
        console.log('🔄 Executing redirect to:', `/subscription?tier=${tier}`);
        window.location.href = `/subscription?tier=${tier}`;
    }, 1000);
}


// Make functions globally accessible
window.showTrialModal = showTrialModal;
window.closeTrialModal = closeTrialModal;
window.startPremiumTrial = startPremiumTrial;
window.showUpgradeModal = showUpgradeModal;
window.closeUpgradeModal = closeUpgradeModal;
window.redirectToUpgrade = redirectToUpgrade;

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

