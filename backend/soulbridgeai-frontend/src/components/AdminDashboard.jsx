import { useEffect, useState } from 'react';
import { useSound, SoundButton } from '../hooks/useSound';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [logs, setLogs] = useState([]);
  const [adminLogs, setAdminLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [authToken, setAuthToken] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  
  // Sound effects
  const { playSuccessSound, playErrorSound } = useSound();

  // Admin login function
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
      });

      const data = await response.json();

      if (data.success) {
        setAuthToken(data.token);
        setIsAuthenticated(true);
        localStorage.setItem('adminToken', data.token);
        localStorage.setItem('adminEmail', data.email);
        
        // Play success sound
        playSuccessSound();
        
        // Load logs after successful login
        loadLogs(data.token);
        loadAdminLogs(data.token);
      } else {
        setError(data.error || 'Login failed');
        playErrorSound();
      }
    } catch (err) {
      setError('Connection error: ' + err.message);
      playErrorSound();
    } finally {
      setLoading(false);
    }
  };

  // Load session logs
  const loadLogs = async (token = authToken) => {
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/session-logs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      
      if (data.success) {
        setLogs(data.logs || []);
      } else {
        setError('Failed to load session logs: ' + data.error);
      }
    } catch (err) {
      setError('Error loading logs: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load admin logs
  const loadAdminLogs = async (token = authToken) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/admin/logs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      
      if (data.success) {
        setAdminLogs(data.logs || []);
      } else {
        setError('Failed to load admin logs: ' + data.error);
      }
    } catch (err) {
      setError('Error loading admin logs: ' + err.message);
    }
  };

  // Check for existing token on component mount
  useEffect(() => {
    const savedToken = localStorage.getItem('adminToken');
    const savedEmail = localStorage.getItem('adminEmail');
    
    if (savedToken && savedEmail) {
      setAuthToken(savedToken);
      setIsAuthenticated(true);
      setLoginData({ ...loginData, email: savedEmail });
      
      // Load logs with saved token
      loadLogs(savedToken);
      loadAdminLogs(savedToken);
    }
  }, []);

  // Logout function
  const handleLogout = () => {
    setIsAuthenticated(false);
    setAuthToken('');
    setLogs([]);
    setAdminLogs([]);
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminEmail');
  };

  // Refresh logs
  const refreshLogs = () => {
    loadLogs();
    loadAdminLogs();
  };

  // Login form
  if (!isAuthenticated) {
    return (
      <div className="admin-login-container">
        <div className="admin-login-card">
          <h2>🔒 Admin Login</h2>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Email:</label>
              <input
                type="email"
                value={loginData.email}
                onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Password:</label>
              <input
                type="password"
                value={loginData.password}
                onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                required
                disabled={loading}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <SoundButton type="submit" disabled={loading} soundType="success">
              {loading ? 'Logging in...' : 'Login'}
            </SoundButton>
          </form>
        </div>
      </div>
    );
  }

  // Main admin dashboard
  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>🛡️ SoulBridge AI Admin Dashboard</h1>
        <div className="admin-controls">
          <span>Welcome, {localStorage.getItem('adminEmail')}</span>
          <SoundButton onClick={refreshLogs} disabled={loading}>
            🔄 Refresh Logs
          </SoundButton>
          <SoundButton onClick={handleLogout} className="logout-btn" soundType="error">
            🚪 Logout
          </SoundButton>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="dashboard-grid">
        {/* Session/Chat Logs */}
        <div className="log-section">
          <h2>💬 User Chat Logs ({logs.length})</h2>
          <div className="log-container">
            {loading ? (
              <div className="loading">Loading logs...</div>
            ) : logs.length === 0 ? (
              <div className="no-logs">No chat logs found</div>
            ) : (
              logs.map((log, index) => (
                <div key={log.id || index} className="log-entry chat-log">
                  <div className="log-header">
                    <strong>👤 {log.userEmail || 'Anonymous'}</strong>
                    <span className="log-time">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="log-content">
                    <div className="user-message">
                      <strong>User:</strong> {log.userMessage}
                    </div>
                    <div className="ai-response">
                      <strong>AI ({log.companion || 'Blayzo'}):</strong> {log.aiResponse}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Admin Activity Logs */}
        <div className="log-section">
          <h2>⚡ Admin Activity Logs ({adminLogs.length})</h2>
          <div className="log-container">
            {adminLogs.length === 0 ? (
              <div className="no-logs">No admin activity logs found</div>
            ) : (
              adminLogs.map((log, index) => (
                <div key={log.id || index} className="log-entry admin-log">
                  <div className="log-header">
                    <strong>🔧 {log.admin_email || 'Admin'}</strong>
                    <span className={`log-type ${log.type}`}>{log.type}</span>
                    <span className="log-time">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="log-content">
                    {log.message}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="stats-section">
        <div className="stat-card">
          <h3>📊 Quick Stats</h3>
          <p>Total Chat Sessions: <strong>{logs.length}</strong></p>
          <p>Admin Actions: <strong>{adminLogs.length}</strong></p>
          <p>Last Updated: <strong>{new Date().toLocaleString()}</strong></p>
        </div>
      </div>
    </div>
  );
}