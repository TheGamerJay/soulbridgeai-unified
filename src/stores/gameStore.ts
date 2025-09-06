import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Game state types
export type GameDifficulty = 'easy' | 'medium' | 'hard';
export type GameMode = 'classic' | 'timed' | 'endless';

export interface Riddle {
  id: string;
  question: string;
  answer: string;
  difficulty: GameDifficulty;
  category: string;
  hint?: string;
}

export interface GameStats {
  totalPlayed: number;
  totalCorrect: number;
  totalWrong: number;
  streak: number;
  bestStreak: number;
  averageTime: number;
  difficultyStats: Record<GameDifficulty, {
    played: number;
    correct: number;
    bestTime: number;
  }>;
}

export interface GameSession {
  mode: GameMode;
  difficulty: GameDifficulty;
  startTime: number;
  endTime?: number;
  currentRiddle: Riddle | null;
  riddleIndex: number;
  score: number;
  lives: number;
  timeRemaining?: number;
  isGameOver: boolean;
  isPaused: boolean;
  hintsUsed: number;
  riddlesAnswered: Riddle[];
}

export interface UserState {
  credits: number;
  plan: 'bronze' | 'silver' | 'gold';
  trial: {
    active: boolean;
    timeRemaining: number;
    creditsRemaining: number;
  };
}

interface GameStore {
  // User state
  user: UserState;
  
  // Game session
  session: GameSession | null;
  
  // Game stats (persistent)
  stats: GameStats;
  
  // Settings (persistent)
  settings: {
    soundEnabled: boolean;
    difficulty: GameDifficulty;
    preferredMode: GameMode;
    autoAdvance: boolean;
  };
  
  // Actions
  setUser: (user: Partial<UserState>) => void;
  startGame: (mode: GameMode, difficulty: GameDifficulty) => void;
  endGame: () => void;
  pauseGame: () => void;
  resumeGame: () => void;
  answerRiddle: (answer: string, timeSpent: number) => boolean;
  useHint: () => boolean;
  nextRiddle: () => void;
  updateStats: (correct: boolean, timeSpent: number, difficulty: GameDifficulty) => void;
  resetStats: () => void;
  updateSettings: (settings: Partial<GameStore['settings']>) => void;
}

const initialStats: GameStats = {
  totalPlayed: 0,
  totalCorrect: 0,
  totalWrong: 0,
  streak: 0,
  bestStreak: 0,
  averageTime: 0,
  difficultyStats: {
    easy: { played: 0, correct: 0, bestTime: Infinity },
    medium: { played: 0, correct: 0, bestTime: Infinity },
    hard: { played: 0, correct: 0, bestTime: Infinity },
  },
};

const initialSettings = {
  soundEnabled: true,
  difficulty: 'medium' as GameDifficulty,
  preferredMode: 'classic' as GameMode,
  autoAdvance: true,
};

