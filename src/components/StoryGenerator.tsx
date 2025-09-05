import React, { useState, useEffect } from 'react';
import './StoryGenerator.css';

interface Character {
  name: string;
  role: string;
  archetype: string;
  motivation: string;
  conflict: string;
  traits: string[];
  age: number | null;
  occupation: string | null;
}

interface PlotPoint {
  name: string;
  description: string;
  chapter: number;
  position: number;
  characters: string[];
  conflict_type: string;
}

interface StoryStructure {
  type: string;
  plot_points: PlotPoint[];
  themes: string[];
  subplots: string[];
}

interface StoryOutline {
  id?: number;
  title: string;
  genre: string;
  length: string;
  premise: string;
  characters: Character[];
  structure: StoryStructure;
  chapters: Chapter[];
  word_count_target: number;
  themes: string[];
  target_audience: string;
  setting: {
    time: string;
    place: string;
    world_building: string;
  };
}

interface Chapter {
  number: number;
  title: string;
  plot_point: string;
  description: string;
  characters: string[];
  word_count_target: number;
  scene_goal: string;
  conflict_type: string;
}

interface GenreInfo {
  value: string;
  name: string;
  description: string;
  popular: boolean;
}

interface LengthInfo {
  value: string;
  name: string;
  description: string;
}

interface StructureInfo {
  value: string;
  name: string;
  description: string;
}

interface UserStats {
  user_plan: string;
  daily_limits: {
    story_outlines: number;
    story_content: number;
  };
  current_usage: {
    story_outlines: number;
    story_content: number;
  };
  remaining_usage: {
    story_outlines: number;
    story_content: number;
  };
  features: {
    all_genres: boolean;
    all_lengths: boolean;
    advanced_analysis: boolean;
    unlimited_outlines: boolean;
    unlimited_content: boolean;
    character_development: boolean;
    plot_structure: boolean;
  };
  available_genres: number;
  available_structures: number;
}

