import React, { useState, useEffect } from 'react';
import './WritingSuite.css';

interface WritingType {
  value: string;
  name: string;
  description: string;
  features: string[];
}

interface Category {
  name: string;
  types: WritingType[];
}

interface Categories {
  scripts: Category;
  articles: Category;
  letters: Category;
  creative: Category;
}

interface Tone {
  value: string;
  name: string;
  description: string;
}

interface Length {
  value: string;
  name: string;
  description: string;
}

interface Writing {
  content: string;
  word_count: number;
  character_count: number;
  estimated_reading_time: number;
  style_score: number;
  readability_score: number;
  format_analysis: any;
  suggestions: string[];
}

interface PromptDetails {
  writing_type: string;
  topic: string;
  tone: string;
  length: string;
  target_audience: string;
}

interface UserStats {
  user_plan: string;
  daily_limit: number;
  current_usage: number;
  remaining_usage: number;
  features: {
    all_writing_types: boolean;
    all_tones: boolean;
    format_customization: boolean;
    unlimited_generation: boolean;
    advanced_analytics: boolean;
    export_options: boolean;
    save_writings: boolean;
    style_analysis: boolean;
  };
  available_categories: number;
  total_writing_types: number;
  available_tones: number;
}

export const WritingSuite: React.FC = () => {
  const [categories, setCategories] = useState<Categories | null>(null);
  const [tones, setTones] = useState<Tone[]>([]);
  const [lengths, setLengths] = useState<Length[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  
  const [activeCategory, setActiveCategory] = useState<string>('scripts');
  const [selectedWritingType, setSelectedWritingType] = useState<string>('');
  const [topic, setTopic] = useState<string>('');
  const [selectedTone, setSelectedTone] = useState<string>('professional');
  const [selectedLength, setSelectedLength] = useState<string>('medium');
  const [targetAudience, setTargetAudience] = useState<string>('');
  const [keyPoints, setKeyPoints] = useState<string[]>(['']);
  const [additionalRequirements, setAdditionalRequirements] = useState<string>('');
  const [saveTitle, setSaveTitle] = useState<string>('');
  
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedWriting, setGeneratedWriting] = useState<Writing | null>(null);
  const [promptDetails, setPromptDetails] = useState<PromptDetails | null>(null);
  const [error, setError] = useState<string>('');
  
  const [activeTab, setActiveTab] = useState<'generate' | 'analyze'>('generate');
  const [analyzeContent, setAnalyzeContent] = useState<string>('');
  const [analyzeType, setAnalyzeType] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  useEffect(() => {
    loadWritingTypes();
    loadUserStats();
  }, []);

  const loadWritingTypes = async () => {
    try {
      const response = await fetch('/api/writing/types');
      const data = await response.json();
      
      if (data.success) {
        setCategories(data.categories);
        setTones(data.tones);
        setLengths(data.lengths);
        
        // Set first available writing type
        const firstCategory = Object.keys(data.categories)[0];
        if (firstCategory && data.categories[firstCategory].types.length > 0) {
          setSelectedWritingType(data.categories[firstCategory].types[0].value);
        }
      }
    } catch (error) {
      console.error('Error loading writing types:', error);
    }
  };

  const loadUserStats = async () => {
    try {
      const response = await fetch('/api/writing/stats');
      const data = await response.json();
      
      if (data.success) {
        setUserStats(data.stats);
      }
    } catch (error) {
      console.error('Error loading user stats:', error);
    }
  };

  const generateWriting = async () => {
    if (!selectedWritingType) {
      setError('Please select a writing type');
      return;
    }

    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    setIsGenerating(true);
    setError('');
    setGeneratedWriting(null);
    setPromptDetails(null);

    try {
      const requestData = {
        writing_type: selectedWritingType,
        topic: topic,
        tone: selectedTone,
        length: selectedLength,
        target_audience: targetAudience,
        key_points: keyPoints.filter(point => point.trim()),
        additional_requirements: additionalRequirements,
        save_title: saveTitle
      };

      const response = await fetch('/api/writing/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedWriting(data.writing);
        setPromptDetails(data.prompt_details);
        loadUserStats(); // Refresh stats
      } else {
        setError(data.error || 'Failed to generate writing');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error generating writing:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzeWriting = async () => {
    if (!analyzeContent.trim()) {
      setError('Please enter content to analyze');
      return;
    }

    setIsGenerating(true);
    setError('');
    setAnalysisResult(null);

    try {
      const response = await fetch('/api/writing/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: analyzeContent,
          writing_type: analyzeType
        })
      });

      const data = await response.json();

      if (data.success) {
        setAnalysisResult(data.analysis);
      } else {
        setError(data.error || 'Failed to analyze writing');
      }
    } catch (error) {
      setError('Network error occurred');
      console.error('Error analyzing writing:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const addKeyPoint = () => {
    if (keyPoints.length < 10) {
      setKeyPoints([...keyPoints, '']);
    }
  };

  const updateKeyPoint = (index: number, value: string) => {
    const newKeyPoints = [...keyPoints];
    newKeyPoints[index] = value;
    setKeyPoints(newKeyPoints);
  };

  const removeKeyPoint = (index: number) => {
    if (keyPoints.length > 1) {
      const newKeyPoints = keyPoints.filter((_, i) => i !== index);
      setKeyPoints(newKeyPoints);
    }
  };

  const switchCategory = (categoryKey: string) => {
    setActiveCategory(categoryKey);
    if (categories && categories[categoryKey as keyof Categories].types.length > 0) {
      setSelectedWritingType(categories[categoryKey as keyof Categories].types[0].value);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Copied to clipboard');
    });
  };

  const downloadAsText = (content: string, type: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}_${new Date().toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const selectedType = categories && selectedWritingType ? 
    Object.values(categories)
      .flatMap(cat => cat.types)
      .find(type => type.value === selectedWritingType) : null;

  return (
    <div className="writing-suite">
      <div className="suite-header">
        <h2>✍️ Writing Suite</h2>
        <p>Professional writing generation for all your needs</p>
        
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

      <div className="suite-tabs">
        <button
          className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          Generate Writing
        </button>
        <button
          className={`tab ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Analyze Writing
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {activeTab === 'generate' && (
        <div className="generate-tab">
          {categories && (
            <div className="category-selection">
              <h3>Choose Writing Category</h3>
              <div className="category-tabs">
                {Object.entries(categories).map(([key, category]) => (
                  <button
                    key={key}
                    className={`category-tab ${activeCategory === key ? 'active' : ''}`}
                    onClick={() => switchCategory(key)}
                  >
                    {key === 'scripts' && '🎬'}
                    {key === 'articles' && '📰'}
                    {key === 'letters' && '📧'}
                    {key === 'creative' && '✨'}
                    {category.name}
                  </button>
                ))}
              </div>

              <div className="writing-types-grid">
                {categories[activeCategory as keyof Categories]?.types.map(type => (
                  <div
                    key={type.value}
                    className={`writing-type-card ${selectedWritingType === type.value ? 'selected' : ''}`}
                    onClick={() => setSelectedWritingType(type.value)}
                  >
                    <h4>{type.name}</h4>
                    <p>{type.description}</p>
                    <div className="features">
                      {type.features.map((feature, index) => (
                        <span key={index} className="feature-tag">{feature}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="writing-form">
            <div className="form-section">
              <h3>📝 Writing Configuration</h3>
              
              <div className="form-group">
                <label htmlFor="topic">Topic/Subject *</label>
                <textarea
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Describe what you want to write about..."
                  rows={3}
                  maxLength={200}
                />
                <small>Max 200 characters</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="tone">Tone & Style</label>
                  <select
                    id="tone"
                    value={selectedTone}
                    onChange={(e) => setSelectedTone(e.target.value)}
                  >
                    {tones.map(tone => (
                      <option key={tone.value} value={tone.value}>
                        {tone.name}
                      </option>
                    ))}
                  </select>
                  {tones.find(t => t.value === selectedTone) && (
                    <div className="selection-info">
                      {tones.find(t => t.value === selectedTone)?.description}
                    </div>
                  )}
                </div>
                
                <div className="form-group">
                  <label htmlFor="length">Length</label>
                  <select
                    id="length"
                    value={selectedLength}
                    onChange={(e) => setSelectedLength(e.target.value)}
                  >
                    {lengths.map(length => (
                      <option key={length.value} value={length.value}>
                        {length.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="target-audience">Target Audience</label>
                <input
                  id="target-audience"
                  type="text"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  placeholder="e.g., business professionals, general public, students..."
                />
              </div>

              <div className="form-group">
                <label>Key Points to Include</label>
                <div className="key-points-container">
                  {keyPoints.map((point, index) => (
                    <div key={index} className="key-point">
                      <span className="point-number">{index + 1}</span>
                      <input
                        type="text"
                        value={point}
                        onChange={(e) => updateKeyPoint(index, e.target.value)}
                        placeholder="Enter a key point..."
                      />
                      {keyPoints.length > 1 && (
                        <button
                          type="button"
                          className="remove-btn"
                          onClick={() => removeKeyPoint(index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  {keyPoints.length < 10 && (
                    <button
                      type="button"
                      className="add-point-btn"
                      onClick={addKeyPoint}
                    >
                      + Add Point
                    </button>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="additional-requirements">Additional Requirements</label>
                <textarea
                  id="additional-requirements"
                  value={additionalRequirements}
                  onChange={(e) => setAdditionalRequirements(e.target.value)}
                  placeholder="Any specific formatting, style, or content requirements..."
                  rows={3}
                />
              </div>

              <div className="form-group">
                <label htmlFor="save-title">Save As (Optional)</label>
                <input
                  id="save-title"
                  type="text"
                  value={saveTitle}
                  onChange={(e) => setSaveTitle(e.target.value)}
                  placeholder="Give your writing a title to save it..."
                />
              </div>

              <button
                className="generate-btn"
                onClick={generateWriting}
                disabled={isGenerating || !selectedWritingType || !topic.trim()}
              >
                {isGenerating ? (
                  <>
                    <span className="spinner"></span>
                    Generating...
                  </>
                ) : (
                  <>
                    ✨ Generate Writing
                  </>
                )}
              </button>
            </div>

            {generatedWriting && promptDetails && (
              <div className="writing-result">
                <div className="result-header">
                  <h3>Generated Content</h3>
                  <div className="result-stats">
                    <span>{generatedWriting.word_count.toLocaleString()} words</span>
                    <span>{generatedWriting.character_count.toLocaleString()} chars</span>
                    <span>{generatedWriting.estimated_reading_time} min read</span>
                    <span>{Math.round(generatedWriting.readability_score)} readability</span>
                  </div>
                </div>

                <div className="content-display">
                  {generatedWriting.content.split('\n').map((paragraph, index) => (
                    <p key={index}>{paragraph}</p>
                  ))}
                </div>

                <div className="writing-analysis">
                  <h4>📊 Writing Analysis</h4>
                  <div className="analysis-grid">
                    <div className="analysis-item">
                      <span className="label">Type:</span>
                      <span className="value">{promptDetails.writing_type.replace('_', ' ')}</span>
                    </div>
                    <div className="analysis-item">
                      <span className="label">Tone:</span>
                      <span className="value">{promptDetails.tone}</span>
                    </div>
                    <div className="analysis-item">
                      <span className="label">Length:</span>
                      <span className="value">{promptDetails.length}</span>
                    </div>
                    <div className="analysis-item">
                      <span className="label">Style Score:</span>
                      <span className="value">{Math.round(generatedWriting.style_score * 100)}%</span>
                    </div>
                  </div>
                </div>

                {generatedWriting.suggestions && generatedWriting.suggestions.length > 0 && (
                  <div className="suggestions-section">
                    <h4>💡 Suggestions for Improvement</h4>
                    {generatedWriting.suggestions.map((suggestion, index) => (
                      <div key={index} className="suggestion">{suggestion}</div>
                    ))}
                  </div>
                )}

                <div className="result-actions">
                  <button
                    className="action-btn"
                    onClick={() => copyToClipboard(generatedWriting.content)}
                  >
                    📋 Copy
                  </button>
                  <button
                    className="action-btn"
                    onClick={() => downloadAsText(generatedWriting.content, promptDetails.writing_type)}
                  >
                    💾 Download
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'analyze' && (
        <div className="analyze-tab">
          <div className="form-section">
            <h3>📊 Analyze Existing Writing</h3>
            
            <div className="form-group">
              <label htmlFor="analyze-content">Writing Content *</label>
              <textarea
                id="analyze-content"
                value={analyzeContent}
                onChange={(e) => setAnalyzeContent(e.target.value)}
                placeholder="Paste your writing here for analysis..."
                rows={8}
              />
              <small>Max 50,000 characters</small>
            </div>

            <div className="form-group">
              <label htmlFor="analyze-type">Writing Type (Optional)</label>
              <select
                id="analyze-type"
                value={analyzeType}
                onChange={(e) => setAnalyzeType(e.target.value)}
              >
                <option value="">Auto-detect</option>
                {categories && Object.values(categories)
                  .flatMap(cat => cat.types)
                  .map(type => (
                    <option key={type.value} value={type.value}>
                      {type.name}
                    </option>
                  ))}
              </select>
            </div>

            <button
              className="analyze-btn"
              onClick={analyzeWriting}
              disabled={isGenerating || !analyzeContent.trim()}
            >
              {isGenerating ? (
                <>
                  <span className="spinner"></span>
                  Analyzing...
                </>
              ) : (
                <>
                  🔍 Analyze Writing
                </>
              )}
            </button>
          </div>

          {analysisResult && (
            <div className="analysis-result">
              <h3>📈 Analysis Results</h3>
              
              <div className="analysis-stats">
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.word_count.toLocaleString()}</div>
                  <div className="stat-label">Words</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.character_count.toLocaleString()}</div>
                  <div className="stat-label">Characters</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{analysisResult.estimated_reading_time}</div>
                  <div className="stat-label">Min Read</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{Math.round(analysisResult.readability_score)}</div>
                  <div className="stat-label">Readability</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{Math.round(analysisResult.style_score * 100)}%</div>
                  <div className="stat-label">Style Score</div>
                </div>
              </div>

              <div className="detailed-analysis">
                <div className="analysis-section">
                  <h4>📝 Structure Analysis</h4>
                  <div className="detail-grid">
                    <div><strong>Paragraphs:</strong> {analysisResult.structure_analysis.paragraph_count}</div>
                    <div><strong>Sentences:</strong> {analysisResult.structure_analysis.sentence_count}</div>
                    <div><strong>Avg Sentence Length:</strong> {analysisResult.structure_analysis.avg_sentence_length} words</div>
                  </div>
                </div>

                {analysisResult.format_analysis && Object.keys(analysisResult.format_analysis).length > 0 && (
                  <div className="analysis-section">
                    <h4>🔧 Format Analysis</h4>
                    <div className="detail-grid">
                      {Object.entries(analysisResult.format_analysis).map(([key, value]: [string, any]) => (
                        <div key={key}>
                          <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}:</strong> {String(value)}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResult.suggestions && analysisResult.suggestions.length > 0 && (
                  <div className="analysis-section">
                    <h4>💡 Improvement Suggestions</h4>
                    {analysisResult.suggestions.map((suggestion: string, index: number) => (
                      <div key={index} className="suggestion">{suggestion}</div>
                    ))}
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

export default WritingSuite;