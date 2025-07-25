import { useCallback, useRef } from 'react';

// Sound utility hook
export const useSound = () => {
  const audioRef = useRef(null);

  const playButtonClick = useCallback(() => {
    try {
      // Create audio element if it doesn't exist
      if (!audioRef.current) {
        audioRef.current = new Audio('/sounds/button-click.mp3');
        audioRef.current.volume = 0.3; // 30% volume
        audioRef.current.preload = 'auto';
      }

      // Reset and play
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(error => {
        // Silently handle audio play errors (user interaction required)
        console.debug('Audio play failed:', error.message);
      });
    } catch (error) {
      console.debug('Sound effect error:', error.message);
    }
  }, []);

  const playSuccessSound = useCallback(() => {
    try {
      // Create a higher pitched success sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      console.debug('Success sound error:', error.message);
    }
  }, []);

  const playErrorSound = useCallback(() => {
    try {
      // Create a lower pitched error sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(300, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.4);
    } catch (error) {
      console.debug('Error sound error:', error.message);
    }
  }, []);

  // Companion Selection Sounds
  const playCompanionSound = useCallback((companionName) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Different sound signatures for each companion
      const companionSounds = {
        'Blayzo': {
          // Wise and calm - Deep, resonant tones
          frequencies: [220, 330, 440],
          durations: [0.3, 0.2, 0.4],
          gains: [0.3, 0.2, 0.25],
          waveType: 'sine'
        },
        'Blayzica': {
          // Energetic and empathetic - Bright, uplifting chimes
          frequencies: [523, 659, 784, 1047],
          durations: [0.2, 0.2, 0.2, 0.3],
          gains: [0.25, 0.25, 0.25, 0.3],
          waveType: 'triangle'
        },
        'Blayzion': {
          // Mystical and cosmic - Ethereal, otherworldly tones
          frequencies: [174, 285, 396, 528, 741],
          durations: [0.4, 0.3, 0.3, 0.3, 0.4],
          gains: [0.2, 0.25, 0.3, 0.25, 0.2],
          waveType: 'sine'
        },
        'Blayzia': {
          // Divine feminine - Warm, healing harmonics
          frequencies: [432, 528, 639, 741],
          durations: [0.4, 0.4, 0.3, 0.5],
          gains: [0.3, 0.35, 0.3, 0.25],
          waveType: 'triangle'
        },
        'Violet': {
          // Mystical and ethereal - Crystal-like, spiritual tones
          frequencies: [852, 963, 1174, 1285],
          durations: [0.3, 0.3, 0.2, 0.4],
          gains: [0.25, 0.3, 0.25, 0.2],
          waveType: 'sine'
        },
        'Crimson': {
          // Fierce and protective - Strong, powerful bass notes
          frequencies: [110, 165, 220, 330],
          durations: [0.4, 0.3, 0.3, 0.4],
          gains: [0.4, 0.35, 0.3, 0.25],
          waveType: 'sawtooth'
        }
      };

      const sound = companionSounds[companionName] || companionSounds['Blayzo'];
      
      // Create and play each tone in sequence
      sound.frequencies.forEach((freq, index) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        const filterNode = audioContext.createBiquadFilter();

        oscillator.connect(filterNode);
        filterNode.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.type = sound.waveType;
        oscillator.frequency.setValueAtTime(freq, audioContext.currentTime + index * 0.1);
        
        // Add subtle filter for more character
        filterNode.type = 'lowpass';
        filterNode.frequency.setValueAtTime(freq * 2, audioContext.currentTime + index * 0.1);
        
        const startTime = audioContext.currentTime + index * 0.1;
        const duration = sound.durations[index];
        
        gainNode.gain.setValueAtTime(0, startTime);
        gainNode.gain.linearRampToValueAtTime(sound.gains[index], startTime + 0.05);
        gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);

        oscillator.start(startTime);
        oscillator.stop(startTime + duration);
      });

      // Add reverb effect for mystical companions
      if (['Blayzion', 'Blayzia', 'Violet'].includes(companionName)) {
        // Create a simple reverb using delay
        const delay = audioContext.createDelay();
        const feedback = audioContext.createGain();
        const delayGain = audioContext.createGain();
        
        delay.delayTime.value = 0.3;
        feedback.gain.value = 0.3;
        delayGain.gain.value = 0.2;
        
        // This would be connected to the main audio chain for reverb effect
      }

    } catch (error) {
      console.debug('Companion sound error:', error.message);
    }
  }, []);

  return {
    playButtonClick,
    playSuccessSound,
    playErrorSound,
    playCompanionSound
  };
};

// Enhanced button component with sound
export const SoundButton = ({ children, onClick, className = '', disabled = false, soundType = 'click', companion = null, ...props }) => {
  const { playButtonClick, playSuccessSound, playErrorSound, playCompanionSound } = useSound();

  const handleClick = useCallback((e) => {
    if (disabled) return;

    // Play sound based on type
    switch (soundType) {
      case 'success':
        playSuccessSound();
        break;
      case 'error':
        playErrorSound();
        break;
      case 'companion':
        if (companion) {
          playCompanionSound(companion);
        } else {
          playButtonClick();
        }
        break;
      default:
        playButtonClick();
        break;
    }

    // Call original onClick
    if (onClick) {
      onClick(e);
    }
  }, [onClick, disabled, soundType, companion, playButtonClick, playSuccessSound, playErrorSound, playCompanionSound]);

  return (
    <button
      {...props}
      className={className}
      onClick={handleClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// Companion Selection Card Component with special sound
export const CompanionCard = ({ companion, onSelect, isSelected = false, className = '' }) => {
  const { playCompanionSound } = useSound();

  const handleCompanionSelect = useCallback(() => {
    // Play companion-specific sound
    playCompanionSound(companion.name);
    
    // Call the selection handler
    if (onSelect) {
      onSelect(companion);
    }
  }, [companion, onSelect, playCompanionSound]);

  const companionEmojis = {
    'Blayzo': '🧘',
    'Blayzica': '✨',
    'Blayzion': '🌌',
    'Blayzia': '💫',
    'Violet': '🔮',
    'Crimson': '⚔️'
  };

  const companionDescriptions = {
    'Blayzo': 'Wise and calm mentor',
    'Blayzica': 'Energetic and empathetic',
    'Blayzion': 'Mystical cosmic sage',
    'Blayzia': 'Divine feminine healer',
    'Violet': 'Ethereal spiritual guide',
    'Crimson': 'Fierce protective warrior'
  };

  return (
    <div 
      className={`companion-card ${isSelected ? 'selected' : ''} ${className}`}
      onClick={handleCompanionSelect}
    >
      <div className="companion-emoji">
        {companionEmojis[companion.name] || '🤖'}
      </div>
      <h3 className="companion-name">{companion.name}</h3>
      <p className="companion-description">
        {companionDescriptions[companion.name] || 'AI Companion'}
      </p>
      <div className="selection-indicator">
        {isSelected && <span>✓ Selected</span>}
      </div>
    </div>
  );
};