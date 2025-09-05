/**
 * Professional Drum Machine UI Component
 * Full-featured interface for the DrumsPro engine
 */

import React, { useState, useEffect, useRef } from 'react';
import { DrumsPro, DrumVoice, SampleKit, DrumStep } from '../audio/drums/DrumsPro';
import './DrumMachinePro.css';

interface DrumMachineProProps {
  className?: string;
}

const DrumMachinePro: React.FC<DrumMachineProProps> = ({ className = '' }) => {
  const drumEngineRef = useRef<DrumsPro | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [currentPattern, setCurrentPattern] = useState<'A' | 'B'>('A');
  const [selectedKit, setSelectedKit] = useState<SampleKit>('808');
  const [tempo, setTempo] = useState(120);
  const [swing, setSwing] = useState(0);
  const [humanize, setHumanize] = useState(0);
  const [selectedVoice, setSelectedVoice] = useState<DrumVoice>('kick');
  const [reverb, setReverb] = useState({ kick: 0.1, snare: 0.3, hat: 0.2 });
  const [sidechain, setSidechain] = useState({ enabled: true, amount: 0.6 });

  // Initialize drum engine
  useEffect(() => {
    drumEngineRef.current = new DrumsPro();
    
    // Set up step update callback
    const updateStep = () => {
      if (drumEngineRef.current) {
        setCurrentStep(drumEngineRef.current.currentStep);
      }
      requestAnimationFrame(updateStep);
    };
    updateStep();

    return () => {
      drumEngineRef.current?.dispose();
    };
  }, []);

  // Update engine settings when UI changes
  useEffect(() => {
    if (!drumEngineRef.current) return;
    
    drumEngineRef.current.settings = {
      ...drumEngineRef.current.settings,
      tempo,
      swing: swing / 100,
      humanize: humanize / 100,
      kit: selectedKit,
      reverb: {
        kick: reverb.kick,
        snare: reverb.snare,
        hat: reverb.hat
      },
      sidechain: {
        enabled: sidechain.enabled,
        amount: sidechain.amount
      }
    };

    if (drumEngineRef.current.isPlaying) {
      drumEngineRef.current.updateKit(selectedKit);
    }
  }, [tempo, swing, humanize, selectedKit, reverb, sidechain]);

  const handlePlay = async () => {
    if (!drumEngineRef.current) return;
    
    if (isPlaying) {
      drumEngineRef.current.stop();
      setIsPlaying(false);
    } else {
      await drumEngineRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleStepClick = (voice: DrumVoice, step: number) => {
    if (!drumEngineRef.current) return;
    
    const currentPattern = drumEngineRef.current.patterns[drumEngineRef.current.currentPattern];
    const stepData = currentPattern[voice][step];
    
    drumEngineRef.current.setStep(voice, step, {
      active: !stepData.active
    });
  };

  const handleStepRightClick = (voice: DrumVoice, step: number, e: React.MouseEvent) => {
    e.preventDefault();
    if (!drumEngineRef.current) return;
    
    const currentPattern = drumEngineRef.current.patterns[drumEngineRef.current.currentPattern];
    const stepData = currentPattern[voice][step];
    
    // Cycle through velocity levels on right click
    const velocities = [0.3, 0.5, 0.8, 1.0];
    const currentIndex = velocities.findIndex(v => Math.abs(v - stepData.velocity) < 0.1);
    const nextIndex = (currentIndex + 1) % velocities.length;
    
    drumEngineRef.current.setStep(voice, step, {
      velocity: velocities[nextIndex]
    });
  };

  const handlePatternSwitch = (pattern: 'A' | 'B') => {
    if (!drumEngineRef.current) return;
    
    drumEngineRef.current.currentPattern = pattern;
    setCurrentPattern(pattern);
  };

  const handleClearPattern = () => {
    if (!drumEngineRef.current) return;
    drumEngineRef.current.clearPattern();
  };

  const handleRandomize = (voice?: DrumVoice) => {
    if (!drumEngineRef.current) return;
    drumEngineRef.current.randomizePattern(voice);
  };

  const handleTapTempo = () => {
    if (!drumEngineRef.current) return;
    drumEngineRef.current.tapTempo();
    setTempo(drumEngineRef.current.settings.tempo);
  };

  const handleExportWAV = async () => {
    if (!drumEngineRef.current) return;
    
    try {
      const wavBlob = await drumEngineRef.current.exportWAV();
      const url = URL.createObjectURL(wavBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `drum-pattern-${currentPattern}.wav`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('WAV export failed:', error);
    }
  };

  const handleExportMIDI = () => {
    if (!drumEngineRef.current) return;
    
    try {
      const midiData = drumEngineRef.current.exportMIDI();
      const blob = new Blob([atob(midiData)], { type: 'audio/midi' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `drum-pattern-${currentPattern}.mid`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('MIDI export failed:', error);
    }
  };

  const getStepClass = (voice: DrumVoice, step: number) => {
    if (!drumEngineRef.current) return 'step';
    
    const pattern = drumEngineRef.current.patterns[drumEngineRef.current.currentPattern];
    const stepData = pattern[voice][step];
    const isActive = stepData.active;
    const isCurrent = step === currentStep && isPlaying;
    const velocity = stepData.velocity;
    
    let className = 'step';
    if (isActive) className += ' active';
    if (isCurrent) className += ' current';
    if (velocity > 0.8) className += ' velocity-high';
    else if (velocity > 0.5) className += ' velocity-medium';
    else className += ' velocity-low';
    
    return className;
  };

  return (
    <div className={`drum-machine-pro ${className}`}>
      {/* Header */}
      <div className="dm-header">
        <h2>🥁 Professional Drum Machine</h2>
        <div className="pattern-selector">
          <button 
            className={`pattern-btn ${currentPattern === 'A' ? 'active' : ''}`}
            onClick={() => handlePatternSwitch('A')}
          >
            A
          </button>
          <button 
            className={`pattern-btn ${currentPattern === 'B' ? 'active' : ''}`}
            onClick={() => handlePatternSwitch('B')}
          >
            B
          </button>
        </div>
      </div>

      {/* Transport Controls */}
      <div className="transport-controls">
        <button className={`play-btn ${isPlaying ? 'playing' : ''}`} onClick={handlePlay}>
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <div className="tempo-section">
          <label>Tempo</label>
          <input 
            type="range" 
            min="60" 
            max="200" 
            value={tempo} 
            onChange={(e) => setTempo(parseInt(e.target.value))}
          />
          <span className="tempo-display">{tempo}</span>
          <button className="tap-tempo-btn" onClick={handleTapTempo}>TAP</button>
        </div>

        <div className="kit-selector">
          <label>Kit</label>
          <select value={selectedKit} onChange={(e) => setSelectedKit(e.target.value as SampleKit)}>
            <option value="CR78">CR-78</option>
            <option value="808">TR-808</option>
            <option value="909">TR-909</option>
            <option value="Synth">Synth</option>
          </select>
        </div>
      </div>

      {/* Step Grid */}
      <div className="step-grid">
        {(['kick', 'snare', 'hat'] as DrumVoice[]).map(voice => (
          <div key={voice} className="voice-row">
            <div className="voice-label">
              <span className={`voice-name ${selectedVoice === voice ? 'selected' : ''}`}
                    onClick={() => setSelectedVoice(voice)}>
                {voice.toUpperCase()}
              </span>
              <button className="randomize-voice-btn" 
                      onClick={() => handleRandomize(voice)}
                      title={`Randomize ${voice}`}>
                🎲
              </button>
            </div>
            
            <div className="steps-container">
              {Array.from({ length: 16 }, (_, i) => (
                <button
                  key={i}
                  className={getStepClass(voice, i)}
                  onClick={() => handleStepClick(voice, i)}
                  onContextMenu={(e) => handleStepRightClick(voice, i, e)}
                  title={`Step ${i + 1} - Left click: toggle, Right click: velocity`}
                >
                  <span className="step-number">{i + 1}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Step Numbers */}
      <div className="step-numbers">
        {Array.from({ length: 16 }, (_, i) => (
          <div key={i} className={`step-number-label ${i === currentStep && isPlaying ? 'current' : ''}`}>
            {i + 1}
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="controls-section">
        {/* Groove Controls */}
        <div className="groove-controls">
          <h4>Groove</h4>
          <div className="control-group">
            <label>Swing</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={swing} 
              onChange={(e) => setSwing(parseInt(e.target.value))}
            />
            <span>{swing}%</span>
          </div>
          
          <div className="control-group">
            <label>Humanize</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={humanize} 
              onChange={(e) => setHumanize(parseInt(e.target.value))}
            />
            <span>{humanize}%</span>
          </div>
        </div>

        {/* Reverb Controls */}
        <div className="reverb-controls">
          <h4>Reverb Sends</h4>
          {(['kick', 'snare', 'hat'] as DrumVoice[]).map(voice => (
            <div key={voice} className="control-group">
              <label>{voice.toUpperCase()}</label>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={Math.round(reverb[voice] * 100)} 
                onChange={(e) => setReverb(prev => ({
                  ...prev,
                  [voice]: parseInt(e.target.value) / 100
                }))}
              />
              <span>{Math.round(reverb[voice] * 100)}%</span>
            </div>
          ))}
        </div>

        {/* Sidechain Controls */}
        <div className="sidechain-controls">
          <h4>Sidechain</h4>
          <div className="control-group">
            <label>
              <input 
                type="checkbox" 
                checked={sidechain.enabled}
                onChange={(e) => setSidechain(prev => ({
                  ...prev,
                  enabled: e.target.checked
                }))}
              />
              Enable
            </label>
          </div>
          
          <div className="control-group">
            <label>Amount</label>
            <input 
              type="range" 
              min="0" 
              max="100" 
              value={Math.round(sidechain.amount * 100)} 
              onChange={(e) => setSidechain(prev => ({
                ...prev,
                amount: parseInt(e.target.value) / 100
              }))}
              disabled={!sidechain.enabled}
            />
            <span>{Math.round(sidechain.amount * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button onClick={handleClearPattern} className="action-btn clear-btn">
          🗑️ Clear Pattern
        </button>
        <button onClick={() => handleRandomize()} className="action-btn randomize-btn">
          🎲 Randomize All
        </button>
        <button onClick={handleExportWAV} className="action-btn export-btn">
          💾 Export WAV
        </button>
        <button onClick={handleExportMIDI} className="action-btn export-btn">
          🎵 Export MIDI
        </button>
      </div>
    </div>
  );
};

export default DrumMachinePro;