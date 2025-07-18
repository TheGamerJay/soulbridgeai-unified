import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AdminDashboard from './components/AdminDashboard';
import CompanionSelector from './components/CompanionSelector';
import './App.css';

function HomePage() {
  const [apiResponse, setApiResponse] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Test backend connection
    const apiUrl = import.meta.env.VITE_API_URL || 'https://soulbridgeai.com';
    fetch(`${apiUrl}/health`)
      .then(res => res.json())
      .then(data => {
        setApiResponse(JSON.stringify(data, null, 2));
        setLoading(false);
      })
      .catch(err => {
        setApiResponse(`API connection error: ${err.message}`);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <img src="/favicon.ico" alt="SoulBridge Logo" style={{ width: "80px", height: "80px" }} />
        <h1>Welcome to SoulBridge AI</h1>
        <p className="subtitle">Your AI Companion Journey</p>
        
        <div className="navigation">
          <Link to="/admin" className="admin-link">🛡️ Admin Dashboard</Link>
          <Link to="/companions" className="admin-link">🤖 Choose Companion</Link>
        </div>
        
        <div className="api-status">
          <h3>Backend Connection Status:</h3>
          {loading ? (
            <div className="loading">Connecting to backend...</div>
          ) : (
            <pre className="api-response">{apiResponse}</pre>
          )}
        </div>
        
        <div className="features">
          <h3>Features Available:</h3>
          <ul>
            <li>🤖 AI Chat Interface</li>
            <li>🎭 Multiple AI Companions</li>
            <li>🛡️ Admin Dashboard with Logs</li>
            <li>🔒 JWT Authentication</li>
            <li>📊 Session Monitoring</li>
            <li>📱 Mobile Responsive Design</li>
          </ul>
        </div>
        
        <div className="links">
          <a href={import.meta.env.VITE_API_URL || 'https://soulbridgeai.com'} target="_blank" rel="noopener noreferrer" className="backend-link">
            Visit SoulBridge AI Backend
          </a>
        </div>
      </header>
    </div>
  );
}

function App() {
  const handleCompanionSelect = (companion) => {
    console.log('Selected companion:', companion);
    // Here you can save to localStorage, send to backend, etc.
    localStorage.setItem('selectedCompanion', JSON.stringify(companion));
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route 
          path="/companions" 
          element={
            <CompanionSelector 
              onCompanionSelect={handleCompanionSelect}
              initialCompanion="Blayzo"
            />
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;