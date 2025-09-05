import React, { useState, useEffect } from 'react';
import DrumMachinePro from './DrumMachinePro';
import PoemGenerator from './PoemGenerator';
import StoryGenerator from './StoryGenerator';
import WritingSuite from './WritingSuite';
import './MiniStudio.css';

type StudioMode = 'drums' | 'poems' | 'stories' | 'writing' | 'lyrics';

interface StudioTab {
  id: StudioMode;
  name: string;
  icon: string;
  description: string;
  component: React.ComponentType;
}

export const MiniStudio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<StudioMode>('drums');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const studioTabs: StudioTab[] = [
    {
      id: 'drums',
      name: 'Drums',
      icon: '🥁',
      description: 'Professional drum machine with sampling',
      component: DrumMachinePro
    },
    {
      id: 'poems',
      name: 'Poems',
      icon: '🎭',
      description: 'Generate and analyze poetry',
      component: PoemGenerator
    },
    {
      id: 'stories',
      name: 'Stories',
      icon: '📚',
      description: 'Create compelling narratives',
      component: StoryGenerator
    },
    {
      id: 'writing',
      name: 'Writing',
      icon: '✍️',
      description: 'Professional writing suite',
      component: WritingSuite
    },
    {
      id: 'lyrics',
      name: 'Lyrics',
      icon: '🎤',
      description: 'AI lyric writing studio',
      component: () => (
        <div className="coming-soon">
          <div className="coming-soon-content">
            <h3>🎤 Lyrics Studio</h3>
            <p>AI-powered lyric writing with consent management</p>
            <div className="features-preview">
              <div className="feature">✨ Smart lyric generation</div>
              <div className="feature">🔍 Plagiarism detection</div>
              <div className="feature">🤝 Artist consent system</div>
              <div className="feature">🎵 Rhyme scheme analysis</div>
            </div>
            <p className="status">Coming soon...</p>
          </div>
        </div>
      )
    }
  ];

  const currentTab = studioTabs.find(tab => tab.id === activeTab);
  const CurrentComponent = currentTab?.component;

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleKeyboardShortcuts = (e: KeyboardEvent) => {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case '1':
          e.preventDefault();
          setActiveTab('drums');
          break;
        case '2':
          e.preventDefault();
          setActiveTab('poems');
          break;
        case '3':
          e.preventDefault();
          setActiveTab('stories');
          break;
        case '4':
          e.preventDefault();
          setActiveTab('writing');
          break;
        case '5':
          e.preventDefault();
          setActiveTab('lyrics');
          break;
        case 'f':
          e.preventDefault();
          toggleFullscreen();
          break;
      }
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyboardShortcuts);
    return () => {
      document.removeEventListener('keydown', handleKeyboardShortcuts);
    };
  }, []);

  return (
    <div className={`mini-studio ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="studio-header">
        <div className="studio-title">
          <h1>🎨 Mini Studio</h1>
          <p>Professional AI-powered creative suite</p>
        </div>
        
        <div className="studio-controls">
          <button
            className="fullscreen-btn"
            onClick={toggleFullscreen}
            title="Toggle Fullscreen (Ctrl+F)"
          >
            {isFullscreen ? '📐' : '⛶'}
          </button>
        </div>
      </div>

      <div className="studio-tabs">
        {studioTabs.map((tab, index) => (
          <button
            key={tab.id}
            className={`studio-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            title={`${tab.description} (Ctrl+${index + 1})`}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-name">{tab.name}</span>
            {tab.id === 'lyrics' && <span className="coming-soon-badge">Soon</span>}
          </button>
        ))}
      </div>

      <div className="studio-workspace">
        {CurrentComponent && <CurrentComponent />}
      </div>

      <div className="studio-footer">
        <div className="shortcuts-info">
          <span>Shortcuts:</span>
          <span>Ctrl+1-5: Switch tabs</span>
          <span>Ctrl+F: Fullscreen</span>
        </div>
        <div className="studio-status">
          <span className="current-mode">{currentTab?.name} Mode</span>
          <span className="status-dot active"></span>
        </div>
      </div>
    </div>
  );
};

export default MiniStudio;