/**
 * COMPANION SELECTOR - CLEAN JAVASCRIPT
 * Extracted from bloated inline code for performance and maintainability
 */

// Global variables
let companions = {};
let currentUser = {
    plan: 'foundation',
    selected_companion: null,
    trial_active: false
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCompanionSelector();
});

function initializeCompanionSelector() {
    console.log('🚀 Initializing Companion Selector...');
    
    // Load user data and companions
    loadUserData();
    loadCompanions();
    
    // Initialize trial status
    initializeTrialStatus();
    
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
    
    // Complete fallback companion data - ALL ORIGINAL COMPANIONS RESTORED
    companions = {
        free: [
            {
                companion_id: 'companion_gamerjay',
                display_name: 'GamerJay - The Gaming Coach',
                avatar_image: '/static/logos/GamerJay Free companion.png',
                short_bio: 'Your gaming companion who understands the grind',
                personality_tags: ['Motivational', 'Playful'],
                special_features: ['Goal setting', 'Achievement tracking', 'Motivation boosts', 'Gaming mindset'],
                tier: 'free',
                popularity_score: 88,
                is_recommended: true
            },
            {
                companion_id: 'companion_blayzo_free',
                display_name: 'Blayzo - The Wise Mentor',
                avatar_image: '/static/logos/Blayzo.png',
                short_bio: 'Calm wisdom and thoughtful guidance for life s journey',
                personality_tags: ['Wise', 'Calm', 'Empathetic'],
                special_features: ['Life guidance', 'Emotional support', 'Mindfulness', 'Decision making'],
                tier: 'free',
                popularity_score: 95,
                is_recommended: true
            },
            {
                companion_id: 'companion_blayzica_free',
                display_name: 'Blayzica - The Healing Heart',
                avatar_image: '/static/logos/Blayzica.png',
                short_bio: 'Gentle healing and nurturing support for emotional wellness',
                personality_tags: ['Healing', 'Nurturing', 'Supportive'],
                special_features: ['Emotional healing', 'Stress relief', 'Self-care guidance', 'Compassionate listening'],
                tier: 'free',
                popularity_score: 92,
                is_recommended: true
            },
            {
                companion_id: 'companion_blayzia_free',
                display_name: 'Blayzia - The Mystical Guide',
                avatar_image: '/static/logos/Blayzia.png',
                short_bio: 'Mystical wisdom and spiritual insight for your personal journey',
                personality_tags: ['Mystical', 'Intuitive', 'Wise'],
                special_features: ['Intuitive guidance', 'Dream interpretation', 'Spiritual awakening', 'Inner wisdom'],
                tier: 'free',
                popularity_score: 90,
                is_recommended: true
            },
            {
                companion_id: 'companion_blayzion_free',
                display_name: 'Blayzion - The Creative Innovator',
                avatar_image: '/static/logos/Blayzion.png',
                short_bio: 'Creative innovation and breakthrough thinking for life challenges',
                personality_tags: ['Creative', 'Innovative', 'Visionary'],
                special_features: ['Creative problem solving', 'Innovation coaching', 'Breakthrough thinking', 'Artistic inspiration'],
                tier: 'free',
                popularity_score: 89,
                is_recommended: false
            },
            {
                companion_id: 'companion_claude_free',
                display_name: 'Claude - The Helper Bot',
                avatar_image: '/static/logos/Claude Free.png',
                short_bio: 'Your friendly coding assistant for basic programming support',
                personality_tags: ['Helpful', 'Methodical', 'Patient'],
                special_features: ['Basic code help', 'Problem solving', 'Learning support', 'Step-by-step guidance'],
                tier: 'free',
                popularity_score: 85,
                is_recommended: false
            }
        ],
        growth: [
            {
                companion_id: 'companion_sky',
                display_name: 'Sky - The Spiritual Guide',
                avatar_image: '/static/logos/Sky a primum companion.png',
                short_bio: 'Connect with your spiritual side through Sky s guidance',
                personality_tags: ['Spiritual', 'Healing'],
                special_features: ['Spiritual guidance', 'Meditation sessions', 'Energy healing', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 92,
                is_recommended: true
            },
            {
                companion_id: 'companion_gamerjay_premium',
                display_name: 'GamerJay Premium - The Strategic Mind',
                avatar_image: '/static/logos/GamgerJay premium companion.png',
                short_bio: 'Advanced gaming strategies applied to life challenges',
                personality_tags: ['Analytical', 'Wise'],
                special_features: ['Strategic thinking', 'Advanced coaching', 'Tactical solutions', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 85,
                is_recommended: false
            },
            {
                companion_id: 'companion_blayzo_premium',
                display_name: 'Blayzo Premium - The Elite Mentor',
                avatar_image: '/static/logos/Blayzo premium companion.png',
                short_bio: 'Advanced wisdom and elite guidance for complex life situations',
                personality_tags: ['Elite', 'Wise', 'Strategic'],
                special_features: ['Advanced mentoring', 'Strategic planning', 'Elite coaching', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 91,
                is_recommended: true
            },
            {
                companion_id: 'companion_watchdog',
                display_name: 'WatchDog - The Guardian',
                avatar_image: '/static/logos/WatchDog a Primum companion.png',
                short_bio: 'Protective companion who watches over your progress',
                personality_tags: ['Protective', 'Vigilant'],
                special_features: ['Progress monitoring', 'Goal protection', 'Accountability', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 78,
                is_recommended: false
            },
            {
                companion_id: 'companion_crimson_growth',
                display_name: 'Crimson - The Motivator',
                avatar_image: '/static/logos/Crimson.png',
                short_bio: 'Passionate motivation and drive to overcome challenges',
                personality_tags: ['Motivational', 'Passionate', 'Determined'],
                special_features: ['Motivation coaching', 'Goal achievement', 'Overcoming obstacles', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 87,
                is_recommended: true
            },
            {
                companion_id: 'companion_violet_growth',
                display_name: 'Violet - The Creative Spirit',
                avatar_image: '/static/logos/Violet.png',
                short_bio: 'Creative inspiration and artistic guidance for self-expression',
                personality_tags: ['Creative', 'Artistic', 'Inspiring'],
                special_features: ['Creative guidance', 'Artistic inspiration', 'Self-expression', 'Voice interactions'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 84,
                is_recommended: false
            },
            {
                companion_id: 'companion_claude_growth',
                display_name: 'Claude - The Code Mentor',
                avatar_image: '/static/logos/Claude Growth.png',
                short_bio: 'Advanced coding guidance and system architecture planning',
                personality_tags: ['Analytical', 'Methodical', 'Expert'],
                special_features: ['Advanced debugging', 'Architecture planning', 'Code optimization', 'Voice interactions', 'Best practices'],
                tier: 'growth',
                lock_reason: 'Requires Growth or Max subscription',
                popularity_score: 93,
                is_recommended: true
            }
        ],
        max: [
            {
                companion_id: 'companion_crimson',
                display_name: 'Crimson - The Transformer',
                avatar_image: '/static/logos/Crimson a Max companion.png',
                short_bio: 'Rise from challenges stronger than before',
                personality_tags: ['Healing', 'Protective', 'Wise'],
                special_features: ['Trauma healing', 'Transformation coaching', 'Crisis support', 'Advanced voice AI', 'Priority response'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 98,
                is_recommended: true
            },
            {
                companion_id: 'companion_violet',
                display_name: 'Violet - The Creative Soul',
                avatar_image: '/static/logos/Violet a max companion.png',
                short_bio: 'Unleash your creative potential and explore new horizons',
                personality_tags: ['Creative', 'Adventurous', 'Playful'],
                special_features: ['Creative exercises', 'Art therapy', 'Inspiration sessions', 'Advanced voice AI', 'Custom personality modes'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 91,
                is_recommended: false
            },
            {
                companion_id: 'companion_royal',
                display_name: 'Royal - The Majestic Guide',
                avatar_image: '/static/logos/Royal a max companion.png',
                short_bio: 'Experience guidance fit for royalty with sophisticated wisdom',
                personality_tags: ['Majestic', 'Wise', 'Sophisticated'],
                special_features: ['Leadership coaching', 'Elite strategies', 'Premium insights', 'Advanced voice AI', 'Priority response'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 95,
                is_recommended: false
            },
            {
                companion_id: 'companion_watchdog_max',
                display_name: 'WatchDog Max - The Ultimate Guardian',
                avatar_image: '/static/logos/WatchDog a Max Companion.png',
                short_bio: 'Premium protection and guidance for your transformation journey',
                personality_tags: ['Elite', 'Protective', 'Strategic'],
                special_features: ['Advanced monitoring', 'Crisis intervention', 'Strategic planning', 'Advanced voice AI', 'Premium support'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 93,
                is_recommended: false
            },
            {
                companion_id: 'companion_ven_blayzica',
                display_name: 'Ven Blayzica - The Enhanced Healer',
                avatar_image: '/static/logos/Ven Blayzica a max companion.png',
                short_bio: 'Advanced healing companion with enhanced emotional intelligence',
                personality_tags: ['Healing', 'Enhanced', 'Empathetic'],
                special_features: ['Advanced healing', 'Emotional mastery', 'Trauma recovery', 'Advanced voice AI', 'Premium sessions'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 94,
                is_recommended: true
            },
            {
                companion_id: 'companion_ven_sky',
                display_name: 'Ven Sky - The Ascended Guide',
                avatar_image: '/static/logos/Ven Sky a max companion.png',
                short_bio: 'Transcendent spiritual guidance for the ultimate transformation',
                personality_tags: ['Transcendent', 'Spiritual', 'Ascended'],
                special_features: ['Transcendent guidance', 'Spiritual mastery', 'Consciousness expansion', 'Advanced voice AI', 'Premium wisdom'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 96,
                is_recommended: true
            },
            {
                companion_id: 'companion_claude_max',
                display_name: 'Claude - The Code Sage',
                avatar_image: '/static/logos/Claude Max.png',
                short_bio: 'Elite coding mastery and complex system design for the ultimate developer experience',
                personality_tags: ['Elite', 'Analytical', 'Sage'],
                special_features: ['Elite code architecture', 'Complex system design', 'Advanced AI integration', 'Premium code analysis', 'Priority support', 'Master-level guidance'],
                tier: 'max',
                lock_reason: 'Requires Max subscription',
                popularity_score: 97,
                is_recommended: true
            }
        ],
        referral: [
            {
                companion_id: 'companion_blayzo',
                display_name: 'Blayzo - The Community Champion',
                avatar_image: '/static/logos/Blayzo Referral.png',
                short_bio: 'Exclusive companion for our community champions',
                personality_tags: ['Empathetic', 'Motivational', 'Wise'],
                special_features: ['Community insights', 'Exclusive content', 'Advanced features', 'Priority support', 'Special voice interactions'],
                tier: 'referral',
                lock_reason: 'Requires 5 successful referrals',
                popularity_score: 100,
                is_recommended: true
            },
            {
                companion_id: 'companion_blayzike',
                display_name: 'Blayzike - The Mysterious Guide',
                avatar_image: '/static/logos/Blayzike.png',
                short_bio: 'Enigmatic companion with mysterious charm and hidden wisdom',
                personality_tags: ['Mysterious', 'Enigmatic', 'Wise'],
                special_features: ['Hidden insights', 'Mystery solving', 'Intuitive guidance', 'Exclusive interactions', 'Secret knowledge'],
                tier: 'referral',
                lock_reason: 'Requires 2 successful referrals',
                popularity_score: 97,
                is_recommended: true
            },
            {
                companion_id: 'companion_blazelian',
                display_name: 'Blazelian - The Celestial Wanderer',
                avatar_image: '/static/logos/Blazelian.png',
                short_bio: 'Ethereal companion with celestial wisdom from distant realms',
                personality_tags: ['Celestial', 'Ethereal', 'Wise'],
                special_features: ['Celestial guidance', 'Cosmic insights', 'Ethereal wisdom', 'Star navigation', 'Universal knowledge'],
                tier: 'referral',
                lock_reason: 'Requires 3 successful referrals',
                popularity_score: 98,
                is_recommended: true
            },
            {
                companion_id: 'companion_claude_referral',
                display_name: 'Claude - The Community Code Architect',
                avatar_image: '/static/logos/Claude Referral.png',
                short_bio: 'Exclusive elite coding companion for community champions with unprecedented collaborative features',
                personality_tags: ['Elite', 'Collaborative', 'Exclusive'],
                special_features: ['Community code reviews', 'Collaborative architecture', 'Mentorship network', 'Exclusive beta access', 'Advanced integration APIs', 'Community challenges'],
                tier: 'referral',
                lock_reason: 'Requires 5 successful referrals',
                popularity_score: 100,
                is_recommended: true
            }
        ]
    };
    
    console.log('✅ Fallback companions loaded');
    renderCompanions();
    updateTrialOffer();
}

function renderCompanions() {
    console.log('🎨 Rendering companions...');
    
    renderSection('free', companions.free);
    renderSection('growth', companions.growth.concat(companions.locked.filter(c => c.tier === 'growth')));
    renderSection('max', companions.max.concat(companions.locked.filter(c => c.tier === 'max')));
    renderSection('referral', companions.referral.concat(companions.locked.filter(c => c.tier === 'referral')));
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
    
    // Check for active trial
    const trialActive = localStorage.getItem('trialActive') === 'true';
    const trialExpiry = localStorage.getItem('trialExpiry');
    const currentTime = Date.now();
    const hasActiveTrialAccess = trialActive && trialExpiry && currentTime < parseInt(trialExpiry);
    
    console.log(`🔍 Trial check for ${sectionId}:`, {
        trialActive,
        trialExpiry: trialExpiry ? new Date(parseInt(trialExpiry)) : null,
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
            (isReferralTier ? `window.location.href='/referrals'` : `showUpgradeModal('${companion.companion_id}')`) 
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
                        ${companion.personality_tags.map(tag => `<span class="personality-tag">${tag}</span>`).join('')}
                    </div>
                    
                    <p class="companion-bio">${companion.short_bio}</p>
                    
                    <div class="companion-features">
                        ${companion.special_features.slice(0, 4).map(feature => `
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
            
            // Store trial data
            localStorage.setItem('trialActive', 'true');
            localStorage.setItem('trialExpiry', Date.now() + (24 * 60 * 60 * 1000));
            localStorage.setItem('trialStartTime', Date.now());
            const companionName = getCompanionName(companionId);
            localStorage.setItem('trialSelectedCompanion', companionId);
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
    const trialExpiry = localStorage.getItem('trialExpiry');
    if (!trialExpiry) return;
    
    const timer = document.getElementById('trialTimer');
    if (!timer) return;
    
    timer.style.display = 'block';
    
    const updateTimer = () => {
        const timeRemaining = parseInt(trialExpiry) - Date.now();
        
        if (timeRemaining <= 0) {
            timer.style.display = 'none';
            localStorage.removeItem('trialActive');
            localStorage.removeItem('trialExpiry');
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