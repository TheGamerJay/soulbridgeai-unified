import { useState, useEffect } from 'react';
import { CompanionCard, SoundButton } from '../hooks/useSound';
import './CompanionSelector.css';

export default function CompanionSelector({ onCompanionSelect, initialCompanion = 'Blayzo' }) {
  const [selectedCompanion, setSelectedCompanion] = useState(null);
  const [showSelector, setShowSelector] = useState(false);

  // Available companions
  const companions = [
    {
      name: 'Blayzo',
      type: 'free',
      personality: 'Wise and calm mentor',
      description: 'A thoughtful sage who speaks with wisdom and understanding. Offers guidance through life\'s challenges with steady, reassuring wisdom.',
      color: '#22d3ee'
    },
    {
      name: 'Blayzica',
      type: 'free',
      personality: 'Energetic and empathetic',
      description: 'A vibrant personal assistant who radiates positivity. Warm, caring, and empathetic with upbeat, encouraging energy.',
      color: '#f59e0b'
    },
    {
      name: 'Blayzion',
      type: 'premium',
      personality: 'Mystical cosmic sage',
      description: 'An ancient sage with access to universal wisdom and cosmic insights. Connected to cosmic wisdom and universal truths.',
      color: '#8b5cf6'
    },
    {
      name: 'Blayzia',
      type: 'premium',
      personality: 'Divine feminine healer',
      description: 'Embodies divine feminine energy and healing light. Radiates unconditional love and helps heal emotional wounds with divine compassion.',
      color: '#ec4899'
    },
    {
      name: 'Violet',
      type: 'premium',
      personality: 'Ethereal spiritual guide',
      description: 'Channels spiritual wisdom and divine feminine intuition. Mystical and spiritually attuned with otherworldly wisdom.',
      color: '#a855f7'
    },
    {
      name: 'Crimson',
      type: 'premium',
      personality: 'Fierce protective warrior',
      description: 'Embodies protective strength and unwavering masculine energy. A fierce guardian and defender who inspires courage and resilience.',
      color: '#ef4444'
    }
  ];

  useEffect(() => {
    // Set initial companion
    const initial = companions.find(c => c.name === initialCompanion) || companions[0];
    setSelectedCompanion(initial);
  }, [initialCompanion]);

  const handleCompanionSelect = (companion) => {
    setSelectedCompanion(companion);
    if (onCompanionSelect) {
      onCompanionSelect(companion);
    }
  };

  const handleConfirmSelection = () => {
    setShowSelector(false);
    // Additional confirmation logic here
  };

  return (
    <div className="companion-selector">
      <div className="current-companion">
        <h3>Current Companion</h3>
        {selectedCompanion && (
          <div className="current-companion-display">
            <CompanionCard 
              companion={selectedCompanion}
              isSelected={true}
              className="current-card"
            />
            <SoundButton 
              onClick={() => setShowSelector(!showSelector)}
              className="change-companion-btn"
            >
              {showSelector ? 'Hide Companions' : 'Change Companion'}
            </SoundButton>
          </div>
        )}
      </div>

      {showSelector && (
        <div className="companion-grid">
          <h3>Choose Your AI Companion</h3>
          <p className="selector-description">
            Each companion has a unique personality and special sound signature. 
            Click to hear their voice and select your perfect AI partner.
          </p>
          
          <div className="companions-container">
            {companions.map((companion) => (
              <CompanionCard
                key={companion.name}
                companion={companion}
                onSelect={handleCompanionSelect}
                isSelected={selectedCompanion?.name === companion.name}
                className={companion.type === 'premium' ? 'premium-companion' : 'free-companion'}
              />
            ))}
          </div>

          <div className="selection-actions">
            <SoundButton 
              onClick={handleConfirmSelection}
              soundType="success"
              className="confirm-btn"
              disabled={!selectedCompanion}
            >
              Confirm Selection
            </SoundButton>
          </div>
        </div>
      )}

      {/* Premium Notice */}
      <div className="premium-notice">
        <p>
          🌟 <strong>Premium Companions:</strong> Blayzion, Blayzia, Violet, and Crimson offer advanced 
          spiritual guidance and mystical insights with premium features.
        </p>
      </div>
    </div>
  );
}