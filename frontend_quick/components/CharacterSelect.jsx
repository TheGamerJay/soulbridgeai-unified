import React, { useState, useEffect } from 'react';

export default function CharacterSelect({ onSelect }) {
  const [companions, setCompanions] = useState({ bronze: [], silver: [], gold: [], referral: [] });
  const [selectedTier, setSelectedTier] = useState('bronze');
  const [loading, setLoading] = useState(true);
  const [userPlan, setUserPlan] = useState('bronze');
  const [trialActive, setTrialActive] = useState(false);
  const [effectivePlan, setEffectivePlan] = useState('bronze');

  useEffect(() => {
    // Fetch available companions from the API
    const fetchCompanions = async () => {
      try {
        const response = await fetch('/api/companions');
        const data = await response.json();
        
        if (data.success) {
          setCompanions(data.companions);
          setUserPlan(data.user_plan || 'bronze');
          setTrialActive(data.trial_active || false);
          setEffectivePlan(data.effective_plan || data.user_plan || 'bronze');
        }
      } catch (error) {
        console.error('Error fetching companions:', error);
        // Fallback to basic companions if API fails
        setCompanions({
          bronze: [
            { companion_id: 'blayzo_free', display_name: 'Blayzo', description: 'Your creative and fun AI companion', tier: 'bronze', lock_reason: null },
            { companion_id: 'blayzica_free', display_name: 'Blayzica', description: 'Your empathetic and caring AI companion', tier: 'bronze', lock_reason: null }
          ],
          silver: [],
          gold: [],
          referral: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchCompanions();
  }, []);

  const handleCharacterSelect = (companionId) => {
    if (onSelect && typeof onSelect === 'function') {
      onSelect(companionId);
    } else {
      console.error('onSelect is not a function');
    }
  };

  const handleKeyPress = (e, companionId) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCharacterSelect(companionId);
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'bronze': return 'from-blue-600 to-blue-800 hover:from-blue-500 hover:to-blue-700 focus:ring-blue-300';
      case 'silver': return 'from-green-600 to-green-800 hover:from-green-500 hover:to-green-700 focus:ring-green-300';
      case 'gold': return 'from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 focus:ring-purple-300';
      case 'referral': return 'from-yellow-600 to-yellow-800 hover:from-yellow-500 hover:to-yellow-700 focus:ring-yellow-300';
      default: return 'from-gray-600 to-gray-800 hover:from-gray-500 hover:to-gray-700 focus:ring-gray-300';
    }
  };

  const getTierTitle = (tier) => {
    switch (tier) {
      case 'bronze': return '🥉 Bronze Companions';
      case 'silver': return '🥈 Silver Tier';
      case 'gold': return '🥇 Gold Tier';
      case 'referral': return '🏆 Referral Exclusive';
      default: return tier;
    }
  };

  const isCompanionLocked = (companion) => {
    return companion.lock_reason !== null && companion.lock_reason !== undefined;
  };

  // Determine which tiers the user can access based on subscription and trial
  const getAccessibleTiers = () => {
    if (trialActive) {
      // During trial: unlock Silver/Gold companions regardless of subscription tier (referral companions remain locked)
      return ['bronze', 'silver', 'gold'];
    } else {
      // Normal access based on subscription tier
      switch (userPlan) {
        case 'bronze':
        case 'free': // Legacy compatibility
          return ['bronze'];
        case 'silver':
        case 'growth': // Legacy compatibility
          return ['bronze', 'silver'];
        case 'gold':
        case 'max': // Legacy compatibility
          return ['bronze', 'silver', 'gold'];
        default:
          return ['bronze'];
      }
    }
  };

  const accessibleTiers = getAccessibleTiers();

  // Filter companions to only show accessible ones in the tier tabs
  const getVisibleTiers = () => {
    const visibleTiers = {};
    Object.keys(companions).forEach(tier => {
      if (companions[tier].length > 0) {
        visibleTiers[tier] = companions[tier];
      }
    });
    return visibleTiers;
  };

  const visibleTiers = getVisibleTiers();

  const renderCompanion = (companion) => {
    const locked = isCompanionLocked(companion);
    const tierColors = getTierColor(companion.tier);
    const isAccessible = accessibleTiers.includes(companion.tier);
    
    // Override lock status based on user access
    const actuallyLocked = locked || !isAccessible;
    
    return (
      <button
        key={companion.companion_id}
        onClick={() => !actuallyLocked && handleCharacterSelect(companion.companion_id)}
        onKeyDown={(e) => !actuallyLocked && handleKeyPress(e, companion.companion_id)}
        disabled={actuallyLocked}
        className={`relative px-6 py-4 rounded-xl text-white font-bold shadow-2xl transform transition-all duration-300 focus:outline-none focus:ring-4 active:scale-95 min-w-[200px] ${
          actuallyLocked 
            ? 'bg-gradient-to-r from-gray-500 to-gray-700 cursor-not-allowed opacity-60' 
            : `bg-gradient-to-r ${tierColors} hover:scale-105 cursor-pointer`
        }`}
        tabIndex={actuallyLocked ? -1 : 0}
        role="button"
        aria-label={`Select ${companion.display_name} as your AI companion`}
      >
        {actuallyLocked && (
          <div className="absolute top-2 right-2">
            🔒
          </div>
        )}
        {!actuallyLocked && trialActive && companion.tier !== 'bronze' && (
          <div className="absolute top-2 right-2">
            🕒
          </div>
        )}
        <div className="text-lg font-bold">{companion.display_name}</div>
        <div className="text-sm opacity-90 mt-1">{companion.description}</div>
        {actuallyLocked && (
          <div className="text-xs mt-2 text-yellow-300">
            {!isAccessible ? `Requires ${companion.tier.charAt(0).toUpperCase() + companion.tier.slice(1)} Plan` : companion.lock_reason}
          </div>
        )}
        {!actuallyLocked && trialActive && companion.tier !== 'bronze' && (
          <div className="text-xs mt-2 text-green-300">
            ⏰ Trial Access
          </div>
        )}
      </button>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8 bg-gradient-to-b from-gray-900 to-black">
        <div className="text-cyan-400 text-2xl">Loading companions...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8 bg-gradient-to-b from-gray-900 to-black">
      <h1 className="text-4xl font-bold mb-8 text-cyan-400 drop-shadow-lg text-center">
        Choose Your AI Companion
      </h1>
      <p className="text-cyan-300 mb-8 text-center max-w-md">
        Select the companion that resonates with you from your available tiers
      </p>

      {/* Tier Navigation */}
      <div className="flex flex-wrap gap-4 mb-8 justify-center">
        {Object.keys(visibleTiers).map((tier) => {
          const isAccessible = accessibleTiers.includes(tier);
          return (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all duration-300 relative ${
                selectedTier === tier
                  ? 'bg-cyan-600 text-white'
                  : isAccessible 
                    ? 'bg-gray-700 text-cyan-300 hover:bg-gray-600'
                    : 'bg-gray-800 text-gray-500 cursor-not-allowed opacity-60'
              }`}
              disabled={!isAccessible}
            >
              {!isAccessible && (
                <span className="absolute -top-1 -right-1">🔒</span>
              )}
              {isAccessible && trialActive && tier !== 'bronze' && (
                <span className="absolute -top-1 -right-1">🕒</span>
              )}
              {getTierTitle(tier)} ({companions[tier].length})
            </button>
          );
        })}
      </div>

      {/* Current User Plan Info */}
      <div className="mb-6 text-center">
        <p className="text-cyan-300 text-sm">
          Subscription: <span className="font-bold text-cyan-400">{userPlan.charAt(0).toUpperCase() + userPlan.slice(1)}</span>
          {trialActive ? (
            <span className="text-green-400 ml-2">• 🕒 5-Hour Trial Active</span>
          ) : (
            <span className="text-gray-400 ml-2">• 🔓 Normal Access</span>
          )}
        </p>
        {trialActive && (
          <p className="text-green-300 text-xs mt-1">
            ⏰ Trial unlocks all companions but keeps your {userPlan} usage limits
          </p>
        )}
      </div>

      {/* Companions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl">
        {companions[selectedTier]?.map(renderCompanion)}
      </div>

      {/* Tier Info */}
      <div className="mt-8 text-cyan-300 text-center text-sm opacity-75 max-w-lg">
        {selectedTier === 'bronze' && (
          <p>🥉 Available to all users at any time</p>
        )}
        {selectedTier === 'silver' && !accessibleTiers.includes('silver') && (
          <p>🥈 Silver tier companions require Silver subscription or trial</p>
        )}
        {selectedTier === 'silver' && accessibleTiers.includes('silver') && (
          <p>🥈 Enhanced companions with advanced features</p>
        )}
        {selectedTier === 'gold' && !accessibleTiers.includes('gold') && (
          <p>🥇 Gold tier companions require Gold subscription or trial</p>
        )}
        {selectedTier === 'gold' && accessibleTiers.includes('gold') && (
          <p>🥇 Elite companions with premium AI models and unlimited features</p>
        )}
        {selectedTier === 'referral' && !accessibleTiers.includes('referral') && (
          <p>🏆 Exclusive companions require Gold subscription or trial</p>
        )}
        {selectedTier === 'referral' && accessibleTiers.includes('referral') && (
          <p>🏆 Exclusive companions unlocked through community referrals</p>
        )}
      </div>

      {/* Access Summary */}
      {!trialActive && (
        <div className="mt-4 text-center text-xs opacity-60 max-w-2xl">
          <p className="text-gray-400">
            {userPlan === 'bronze' && '🔒 Upgrade to Silver for enhanced companions • Upgrade to Gold for elite companions'}
            {userPlan === 'silver' && '✅ You have access to Bronze + Silver companions • Upgrade to Gold for elite companions'}
            {userPlan === 'gold' && '✅ You have access to all companion tiers'}
          </p>
        </div>
      )}
      {trialActive && (
        <div className="mt-4 text-center text-xs max-w-2xl">
          <p className="text-green-400">
            🕒 Trial Mode: Silver/Gold companions unlocked for 5 hours! Usage limits remain at your {userPlan} tier level.
          </p>
          <p className="text-yellow-400 mt-1">
            After trial ends, access returns to your {userPlan} subscription level.
          </p>
        </div>
      )}
    </div>
  );
}
