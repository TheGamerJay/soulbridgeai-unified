/**
 * COMPANION SELECTOR - CLEAN JAVASCRIPT
 * Extracted from bloated inline code for performance and maintainability
 */

// Global variables
let companions = {};
let currentUser = {
    plan: 'foundation',
    selected_companion: null,
    trial_active: false,
    trial_expires: null,
    trial_companion: null
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCompanionSelector();
});

async function initializeCompanionSelector() {
    console.log('🚀 Initializing Companion Selector...');
    
    // Load user data and companions (sync with backend)
    await loadUserDataFromBackend();
    loadCompanions();
    
    // Initialize trial status from backend
    await initializeTrialStatusFromBackend();
    
    // Set up event listeners
    setupEventListeners();
    
    // Handle switching from chat
    handleChatSwitching();
    
    console.log('✅ Companion Selector initialized');
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
    // Add any additional event listeners here
    document.addEventListener('visibilitychange', handleVisibilityChange);
}

async function loadUserDataFromBackend() {
    try {
        console.log('👤 Loading user data from backend...');
        const response = await fetch('/api/user/status');
        if (response.ok) {
            const userData = await response.json();
            currentUser.plan = userData.plan || 'foundation';
            currentUser.trial_active = userData.trial_active || false;
            currentUser.trial_expires = userData.trial_expires || null;
            currentUser.trial_companion = userData.trial_companion || null;
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

async function loadUserData() {
    try {
        console.log('👤 Loading user data...');
        // This would typically fetch from an API
        // For now, using defaults
        currentUser.plan = 'foundation';
        console.log('✅ User data loaded:', currentUser);
    } catch (error) {
        console.error('❌ Error loading user data:', error);
    }
}

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
            updateTrialOffer();
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
                lock_reason: 'Requires Growth Plan',
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
                lock_reason: 'Requires Growth Plan',
                popularity_score: 92,
                is_recommended: true
            },
            {
                companion_id: 'blayzica_growth',
                display_name: 'Blayzica Pro',
                avatar_image: '/static/logos/Blayzica.png',
                short_bio: 'Enhanced Blayzica with deeper emotional intelligence',
                personality_tags: ['Empathetic', 'Intelligent'],
                special_features: ['Deep emotional support', 'Advanced empathy', 'Personalized guidance', 'Crisis support'],
                tier: 'growth',
                lock_reason: 'Requires Growth Plan',
                popularity_score: 91,
                is_recommended: true
            },
            {
                companion_id: 'companion_gamerjay_premium',
                display_name: 'GamerJay Premium',
                avatar_image: '/static/logos/GamgerJay premium companion.png',
                short_bio: 'Enhanced GamerJay with premium features',
                personality_tags: ['Gaming', 'Premium'],
                special_features: ['Pro gaming strategies', 'Performance analysis', 'Competitive coaching', 'Advanced metrics'],
                tier: 'growth',
                lock_reason: 'Requires Growth Plan',
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
                lock_reason: 'Requires Transformation Plan',
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
                lock_reason: 'Requires Transformation Plan',
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
    updateTrialOffer();
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
    
    // Check for active trial from backend data
    const currentTime = Date.now();
    const hasActiveTrialAccess = currentUser.trial_active && 
                                currentUser.trial_expires && 
                                currentTime < new Date(currentUser.trial_expires).getTime();
    
    console.log(`🔍 Trial check for ${sectionId}:`, {
        trial_active: currentUser.trial_active,
        trial_expires: currentUser.trial_expires ? new Date(currentUser.trial_expires) : null,
        hasActiveTrialAccess
    });
    
    container.innerHTML = companionList.map(companion => {
        let isLocked = companion.lock_reason;
        
        // If trial is active, unlock ONLY Growth companions (not Max)
        if (hasActiveTrialAccess && companion.tier === 'growth') {
            isLocked = false;
            console.log(`🔓 UNLOCKED for trial: ${companion.display_name}`);
        }
        
        const isSelected = currentUser.selected_companion === companion.companion_id;
        const isReferralTier = companion.tier === 'referral';
        const clickAction = isLocked ? 
            (isReferralTier ? `window.location.href='/referrals'` : `showCompanionDetails('${companion.companion_id}')`) 
            : `selectCompanion('${companion.companion_id}')`;
        
        return `
            <div class="companion-card ${isLocked ? 'locked' : ''} ${isSelected ? 'selected' : ''}" 
                 onclick="${clickAction}">
                
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
                            <button class="btn-select ${isSelected ? 'selected' : ''}" 
                                    ${isSelected ? 'disabled' : ''}
                                    onclick="${isSelected ? '' : (hasActiveTrialAccess && companion.tier === 'growth' ? `startPremiumTrial('${companion.companion_id}')` : `selectCompanion('${companion.companion_id}')`)}">
                                ${isSelected ? 'Selected' : (hasActiveTrialAccess && companion.tier === 'growth' ? '✨ Try Premium' : 'Select')}
                            </button>
                        ` : `
                            <button class="btn-select" disabled style="${isReferralTier ? 'background: #FFD700; color: #333;' : 'background: #ccc; color: #666; cursor: not-allowed;'}">
                                ${isReferralTier ? '👥 View Referral Program' : `🔒 ${companion.lock_reason}`}
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

async function selectCompanion(companionId) {
    console.log('🤖 Selecting companion:', companionId);
    
    try {
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
            
            // Update UI
            currentUser.selected_companion = companionId;
            renderCompanions();
            
            // Store selection for instant access
            const companionName = getCompanionName(companionId);
            localStorage.setItem('selectedCharacter', companionName);
            localStorage.setItem('currentScreen', 'chat');
            localStorage.setItem('companionSelectionTime', Date.now());
            
            // Show success message
            showNotification(`${companionName} companion selected! Redirecting...`, 'success');
            
            // Immediate redirect for smooth flow
            setTimeout(() => {
                window.location.href = `/chat?companion=${companionName.toLowerCase()}`;
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

async function startPremiumTrial(companionId) {
    console.log('🚀 Starting premium trial for companion:', companionId);
    
    try {
        const response = await fetch('/api/companions/trial', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                companion_id: companionId,
                trial_type: 'companion_specific'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Premium trial started successfully');
            showNotification(`Premium trial started! Enjoy 24 hours with your premium companion.`, 'success');
            
            // Update currentUser with backend data (no localStorage for trial data)
            currentUser.trial_active = data.trial_active;
            currentUser.trial_expires = data.trial_expires;
            currentUser.trial_companion = companionId;
            currentUser.plan = 'trial';
            
            // Keep necessary localStorage for UI state only
            const companionName = getCompanionName(companionId);
            localStorage.setItem('selectedCharacter', companionName);
            localStorage.setItem('currentScreen', 'chat');
            localStorage.setItem('hasActiveChat', 'true');
            localStorage.setItem('companionSelectionTime', Date.now());
            sessionStorage.setItem('hasActiveChat', 'true');
            
            // Redirect to chat with instant companion loading
            console.log('🔄 Redirecting to chat with premium companion:', companionName);
            window.location.href = `/chat?companion=${companionName.toLowerCase()}&trial=true`;
            
        } else {
            console.error('❌ Premium trial failed:', data.error);
            showNotification(data.error || 'Failed to start premium trial', 'error');
        }
        
    } catch (error) {
        console.error('❌ Premium trial error:', error);
        showNotification('Failed to start premium trial', 'error');
    }
}

function getCompanionName(companionId) {
    const nameMap = {
        'companion_gamerjay': 'GamerJay',
        'companion_sky': 'Sky',
        'companion_crimson': 'Crimson',
        'companion_violet': 'Violet',
        'companion_blayzo': 'Blayzo'
    };
    
    return nameMap[companionId] || companionId.replace('companion_', '').charAt(0).toUpperCase() + companionId.replace('companion_', '').slice(1);
}

function showUpgradeModal(companionId) {
    console.log('💰 Showing upgrade modal for:', companionId);
    // Implement upgrade modal logic
    showNotification('Upgrade required for this companion', 'info');
}

function updateTrialOffer() {
    // Update trial offer section if needed
    console.log('🎯 Trial offer updated');
}

async function initializeTrialStatusFromBackend() {
    try {
        console.log('⏰ Loading trial status from backend...');
        const response = await fetch('/api/debug/trial-status');
        if (response.ok) {
            const data = await response.json();
            const trialData = data.trial_data;
            
            if (trialData.trial_active && trialData.trial_expires) {
                currentUser.trial_active = true;
                currentUser.trial_expires = trialData.trial_expires;
                currentUser.trial_companion = trialData.trial_companion;
                
                // Start timer if trial is still active
                if (!trialData.trial_expired) {
                    console.log('⏰ Active trial detected from backend, starting timer');
                    startTrialTimer();
                }
            }
            console.log('✅ Trial status loaded from backend:', currentUser);
        }
    } catch (error) {
        console.error('❌ Error loading trial status from backend:', error);
    }
}

function initializeTrialStatus() {
    // Check if user has active trial
    const trialActive = localStorage.getItem('trialActive') === 'true';
    const trialExpiry = localStorage.getItem('trialExpiry');
    
    if (trialActive && trialExpiry) {
        const timeRemaining = parseInt(trialExpiry) - Date.now();
        if (timeRemaining > 0) {
            console.log('⏰ Active trial detected, starting timer');
            startTrialTimer();
        } else {
            console.log('⏰ Trial expired, cleaning up');
            localStorage.removeItem('trialActive');
            localStorage.removeItem('trialExpiry');
        }
    }
}

function startTrialTimer() {
    // Use backend trial data instead of localStorage
    if (!currentUser.trial_expires || !currentUser.trial_active) return;
    
    const timer = document.getElementById('trialTimer');
    if (!timer) return;
    
    timer.style.display = 'block';
    
    const updateTimer = () => {
        const trialExpiryTime = new Date(currentUser.trial_expires).getTime();
        const timeRemaining = trialExpiryTime - Date.now();
        
        if (timeRemaining <= 0) {
            timer.style.display = 'none';
            currentUser.trial_active = false;
            currentUser.trial_expires = null;
            return;
        }
        
        const hours = Math.floor(timeRemaining / (1000 * 60 * 60));
        const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
        
        const display = document.getElementById('trialTimeDisplay');
        if (display) {
            display.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    };
    
    updateTimer();
    setInterval(updateTimer, 1000);
}

function showNotification(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
    
    // Create notification element
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
    
    // Slide in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Slide out and remove
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Companion Details Modal Functions
function showCompanionDetails(companionId) {
    const companion = findCompanionById(companionId);
    if (!companion) {
        console.error('Companion not found:', companionId);
        return;
    }
    
    // Populate modal with companion data
    document.getElementById('modalCompanionName').textContent = companion.display_name;
    document.getElementById('modalCompanionAvatar').src = companion.avatar_image;
    document.getElementById('modalCompanionBio').textContent = companion.short_bio || companion.description;
    document.getElementById('modalCompanionTier').textContent = `${companion.tier.toUpperCase()} TIER`;
    
    // Show appropriate upgrade options based on companion tier
    const upgradeSection = document.getElementById('upgradeSection');
    const growthPlan = document.querySelector('.growth-plan');
    const maxPlan = document.querySelector('.max-plan');
    
    if (companion.tier === 'growth') {
        growthPlan.style.display = 'block';
        maxPlan.style.display = 'block';
        growthPlan.classList.add('recommended');
        maxPlan.classList.remove('recommended');
    } else if (companion.tier === 'max') {
        growthPlan.style.display = 'none';
        maxPlan.style.display = 'block';
        maxPlan.classList.add('recommended');
    }
    
    // Show modal
    document.getElementById('companionModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeCompanionModal() {
    document.getElementById('companionModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function selectUpgradePlan(planType) {
    closeCompanionModal();
    
    // Redirect to plan selection page
    if (planType === 'growth') {
        window.location.href = '/plan-selection?plan=growth';
    } else if (planType === 'max') {
        window.location.href = '/plan-selection?plan=max';
    }
}

function findCompanionById(companionId) {
    const allCompanions = [
        ...(companions.free || []),
        ...(companions.growth || []),
        ...(companions.max || []),
        ...(companions.referral || [])
    ];
    
    return allCompanions.find(c => c.companion_id === companionId);
}

// Close modal when pressing Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCompanionModal();
    }
});

// Export functions for testing
window.showCompanionDetails = showCompanionDetails;
window.closeCompanionModal = closeCompanionModal;

function navigateBack() {
    window.history.back();
}

function handleVisibilityChange() {
    if (!document.hidden) {
        // Page became visible, refresh companion data
        loadCompanions();
    }
}

async function previewVoice(companionId) {
    showNotification('Voice preview coming soon!', 'info');
}