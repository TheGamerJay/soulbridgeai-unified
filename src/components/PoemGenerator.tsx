import React, { useState, useEffect } from 'react';
import './PoemGenerator.css';

interface PoemType {
  type: string;
  name: string;
  lines: number | string;
  syllable_pattern: number[] | null;
  rhyme_scheme: string | null;
  description: string;
  difficulty: string;
  special_rules: string[];
}

interface Poem {
  title: string;
  content: string;
  structure: string;
  syllable_counts: number[];
  validation: {
    is_valid: boolean;
    issues: string[];
    score: number;
  };
}

interface UserStats {
  user_plan: string;
  daily_limit: number;
  current_usage: number;
  remaining_usage: number;
  features: {
    all_poem_types: boolean;
    validation: boolean;
    structure_analysis: boolean;
    syllable_counting: boolean;
    rhyme_analysis: boolean;
    unlimited_generation: boolean;
  };
  available_types: string[];
}

export const PoemGenerator: React.FC = () => {
  const [poemTypes, setPoemTypes] = useState<PoemType[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [selectedType, setSelectedType] = useState<string>('');
  const [theme, setTheme] = useState<string>('');
  const [mood, setMood] = useState<string>('neutral');
  const [language, setLanguage] = useState<string>('en');
  const [customWord, setCustomWord] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedPoem, setGeneratedPoem] = useState<Poem | null>(null);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'generate' | 'analyze'>('generate');
  const [analyzeText, setAnalyzeText] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  useEffect(() => {
    loadPoemTypes();
    loadUserStats();
  }, []);

  const loadPoemTypes = async () => {
    try {
      const response = await fetch('/api/poems/types');
      const data = await response.json();
      
      if (data.success) {
        setPoemTypes(data.poem_types);
        if (data.poem_types.length > 0) {
          setSelectedType(data.poem_types[0].type);
        }
      }
    } catch (error) {
      console.error('Error loading poem types:', error);
    }
  };

  const loadUserStats = async () => {
    try {
      const response = await fetch('/api/poems/stats');
      const data = await response.json();
      
      if (data.success) {
        setUserStats(data.stats);
      }
    } catch (error) {
      console.error('Error loading user stats:', error);
    }
  };

  const generatePoem = async () => {
    if (!theme.trim()) {
      setError('Please enter a theme for your poem');
      return;
    }

    if (selectedType === 'acrostic' && !customWord.trim()) {
      setError('Please enter a word for your acrostic poem');
      return;
    }

    setIsGenerating(true);
    setError('');
    setGeneratedPoem(null);

    try {
      const requestData = {
        poem_type: selectedType,
        theme: theme,
        mood: mood,
        language: language,
        ...(selectedType === 'acrostic' && { custom_word: customWord })
      };

      const response = await fetch('/api/poems/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedPoem({
          title: `${selectedType.replace('_', ' ').toUpperCase()} - ${theme}`,
          content: data.poem.content,
          structure: data.poem.structure,
          syllable_counts: data.poem.syllable_counts || [],
          validation: data.validation
        });
        
        // Refresh stats
        loadUserStats();
      } else {
        setError(data.error || 'Failed to generate poem');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error generating poem:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzePoem = async () => {
    if (!analyzeText.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setIsGenerating(true);
    setError('');
    setAnalysisResult(null);

    try {
      const response = await fetch('/api/poems/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: analyzeText
        })
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResult(data.analysis);
      } else {
        setError(data.error || 'Failed to analyze poem');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error analyzing poem:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const validatePoem = async () => {
    if (!analyzeText.trim() || !selectedType) {
      setError('Please enter text and select a poem type');
      return;
    }

    setIsGenerating(true);
    setError('');

    try {
      const response = await fetch('/api/poems/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          poem_type: selectedType,
          content: analyzeText
        })
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResult({
          ...analysisResult,
          validation: data.validation,
          poem_type: data.poem_type
        });
      } else {
        setError(data.error || 'Failed to validate poem');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error validating poem:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      // You could show a toast notification here
      console.log('Copied to clipboard');
    });
  };

  const selectedPoemType = poemTypes.find(type => type.type === selectedType);

  return (
    <div className="poem-generator">
      <div className="poem-header">
        <h2>🎭 Poem Generator</h2>
        <p>Create beautiful poetry with AI assistance</p>
        
        {userStats && (
          <div className="usage-info">
            <span className="plan-badge">{userStats.user_plan.toUpperCase()}</span>
            {userStats.daily_limit === -1 ? (
              <span>Unlimited ({userStats.current_usage} used today)</span>
            ) : (
              <span>{userStats.remaining_usage}/{userStats.daily_limit} remaining</span>
            )}
          </div>
        )}
      </div>

      <div className="poem-tabs">
        <button
          className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          Generate Poem
        </button>
        <button
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Analyze Poem
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {activeTab === 'generate' && (
        <div className="generate-tab">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="poem-type">Poem Type</label>
              <select
                id="poem-type"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
              >
                {poemTypes.map(type => (
                  <option key={type.type} value={type.type}>
                    {type.name} ({type.difficulty})
                  </option>
                ))}
              </select>
              {selectedPoemType && (
                <div className="type-info">
                  <p>{selectedPoemType.description}</p>
                  <div className="type-details">
                    <span>Lines: {selectedPoemType.lines}</span>
                    {selectedPoemType.syllable_pattern && (
                      <span>Pattern: {selectedPoemType.syllable_pattern.join('-')}</span>
                    )}
                    {selectedPoemType.rhyme_scheme && (
                      <span>Rhyme: {selectedPoemType.rhyme_scheme}</span>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="theme">Theme *</label>
                <input
                  id="theme"
                  type="text"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  placeholder="Enter your poem's theme..."
                  maxLength={100}
                />
              </div>
              <div className="form-group">
                <label htmlFor="mood">Mood</label>
                <select
                  id="mood"
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                >
                  <option value="neutral">Neutral</option>
                  <option value="happy">Happy</option>
                  <option value="sad">Sad</option>
                  <option value="romantic">Romantic</option>
                  <option value="mysterious">Mysterious</option>
                  <option value="peaceful">Peaceful</option>
                  <option value="energetic">Energetic</option>
                </select>
              </div>
            </div>

            {selectedType === 'acrostic' && (
              <div className="form-group">
                <label htmlFor="custom-word">Acrostic Word *</label>
                <input
                  id="custom-word"
                  type="text"
                  value={customWord}
                  onChange={(e) => setCustomWord(e.target.value.toUpperCase())}
                  placeholder="Enter word for acrostic..."
                  maxLength={20}
                />
              </div>
            )}

            <button
              className="generate-btn"
              onClick={generatePoem}
              disabled={isGenerating || !theme.trim() || (selectedType === 'acrostic' && !customWord.trim())}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  Generating...
                </>
              ) : (
                <>
                  ✨ Generate Poem
                </>
              )}
            </button>
          </div>

          {generatedPoem && (
            <div className="poem-result">
              <div className="poem-header-result">
                <h3>{generatedPoem.title}</h3>
                <div className="poem-actions">
                  <button
                    className="action-btn"
                    onClick={() => copyToClipboard(generatedPoem.content)}
                  >
                    📋 Copy
                  </button>
                </div>
              </div>

              <div className="poem-content">
                {generatedPoem.content.split('\n').map((line, index) => (
                  <div key={index} className="poem-line">
                    <span className="line-number">{index + 1}</span>
                    <span className="line-text">{line}</span>
                    {generatedPoem.syllable_counts[index] && (
                      <span className="syllable-count">
                        ({generatedPoem.syllable_counts[index]})
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {generatedPoem.validation && (
                <div className={`validation ${generatedPoem.validation.is_valid ? 'valid' : 'invalid'}`}>
                  <div className="validation-header">
                    <span className={`status ${generatedPoem.validation.is_valid ? 'valid' : 'invalid'}`}>
                      {generatedPoem.validation.is_valid ? '✅ Valid' : '⚠️ Issues Found'}
                    </span>
                    <span className="score">Score: {Math.round(generatedPoem.validation.score * 100)}%</span>
                  </div>
                  
                  {generatedPoem.validation.issues.length > 0 && (
                    <div className="validation-issues">
                      <h4>Issues:</h4>
                      <ul>
                        {generatedPoem.validation.issues.map((issue, index) => (
                          <li key={index}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'analyze' && (
        <div className="analyze-tab">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="analyze-text">Poem Text</label>
              <textarea
                id="analyze-text"
                value={analyzeText}
                onChange={(e) => setAnalyzeText(e.target.value)}
                placeholder="Paste your poem here for analysis..."
                rows={8}
              />
            </div>

            <div className="form-actions">
              <button
                className="analyze-btn"
                onClick={analyzePoem}
                disabled={isGenerating || !analyzeText.trim()}
              >
                {isGenerating ? (
                  <>
                    <span className="spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  <>
                    🔍 Analyze Structure
                  </>
                )}
              </button>

              <button
                className="validate-btn"
                onClick={validatePoem}
                disabled={isGenerating || !analyzeText.trim() || !selectedType}
              >
                ✅ Validate as {selectedPoemType?.name || 'Selected Type'}
              </button>
            </div>
          </div>

          {analysisResult && (
            <div className="analysis-result">
              <h3>📊 Analysis Results</h3>
              
              <div className="analysis-stats">
                <div className="stat">
                  <span className="label">Lines:</span>
                  <span className="value">{analysisResult.line_count}</span>
                </div>
                <div className="stat">
                  <span className="label">Total Syllables:</span>
                  <span className="value">{analysisResult.total_syllables}</span>
                </div>
                <div className="stat">
                  <span className="label">Avg Syllables:</span>
                  <span className="value">{analysisResult.average_syllables}</span>
                </div>
                <div className="stat">
                  <span className="label">Rhyme Quality:</span>
                  <span className="value">{Math.round(analysisResult.rhyme_analysis?.quality_score * 100 || 0)}%</span>
                </div>
              </div>

              {analysisResult.syllable_counts && (
                <div className="syllable-pattern">
                  <h4>Syllable Pattern</h4>
                  <div className="pattern">
                    {analysisResult.syllable_counts.join(' - ')}
                  </div>
                </div>
              )}

              {analysisResult.identified_types && analysisResult.identified_types.length > 0 && (
                <div className="identified-types">
                  <h4>Possible Poem Types</h4>
                  {analysisResult.identified_types.map((type: any, index: number) => (
                    <div key={index} className="identified-type">
                      <span className="type-name">{type.type.replace('_', ' ')}</span>
                      <span className="confidence">{Math.round(type.confidence * 100)}% match</span>
                    </div>
                  ))}
                </div>
              )}

              {analysisResult.validation && (
                <div className={`validation ${analysisResult.validation.is_valid ? 'valid' : 'invalid'}`}>
                  <div className="validation-header">
                    <span className={`status ${analysisResult.validation.is_valid ? 'valid' : 'invalid'}`}>
                      {analysisResult.validation.is_valid ? '✅ Valid' : '⚠️ Issues Found'}
                    </span>
                    <span className="score">Score: {Math.round(analysisResult.validation.score * 100)}%</span>
                  </div>
                  
                  {analysisResult.validation.issues.length > 0 && (
                    <div className="validation-issues">
                      <h4>Issues:</h4>
                      <ul>
                        {analysisResult.validation.issues.map((issue: string, index: number) => (
                          <li key={index}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PoemGenerator;