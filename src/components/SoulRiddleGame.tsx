import React, { useState, useEffect, useCallback } from 'react';
import { useGameStore, GameMode, GameDifficulty } from '../stores/gameStore';
import './SoulRiddleGame.css';

interface SoulRiddleGameProps {
  onClose?: () => void;
}

const SoulRiddleGame: React.FC<SoulRiddleGameProps> = ({ onClose }) => {
  const {
    user,
    session,
    stats,
    settings,
    startGame,
    endGame,
    pauseGame,
    resumeGame,
    answerRiddle,
    useHint,
    nextRiddle,
    updateSettings,
  } = useGameStore();

  const [userAnswer, setUserAnswer] = useState('');
  const [showHint, setShowHint] = useState(false);
  const [riddleStartTime, setRiddleStartTime] = useState<number>(Date.now());
  const [gameMode, setGameMode] = useState<GameMode>('classic');
  const [gameDifficulty, setGameDifficulty] = useState<GameDifficulty>('medium');
  const [showStats, setShowStats] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Timer for current riddle
  const [currentTime, setCurrentTime] = useState<number>(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (session && !session.isPaused && !session.isGameOver) {
      interval = setInterval(() => {
        setCurrentTime(Date.now() - riddleStartTime);
        
        // Update time remaining for timed mode
        if (session.timeRemaining !== undefined) {
          const elapsed = Math.floor((Date.now() - session.startTime) / 1000);
          const remaining = Math.max(0, 300 - elapsed); // 5 minutes
          
          if (remaining <= 0) {
            endGame();
          }
        }
      }, 100);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [session, riddleStartTime, endGame]);

  // Reset riddle timer when new riddle loads
  useEffect(() => {
    if (session?.currentRiddle) {
      setRiddleStartTime(Date.now());
      setCurrentTime(0);
      setUserAnswer('');
      setShowHint(false);
    }
  }, [session?.currentRiddle]);

  const handleStartGame = () => {
    startGame(gameMode, gameDifficulty);
  };

  const handleSubmitAnswer = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    if (!session || !userAnswer.trim()) return;
    
    const timeSpent = Math.floor(currentTime / 1000);
    const isCorrect = answerRiddle(userAnswer, timeSpent);
    
    // Show feedback briefly, then advance
    setTimeout(() => {
      if (!session.isGameOver) {
        nextRiddle();
      }
    }, 1500);
  }, [session, userAnswer, currentTime, answerRiddle, nextRiddle]);

  const handleUseHint = () => {
    if (useHint()) {
      setShowHint(true);
    }
  };

  const formatTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${remainingSeconds}s`;
  };

  const getDifficultyColor = (difficulty: GameDifficulty): string => {
    switch (difficulty) {
      case 'easy': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'hard': return '#EF4444';
      default: return '#6B7280';
    }
  };

  // Game not started - Show menu
  if (!session) {
    return (
      <div className="soul-riddle-game">
        <div className="game-header">
          <div className="game-title">
            <h1>🧩 Soul Riddle</h1>
            <p>Test your wits with mystical brain teasers</p>
          </div>
          {onClose && (
            <button className="close-btn" onClick={onClose}>
              ✕
            </button>
          )}
        </div>

        <div className="game-menu">
          <div className="user-info">
            <div className="credits-display">
              <span className="credits-icon">💎</span>
              <span className="credits-amount">{user.credits}</span>
              <span className="credits-label">Credits</span>
            </div>
            <div className="plan-badge plan-${user.plan}">{user.plan.toUpperCase()}</div>
          </div>

          <div className="game-modes">
            <h3>Choose Game Mode</h3>
            <div className="mode-selector">
              {(['classic', 'timed', 'endless'] as GameMode[]).map((mode) => (
                <button
                  key={mode}
                  className={`mode-btn ${gameMode === mode ? 'selected' : ''}`}
                  onClick={() => setGameMode(mode)}
                >
                  <div className="mode-icon">
                    {mode === 'classic' ? '🎯' : mode === 'timed' ? '⏰' : '∞'}
                  </div>
                  <div className="mode-info">
                    <div className="mode-name">{mode.charAt(0).toUpperCase() + mode.slice(1)}</div>
                    <div className="mode-desc">
                      {mode === 'classic' && '3 lives, increasing difficulty'}
                      {mode === 'timed' && '5 minutes, score as many as possible'}
                      {mode === 'endless' && 'No limits, pure brain training'}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="difficulty-selector">
            <h3>Difficulty Level</h3>
            <div className="difficulty-buttons">
              {(['easy', 'medium', 'hard'] as GameDifficulty[]).map((difficulty) => (
                <button
                  key={difficulty}
                  className={`difficulty-btn ${gameDifficulty === difficulty ? 'selected' : ''}`}
                  style={{ borderColor: getDifficultyColor(difficulty) }}
                  onClick={() => setGameDifficulty(difficulty)}
                >
                  <span 
                    className="difficulty-dot" 
                    style={{ backgroundColor: getDifficultyColor(difficulty) }}
                  />
                  {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="menu-actions">
            <button className="start-btn" onClick={handleStartGame}>
              🚀 Start Game
            </button>
            
            <div className="menu-buttons">
              <button className="menu-btn" onClick={() => setShowStats(true)}>
                📊 Stats
              </button>
              <button className="menu-btn" onClick={() => setShowSettings(true)}>
                ⚙️ Settings
              </button>
            </div>
          </div>
        </div>

        {/* Stats Modal */}
        {showStats && (
          <div className="modal-overlay" onClick={() => setShowStats(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>📊 Your Stats</h3>
                <button onClick={() => setShowStats(false)}>✕</button>
              </div>
              <div className="stats-content">
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-value">{stats.totalPlayed}</div>
                    <div className="stat-label">Total Played</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{stats.totalCorrect}</div>
                    <div className="stat-label">Correct</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{Math.round((stats.totalCorrect / Math.max(stats.totalPlayed, 1)) * 100)}%</div>
                    <div className="stat-label">Accuracy</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{stats.bestStreak}</div>
                    <div className="stat-label">Best Streak</div>
                  </div>
                </div>
                
                <div className="difficulty-stats">
                  <h4>By Difficulty</h4>
                  {Object.entries(stats.difficultyStats).map(([diff, stat]) => (
                    <div key={diff} className="difficulty-stat">
                      <span className="diff-name">{diff.charAt(0).toUpperCase() + diff.slice(1)}</span>
                      <span className="diff-played">{stat.played} played</span>
                      <span className="diff-accuracy">
                        {stat.played > 0 ? Math.round((stat.correct / stat.played) * 100) : 0}% accuracy
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings Modal */}
        {showSettings && (
          <div className="modal-overlay" onClick={() => setShowSettings(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>⚙️ Settings</h3>
                <button onClick={() => setShowSettings(false)}>✕</button>
              </div>
              <div className="settings-content">
                <div className="setting-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={settings.soundEnabled}
                      onChange={(e) => updateSettings({ soundEnabled: e.target.checked })}
                    />
                    Sound Effects
                  </label>
                </div>
                <div className="setting-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={settings.autoAdvance}
                      onChange={(e) => updateSettings({ autoAdvance: e.target.checked })}
                    />
                    Auto-advance after correct answer
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Game in progress
  return (
    <div className="soul-riddle-game playing">
      <div className="game-header">
        <div className="game-info">
          <div className="game-mode-display">
            <span className="mode-icon">
              {session.mode === 'classic' ? '🎯' : session.mode === 'timed' ? '⏰' : '∞'}
            </span>
            <span className="mode-name">{session.mode.toUpperCase()}</span>
          </div>
          
          <div className="game-stats">
            <div className="stat">
              <span className="stat-label">Score</span>
              <span className="stat-value">{session.score}</span>
            </div>
            
            {session.mode !== 'endless' && (
              <div className="stat">
                <span className="stat-label">Lives</span>
                <span className="stat-value">{'❤️'.repeat(session.lives)}</span>
              </div>
            )}
            
            {session.timeRemaining !== undefined && (
              <div className="stat">
                <span className="stat-label">Time</span>
                <span className="stat-value">{formatTime((session.timeRemaining || 0) * 1000)}</span>
              </div>
            )}
          </div>
        </div>

        <div className="game-controls">
          <button 
            className="control-btn"
            onClick={session.isPaused ? resumeGame : pauseGame}
          >
            {session.isPaused ? '▶️' : '⏸️'}
          </button>
          <button className="control-btn" onClick={endGame}>
            🛑
          </button>
          {onClose && (
            <button className="close-btn" onClick={onClose}>
              ✕
            </button>
          )}
        </div>
      </div>

      {session.isPaused ? (
        <div className="pause-screen">
          <div className="pause-content">
            <h2>⏸️ Game Paused</h2>
            <button className="resume-btn" onClick={resumeGame}>
              ▶️ Resume Game
            </button>
          </div>
        </div>
      ) : session.isGameOver ? (
        <div className="game-over-screen">
          <div className="game-over-content">
            <h2>🎯 Game Over!</h2>
            <div className="final-stats">
              <div className="final-stat">
                <span className="final-label">Final Score</span>
                <span className="final-value">{session.score}</span>
              </div>
              <div className="final-stat">
                <span className="final-label">Riddles Answered</span>
                <span className="final-value">{session.riddlesAnswered.length}</span>
              </div>
              <div className="final-stat">
                <span className="final-label">Hints Used</span>
                <span className="final-value">{session.hintsUsed}</span>
              </div>
            </div>
            <div className="game-over-actions">
              <button className="play-again-btn" onClick={() => { endGame(); startGame(session.mode, session.difficulty); }}>
                🔄 Play Again
              </button>
              <button className="menu-btn" onClick={endGame}>
                📋 Main Menu
              </button>
            </div>
          </div>
        </div>
      ) : session.currentRiddle ? (
        <div className="riddle-screen">
          <div className="riddle-header">
            <div className="riddle-meta">
              <span className="riddle-category">{session.currentRiddle.category}</span>
              <span 
                className="riddle-difficulty"
                style={{ color: getDifficultyColor(session.currentRiddle.difficulty) }}
              >
                {session.currentRiddle.difficulty.toUpperCase()}
              </span>
            </div>
            <div className="riddle-timer">
              <span className="timer-label">Time:</span>
              <span className="timer-value">{formatTime(currentTime)}</span>
            </div>
          </div>

          <div className="riddle-content">
            <div className="riddle-question">
              <h3>{session.currentRiddle.question}</h3>
            </div>

            {showHint && session.currentRiddle.hint && (
              <div className="riddle-hint">
                <div className="hint-icon">💡</div>
                <div className="hint-text">{session.currentRiddle.hint}</div>
              </div>
            )}

            <form className="answer-form" onSubmit={handleSubmitAnswer}>
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Type your answer here..."
                className="answer-input"
                autoFocus
              />
              <div className="form-actions">
                <button type="submit" className="submit-btn" disabled={!userAnswer.trim()}>
                  Submit Answer
                </button>
                {session.currentRiddle.hint && !showHint && (
                  <button 
                    type="button" 
                    className="hint-btn"
                    onClick={handleUseHint}
                    disabled={user.credits < 5}
                  >
                    💡 Hint (5 💎)
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      ) : (
        <div className="loading-screen">
          <div className="loading-content">
            <div className="loading-spinner">🧩</div>
            <p>Loading next riddle...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SoulRiddleGame;