export const StoryGenerator: React.FC = () => {
  const [genres, setGenres] = useState<GenreInfo[]>([]);
  const [lengths, setLengths] = useState<LengthInfo[]>([]);
  const [structures, setStructures] = useState<StructureInfo[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  
  const [selectedGenre, setSelectedGenre] = useState<string>('');
  const [selectedLength, setSelectedLength] = useState<string>('');
  const [selectedStructure, setSelectedStructure] = useState<string>('three_act');
  const [premise, setPremise] = useState<string>('');
  const [themes, setThemes] = useState<string[]>([]);
  const [themeInput, setThemeInput] = useState<string>('');
  const [characterCount, setCharacterCount] = useState<number>(3);
  
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [currentOutline, setCurrentOutline] = useState<StoryOutline | null>(null);
  const [generatedContent, setGeneratedContent] = useState<string>('');
  const [error, setError] = useState<string>('');
  
  const [activeTab, setActiveTab] = useState<'outline' | 'generate' | 'analyze'>('outline');
  const [analyzeText, setAnalyzeText] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [selectedChapter, setSelectedChapter] = useState<number>(0);

  useEffect(() => {
    loadGenres();
    loadUserStats();
  }, []);

  const loadGenres = async () => {
    try {
      const response = await fetch('/api/stories/genres');
      const data = await response.json();
      
      if (data.success) {
        setGenres(data.genres);
        setLengths(data.lengths);
        setStructures(data.structures);
        
        if (data.genres.length > 0) {
          setSelectedGenre(data.genres[0].value);
        }
        if (data.lengths.length > 0) {
          setSelectedLength(data.lengths[0].value);
        }
      }
    } catch (error) {
      console.error('Error loading genres:', error);
    }
  };

  const loadUserStats = async () => {
    try {
      const response = await fetch('/api/stories/stats');
      const data = await response.json();
      
      if (data.success) {
        setUserStats(data.stats);
      }
    } catch (error) {
      console.error('Error loading user stats:', error);
    }
  };

  const generateOutline = async () => {
    if (!premise.trim()) {
      setError('Please enter a story premise');
      return;
    }

    if (!selectedGenre || !selectedLength) {
      setError('Please select genre and length');
      return;
    }

    setIsGenerating(true);
    setError('');
    setCurrentOutline(null);

    try {
      const requestData = {
        genre: selectedGenre,
        length: selectedLength,
        premise: premise,
        themes: themes,
        structure: selectedStructure,
        character_count: characterCount
      };

      const response = await fetch('/api/stories/generate-outline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setCurrentOutline(data.outline);
        setActiveTab('generate');
        loadUserStats(); // Refresh stats
      } else {
        setError(data.error || 'Failed to generate outline');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error generating outline:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateContent = async (chapterNumber?: number) => {
    if (!currentOutline) {
      setError('Please generate an outline first');
      return;
    }

    setIsGenerating(true);
    setError('');
    setGeneratedContent('');

    try {
      const requestData = {
        outline: currentOutline,
        ...(chapterNumber && { chapter_number: chapterNumber })
      };

      const response = await fetch('/api/stories/generate-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedContent(data.content);
        if (!chapterNumber) {
          loadUserStats(); // Refresh stats for full story generation
        }
      } else {
        setError(data.error || 'Failed to generate content');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error generating content:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzeStory = async () => {
    if (!analyzeText.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setIsGenerating(true);
    setError('');
    setAnalysisResult(null);

    try {
      const response = await fetch('/api/stories/analyze', {
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
        setError(data.error || 'Failed to analyze story');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error analyzing story:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const addTheme = () => {
    if (themeInput.trim() && !themes.includes(themeInput.trim())) {
      setThemes([...themes, themeInput.trim()]);
      setThemeInput('');
    }
  };

  const removeTheme = (themeToRemove: string) => {
    setThemes(themes.filter(theme => theme !== themeToRemove));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Copied to clipboard');
    });
  };

  return (
    <div className="story-generator">
      <div className="story-header">
        <h2>📚 Story Generator</h2>
        <p>Create compelling narratives with AI-powered storytelling</p>
        
        {userStats && (
          <div className="usage-info">
            <span className="plan-badge">{userStats.user_plan.toUpperCase()}</span>
            <div className="usage-stats">
              <span>Outlines: {userStats.daily_limits.story_outlines === -1 ? 'Unlimited' : `${userStats.remaining_usage.story_outlines}/${userStats.daily_limits.story_outlines}`}</span>
              <span>Content: {userStats.daily_limits.story_content === -1 ? 'Unlimited' : `${userStats.remaining_usage.story_content}/${userStats.daily_limits.story_content}`}</span>
            </div>
          </div>
        )}
      </div>

      <div className="story-tabs">
        <button
          className={`tab ${activeTab === 'outline' ? 'active' : ''}`}
          onClick={() => setActiveTab('outline')}
        >
          Create Outline
        </button>
        <button
          className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
          disabled={!currentOutline}
        >
          Generate Story
        </button>
        <button
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Analyze Text
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {activeTab === 'outline' && (
        <div className="outline-tab">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="premise">Story Premise *</label>
              <textarea
                id="premise"
                value={premise}
                onChange={(e) => setPremise(e.target.value)}
                placeholder="Describe your story idea, main conflict, or theme..."
                rows={3}
                maxLength={500}
              />
              <small>Max 500 characters</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="genre">Genre *</label>
                <select
                  id="genre"
                  value={selectedGenre}
                  onChange={(e) => setSelectedGenre(e.target.value)}
                >
                  <option value="">Select Genre</option>
                  {genres.map(genre => (
                    <option key={genre.value} value={genre.value}>
                      {genre.name} {genre.popular && '⭐'}
                    </option>
                  ))}
                </select>
                {selectedGenre && (
                  <div className="selection-info">
                    {genres.find(g => g.value === selectedGenre)?.description}
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="length">Story Length *</label>
                <select
                  id="length"
                  value={selectedLength}
                  onChange={(e) => setSelectedLength(e.target.value)}
                >
                  <option value="">Select Length</option>
                  {lengths.map(length => (
                    <option key={length.value} value={length.value}>
                      {length.name}
                    </option>
                  ))}
                </select>
                {selectedLength && (
                  <div className="selection-info">
                    {lengths.find(l => l.value === selectedLength)?.description}
                  </div>
                )}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="structure">Narrative Structure</label>
                <select
                  id="structure"
                  value={selectedStructure}
                  onChange={(e) => setSelectedStructure(e.target.value)}
                >
                  {structures.map(structure => (
                    <option key={structure.value} value={structure.value}>
                      {structure.name}
                    </option>
                  ))}
                </select>
                {selectedStructure && (
                  <div className="selection-info">
                    {structures.find(s => s.value === selectedStructure)?.description}
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="character-count">Number of Characters</label>
                <select
                  id="character-count"
                  value={characterCount}
                  onChange={(e) => setCharacterCount(parseInt(e.target.value))}
                >
                  {[3, 4, 5, 6, 7, 8].map(count => (
                    <option key={count} value={count}>
                      {count} Characters
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Themes</label>
              <div className="themes-container">
                <div className="themes-list">
                  {themes.map(theme => (
                    <span key={theme} className="theme-tag">
                      {theme}
                      <button onClick={() => removeTheme(theme)}>×</button>
                    </span>
                  ))}
                </div>
                <div className="theme-input">
                  <input
                    type="text"
                    value={themeInput}
                    onChange={(e) => setThemeInput(e.target.value)}
                    placeholder="Enter theme and press Add"
                    onKeyPress={(e) => e.key === 'Enter' && addTheme()}
                  />
                  <button type="button" onClick={addTheme}>Add</button>
                </div>
              </div>
              <small>Common themes: love, betrayal, redemption, power, family, friendship</small>
            </div>

            <button
              className="generate-btn"
              onClick={generateOutline}
              disabled={isGenerating || !premise.trim() || !selectedGenre || !selectedLength}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  Generating Outline...
                </>
              ) : (
                <>
                  ✨ Generate Story Outline
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'generate' && currentOutline && (
        <div className="generate-tab">
          <div className="outline-summary">
            <h3>📋 {currentOutline.title}</h3>
            <div className="outline-meta">
              <span>Genre: {currentOutline.genre.replace('_', ' ')}</span>
              <span>Length: {currentOutline.length.replace('_', ' ')}</span>
              <span>Target: {currentOutline.word_count_target.toLocaleString()} words</span>
              <span>Characters: {currentOutline.characters.length}</span>
              <span>Chapters: {currentOutline.chapters.length}</span>
            </div>
          </div>

          <div className="content-generation">
            <div className="generation-options">
              <button
                className="generate-btn full-story"
                onClick={() => generateContent()}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <span className="spinner"></span>
                    Generating Full Story...
                  </>
                ) : (
                  <>
                    📖 Generate Full Story
                  </>
                )}
              </button>

              <div className="chapter-generation">
                <select
                  value={selectedChapter}
                  onChange={(e) => setSelectedChapter(parseInt(e.target.value))}
                  disabled={isGenerating}
                >
                  <option value={0}>Select Chapter</option>
                  {currentOutline.chapters.map((chapter, index) => (
                    <option key={index} value={index + 1}>
                      Chapter {index + 1}: {chapter.title}
                    </option>
                  ))}
                </select>
                <button
                  className="generate-btn chapter"
                  onClick={() => generateContent(selectedChapter)}
                  disabled={isGenerating || selectedChapter === 0}
                >
                  Generate Chapter
                </button>
              </div>
            </div>

            {generatedContent && (
              <div className="story-content">
                <div className="content-header">
                  <h3>Generated Content</h3>
                  <div className="content-stats">
                    <span>Words: {generatedContent.split(' ').length.toLocaleString()}</span>
                    <span>Characters: {generatedContent.length.toLocaleString()}</span>
                  </div>
                  <button
                    className="copy-btn"
                    onClick={() => copyToClipboard(generatedContent)}
                  >
                    📋 Copy
                  </button>
                </div>
                <div className="content-text">
                  {generatedContent.split('\n').map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="outline-details">
            <div className="characters-section">
              <h4>👥 Characters</h4>
              <div className="characters-grid">
                {currentOutline.characters.map((character, index) => (
                  <div key={index} className="character-card">
                    <h5>{character.name}</h5>
                    <div className="character-role">{character.role} • {character.archetype}</div>
                    <div className="character-details">
                      <div><strong>Motivation:</strong> {character.motivation}</div>
                      <div><strong>Conflict:</strong> {character.conflict}</div>
                      <div><strong>Traits:</strong> {character.traits.join(', ')}</div>
                      {character.age && <div><strong>Age:</strong> {character.age}</div>}
                      {character.occupation && <div><strong>Occupation:</strong> {character.occupation}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="structure-section">
              <h4>🗺️ Plot Structure</h4>
              <div className="plot-points">
                {currentOutline.structure.plot_points.map((point, index) => (
                  <div key={index} className="plot-point">
                    <div className="point-position">{Math.round(point.position * 100)}%</div>
                    <div className="point-details">
                      <h5>{point.name}</h5>
                      <p>{point.description}</p>
                      <div className="point-meta">
                        <span>Chapter {point.chapter}</span>
                        <span>{point.conflict_type} conflict</span>
                        <span>Focus: {point.characters.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chapters-section">
              <h4>📝 Chapter Outlines</h4>
              <div className="chapters-list">
                {currentOutline.chapters.map((chapter, index) => (
                  <div key={index} className="chapter-outline">
                    <h5>Chapter {chapter.number}: {chapter.title}</h5>
                    <p><strong>Goal:</strong> {chapter.scene_goal}</p>
                    <div className="chapter-meta">
                      <span>Characters: {chapter.characters.join(', ')}</span>
                      <span>Target: {chapter.word_count_target} words</span>
                      <span>Conflict: {chapter.conflict_type}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analyze' && (
        <div className="analyze-tab">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="analyze-text">Story Text</label>
              <textarea
                id="analyze-text"
                value={analyzeText}
                onChange={(e) => setAnalyzeText(e.target.value)}
                placeholder="Paste your story here for analysis..."
                rows={10}
              />
            </div>

            <button
              className="analyze-btn"
              onClick={analyzeStory}
              disabled={isGenerating || !analyzeText.trim()}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  Analyzing...
                </>
              ) : (
                <>
                  🔍 Analyze Story
                </>
              )}
            </button>
          </div>

          {analysisResult && (
            <div className="analysis-result">
              <h3>📊 Story Analysis</h3>
              
              <div className="analysis-stats">
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.word_count.toLocaleString()}</div>
                  <div className="stat-label">Words</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.sentence_count}</div>
                  <div className="stat-label">Sentences</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.paragraph_count}</div>
                  <div className="stat-label">Paragraphs</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.avg_sentence_length}</div>
                  <div className="stat-label">Avg Length</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{Math.round(analysisResult.readability_score)}</div>
                  <div className="stat-label">Readability</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.dialogue_percentage}%</div>
                  <div className="stat-label">Dialogue</div>
                </div>
              </div>

              <div className="analysis-details">
                <div className="analysis-section">
                  <h4>📖 Style Analysis</h4>
                  <div className="detail-grid">
                    <div><strong>Point of View:</strong> {analysisResult.pov.replace('_', ' ')}</div>
                    <div><strong>Tense:</strong> {analysisResult.tense}</div>
                    <div><strong>Dialogue Percentage:</strong> {analysisResult.dialogue_percentage}%</div>
                  </div>
                </div>

                {analysisResult.character_mentions && Object.keys(analysisResult.character_mentions).length > 0 && (
                  <div className="analysis-section">
                    <h4>👥 Character Mentions</h4>
                    <div className="character-mentions">
                      {Object.entries(analysisResult.character_mentions).map(([name, count]: [string, any]) => (
                        <div key={name} className="mention-item">
                          <span className="character-name">{name}</span>
                          <span className="mention-count">{count} times</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.theme_indicators && analysisResult.theme_indicators.length > 0 && (
                  <div className="analysis-section">
                    <h4>🎭 Identified Themes</h4>
                    <div className="themes-list">
                      {analysisResult.theme_indicators.map((theme: string, index: number) => (
                        <span key={index} className="theme-tag">{theme}</span>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.conflict_types && analysisResult.conflict_types.length > 0 && (
                  <div className="analysis-section">
                    <h4>⚔️ Conflict Types</h4>
                    <div className="conflict-types">
                      {analysisResult.conflict_types.map((type: string, index: number) => (
                        <span key={index} className="conflict-tag">{type.replace('_', ' ')}</span>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                  <div className="analysis-section">
                    <h4>💡 Recommendations</h4>
                    <div className="recommendations">
                      {analysisResult.recommendations.map((rec: string, index: number) => (
                        <div key={index} className="recommendation">{rec}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StoryGenerator;