import React, { useState, useEffect } from 'react';

export default function CharacterSelect({ onSelect }) {
  const [companions, setCompanions] = useState({ free: [], growth: [], max: [], referral: [] });
  const [selectedTier, setSelectedTier] = useState('free');
  const [loading, setLoading] = useState(true);
  const [userPlan, setUserPlan] = useState('free');
  const [trialActive, setTrialActive] = useState(false);

  useEffect(() => {
    // Fetch available companions from the API
    const fetchCompanions = async () => {
      try {
        const response = await fetch('/api/companions');
        const data = await response.json();
        
        if (data.success) {
          setCompanions(data.companions);
          setUserPlan(data.user_plan || 'free');
          setTrialActive(data.trial_active || false);
        }
      } catch (error) {
        console.error('Error fetching companions:', error);
        // Fallback to basic companions if API fails
        setCompanions({
          free: [
            { companion_id: 'blayzo_free', display_name: 'Blayzo', description: 'Your creative and fun AI companion', tier: 'free', lock_reason: null },
            { companion_id: 'blayzica_free', display_name: 'Blayzica', description: 'Your empathetic and caring AI companion', tier: 'free', lock_reason: null }
          ],
          growth: [],
          max: [],
          referral: []
        });
      } finally {
        setLoading(false);
      }
    };

    fetchCompanions();
  }, []);

  const handleCharacterSelect = (companionId) => {
    console.log(`${companionId} selected`);
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
      case 'free': return 'from-blue-600 to-blue-800 hover:from-blue-500 hover:to-blue-700 focus:ring-blue-300';
      case 'growth': return 'from-green-600 to-green-800 hover:from-green-500 hover:to-green-700 focus:ring-green-300';
      case 'max': return 'from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 focus:ring-purple-300';
      case 'referral': return 'from-yellow-600 to-yellow-800 hover:from-yellow-500 hover:to-yellow-700 focus:ring-yellow-300';
      default: return 'from-gray-600 to-gray-800 hover:from-gray-500 hover:to-gray-700 focus:ring-gray-300';
    }
  };

  const getTierTitle = (tier) => {
    switch (tier) {
      case 'free': return '🆓 Free Companions';
      case 'growth': return '🌱 Growth Tier';
      case 'max': return '⚡ Max Tier';
      case 'referral': return '🏆 Referral Exclusive';
      default: return tier;
    }
  };

  const isCompanionLocked = (companion) => {
    return companion.lock_reason !== null && companion.lock_reason !== undefined;
  };

  const renderCompanion = (companion) => {
    const locked = isCompanionLocked(companion);
    const tierColors = getTierColor(companion.tier);
    
    return (
      <button
        key={companion.companion_id}
        onClick={() => !locked && handleCharacterSelect(companion.companion_id)}
        onKeyDown={(e) => !locked && handleKeyPress(e, companion.companion_id)}
        disabled={locked}
        className={`relative px-6 py-4 rounded-xl text-white font-bold shadow-2xl transform transition-all duration-300 focus:outline-none focus:ring-4 active:scale-95 min-w-[200px] ${
          locked 
            ? 'bg-gradient-to-r from-gray-500 to-gray-700 cursor-not-allowed opacity-60' 
            : `bg-gradient-to-r ${tierColors} hover:scale-105 cursor-pointer`
        }`}
        tabIndex={locked ? -1 : 0}
        role="button"
        aria-label={`Select ${companion.display_name} as your AI companion`}
      >
        {locked && (
          <div className="absolute top-2 right-2">
            🔒
          </div>
        )}
        <div className="text-lg font-bold">{companion.display_name}</div>
        <div className="text-sm opacity-90 mt-1">{companion.description}</div>
        {locked && (
          <div className="text-xs mt-2 text-yellow-300">
            {companion.lock_reason}
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
        {Object.keys(companions).map((tier) => (
          companions[tier].length > 0 && (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all duration-300 ${
                selectedTier === tier
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-700 text-cyan-300 hover:bg-gray-600'
              }`}
            >
              {getTierTitle(tier)} ({companions[tier].length})
            </button>
          )
        ))}
      </div>

      {/* Current User Plan Info */}
      <div className="mb-6 text-center">
        <p className="text-cyan-300 text-sm">
          Current Plan: <span className="font-bold text-cyan-400">{userPlan}</span>
          {trialActive && <span className="text-green-400 ml-2">• Trial Active</span>}
        </p>
      </div>

      {/* Companions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl">
        {companions[selectedTier]?.map(renderCompanion)}
      </div>

      {/* Tier Info */}
      <div className="mt-8 text-cyan-300 text-center text-sm opacity-75 max-w-lg">
        {selectedTier === 'free' && (
          <p>🆓 These companions are available to all users</p>
        )}
        {selectedTier === 'growth' && (
          <p>🌱 Growth tier companions offer enhanced features and capabilities</p>
        )}
        {selectedTier === 'max' && (
          <p>⚡ Max tier companions provide elite features and advanced AI models</p>
        )}
        {selectedTier === 'referral' && (
          <p>🏆 Exclusive companions unlocked through community referrals</p>
        )}
      </div>
    </div>
  );
}