// Sample riddles - in a real app, these would come from an API
const sampleRiddles: Riddle[] = [
  {
    id: '1',
    question: 'What has keys but no locks, space but no room, and you can enter but not go inside?',
    answer: 'keyboard',
    difficulty: 'easy',
    category: 'Technology',
    hint: 'You use it to type'
  },
  {
    id: '2', 
    question: 'I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?',
    answer: 'echo',
    difficulty: 'medium',
    category: 'Nature',
    hint: 'Sound that returns to you'
  },
  {
    id: '3',
    question: 'The more you take, the more you leave behind. What am I?',
    answer: 'footsteps',
    difficulty: 'easy',
    category: 'Movement',
    hint: 'You make them when walking'
  },
  {
    id: '4',
    question: 'What can travel around the world while staying in a corner?',
    answer: 'stamp',
    difficulty: 'medium',
    category: 'Objects',
    hint: 'Found on letters'
  },
  {
    id: '5',
    question: 'I am not alive, but I grow; I don\'t have lungs, but I need air; I don\'t have a mouth, but water kills me.',
    answer: 'fire',
    difficulty: 'hard',
    category: 'Elements',
    hint: 'Hot and bright'
  }
];

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      user: {
        credits: 100,
        plan: 'bronze',
        trial: {
          active: false,
          timeRemaining: 0,
          creditsRemaining: 0,
        },
      },
      
      session: null,
      stats: initialStats,
      settings: initialSettings,
      
      setUser: (user) => set((state) => ({
        user: { ...state.user, ...user }
      })),
      
      startGame: (mode, difficulty) => {
        const newSession: GameSession = {
          mode,
          difficulty,
          startTime: Date.now(),
          currentRiddle: null,
          riddleIndex: 0,
          score: 0,
          lives: mode === 'classic' ? 3 : mode === 'timed' ? 1 : Infinity,
          timeRemaining: mode === 'timed' ? 300 : undefined, // 5 minutes for timed mode
          isGameOver: false,
          isPaused: false,
          hintsUsed: 0,
          riddlesAnswered: [],
        };
        
        set({ session: newSession });
        
        // Load first riddle
        get().nextRiddle();
      },
      
      endGame: () => set((state) => {
        if (state.session) {
          return {
            session: {
              ...state.session,
              endTime: Date.now(),
              isGameOver: true,
            }
          };
        }
        return state;
      }),
      
      pauseGame: () => set((state) => ({
        session: state.session ? { ...state.session, isPaused: true } : null
      })),
      
      resumeGame: () => set((state) => ({
        session: state.session ? { ...state.session, isPaused: false } : null
      })),
      
      answerRiddle: (answer, timeSpent) => {
        const state = get();
        const session = state.session;
        
        if (!session || !session.currentRiddle) return false;
        
        const isCorrect = answer.toLowerCase().trim() === session.currentRiddle.answer.toLowerCase();
        
        // Update session
        set({
          session: {
            ...session,
            score: isCorrect ? session.score + (session.currentRiddle.difficulty === 'easy' ? 10 : session.currentRiddle.difficulty === 'medium' ? 20 : 30) : session.score,
            lives: !isCorrect && session.mode !== 'endless' ? Math.max(0, session.lives - 1) : session.lives,
            riddlesAnswered: [...session.riddlesAnswered, session.currentRiddle],
          }
        });
        
        // Update stats
        state.updateStats(isCorrect, timeSpent, session.currentRiddle.difficulty);
        
        // Check game over
        if (!isCorrect && session.lives <= 1 && session.mode !== 'endless') {
          state.endGame();
        }
        
        return isCorrect;
      },
      
      useHint: () => {
        const state = get();
        const session = state.session;
        
        if (!session || state.user.credits < 5) return false;
        
        set((prevState) => ({
          user: { ...prevState.user, credits: prevState.user.credits - 5 },
          session: session ? { ...session, hintsUsed: session.hintsUsed + 1 } : null
        }));
        
        return true;
      },
      
      nextRiddle: () => {
        const state = get();
        const session = state.session;
        
        if (!session) return;
        
        // Filter riddles by difficulty
        const availableRiddles = sampleRiddles.filter(r => r.difficulty === session.difficulty);
        
        if (availableRiddles.length === 0) {
          state.endGame();
          return;
        }
        
        // Get next riddle (cycling through available riddles)
        const nextRiddle = availableRiddles[session.riddleIndex % availableRiddles.length];
        
        set({
          session: {
            ...session,
            currentRiddle: nextRiddle,
            riddleIndex: session.riddleIndex + 1,
          }
        });
      },
      
      updateStats: (correct, timeSpent, difficulty) => set((state) => {
        const stats = state.stats;
        const diffStat = stats.difficultyStats[difficulty];
        
        const newStats: GameStats = {
          totalPlayed: stats.totalPlayed + 1,
          totalCorrect: correct ? stats.totalCorrect + 1 : stats.totalCorrect,
          totalWrong: correct ? stats.totalWrong : stats.totalWrong + 1,
          streak: correct ? stats.streak + 1 : 0,
          bestStreak: correct ? Math.max(stats.bestStreak, stats.streak + 1) : stats.bestStreak,
          averageTime: ((stats.averageTime * stats.totalPlayed) + timeSpent) / (stats.totalPlayed + 1),
          difficultyStats: {
            ...stats.difficultyStats,
            [difficulty]: {
              played: diffStat.played + 1,
              correct: correct ? diffStat.correct + 1 : diffStat.correct,
              bestTime: correct ? Math.min(diffStat.bestTime, timeSpent) : diffStat.bestTime,
            }
          }
        };
        
        return { stats: newStats };
      }),
      
      resetStats: () => set({ stats: initialStats }),
      
      updateSettings: (newSettings) => set((state) => ({
        settings: { ...state.settings, ...newSettings }
      })),
    }),
    {
      name: 'soulridge-game-store',
      partialize: (state) => ({
        stats: state.stats,
        settings: state.settings,
        user: state.user,
      }),
    }
  )
);