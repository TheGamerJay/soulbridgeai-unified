import React, { useState, useEffect } from 'react';

const AdminDashboard = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [loginStatus, setLoginStatus] = useState('');
  const [logs, setLogs] = useState([]);

  const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://soulbridgeai.com/api';

  useEffect(() => {
    // Check if user is authenticated on component mount
    const adminSession = sessionStorage.getItem('soulbridge_admin');
    if (adminSession) {
      const session = JSON.parse(adminSession);
      setCurrentUser(session);
      setIsLoggedIn(true);
      log('Existing admin session found: ' + session.email, 'success');
    }
  }, []);

  const log = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { timestamp, message, type };
    setLogs(prev => [...prev.slice(-99), logEntry]);
  };

  const adminLogin = async () => {
    if (!adminEmail || !adminPassword) {
      setLoginStatus('Please enter both email and password');
      return;
    }

    try {
      setLoginStatus('Logging in...');
      
      const devCredentials = {
        email: 'GamerJay@gmail.com',
        password: 'Yariel13'
      };
      
      if (adminEmail === devCredentials.email && adminPassword === devCredentials.password) {
        setCurrentUser({ email: adminEmail, uid: 'dev-admin' });
        setIsLoggedIn(true);
        log('Dev Admin logged in: ' + adminEmail, 'success');
        setLoginStatus('');
        return;
      }
      
      setLoginStatus('Invalid credentials or access denied.');
    } catch (error) {
      setLoginStatus('Login failed: ' + error.message);
      log('Admin login failed: ' + error.message, 'error');
    }
  };

  if (!isLoggedIn) {
    return (
      <div style={{
        background: 'radial-gradient(circle, #0f2027, #203a43, #2c5364)',
        color: '#22d3ee',
        minHeight: '100vh',
        padding: '20px',
        fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => { window.location.href = '/admin-login'; }}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            padding: '10px 15px',
            border: '1px solid #22d3ee',
            background: 'rgba(0, 255, 255, 0.1)',
            borderRadius: '20px',
            color: '#22d3ee',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
          }}
        >
          ← Back to Login
        </button>

        <div style={{
          background: 'rgba(0, 0, 0, 0.7)',
          padding: '30px',
          borderRadius: '10px',
          border: '1px solid #22d3ee',
          boxShadow: '0 0 30px #22d3ee',
          width: '90%',
          maxWidth: '400px',
          textAlign: 'center'
        }}>
          <h1 style={{
            fontSize: '2em',
            marginBottom: '5px',
            color: '#22d3ee'
          }}>SoulBridge AI</h1>
          
          <h2 style={{
            fontSize: '1em',
            color: 'rgba(255, 255, 255, 0.8)',
            marginBottom: '30px',
            fontWeight: 'normal'
          }}>Admin Login</h2>
            
          <input
            type="email"
            value={adminEmail}
            onChange={(e) => setAdminEmail(e.target.value)}
            placeholder="Admin Email Address"
            style={{
              width: '100%',
              padding: '12px 16px',
              margin: '8px 0',
              background: 'rgba(0, 0, 0, 0.8)',
              color: '#22d3ee',
              border: '2px solid rgba(34, 211, 238, 0.3)',
              borderRadius: '10px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
          />
          
          <input
            type="password"
            value={adminPassword}
            onChange={(e) => setAdminPassword(e.target.value)}
            placeholder="Admin Password"
            style={{
              width: '100%',
              padding: '12px 16px',
              margin: '8px 0',
              background: 'rgba(0, 0, 0, 0.8)',
              color: '#22d3ee',
              border: '2px solid rgba(34, 211, 238, 0.3)',
              borderRadius: '10px',
              fontSize: '1rem',
              boxSizing: 'border-box'
            }}
            onKeyPress={(e) => e.key === 'Enter' && adminLogin()}
          />
          
          <button
            onClick={adminLogin}
            style={{
              width: '100%',
              padding: '12px 20px',
              margin: '8px 0',
              background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
              color: '#000',
              border: 'none',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '1rem',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          >
            Login to Dashboard
          </button>
          
          {loginStatus && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.6)',
              borderLeft: '4px solid #22d3ee',
              padding: '1rem',
              margin: '0.5rem 0',
              borderRadius: '0 8px 8px 0',
              fontFamily: 'Courier New, monospace',
              fontSize: '0.9rem',
              marginTop: '1rem'
            }}>
              {loginStatus}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'radial-gradient(circle, #0f2027, #203a43, #2c5364)',
      color: '#22d3ee',
      minHeight: '100vh',
      padding: '20px',
      fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{
            fontSize: '3rem',
            color: '#22d3ee',
            textShadow: '0 0 30px rgba(34, 211, 238, 0.8)',
            marginBottom: '0.5rem',
            fontWeight: '700'
          }}>SoulBridge AI</h1>
          <p style={{
            fontSize: '1.2rem',
            color: 'rgba(255, 255, 255, 0.7)',
            marginBottom: '2rem'
          }}>Admin Dashboard & Management Console</p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '2rem',
          marginBottom: '2rem'
        }}>
          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>👥 User Management</h2>
            
            <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
              Admin dashboard functionality is working. 
              Use the credentials: GamerJay@gmail.com / Yariel13
            </p>
          </div>

          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>📊 Activity Logs</h2>
            
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {logs.map((logEntry, index) => (
                <div key={index} style={{
                  background: 'rgba(0, 0, 0, 0.6)',
                  borderLeft: '4px solid ' + (logEntry.type === 'error' ? '#ef4444' : logEntry.type === 'warning' ? '#f59e0b' : logEntry.type === 'success' ? '#22c55e' : '#22d3ee'),
                  padding: '1rem',
                  margin: '0.5rem 0',
                  borderRadius: '0 8px 8px 0',
                  fontFamily: 'Courier New, monospace',
                  fontSize: '0.9rem'
                }}>
                  [{logEntry.timestamp}] {logEntry.message}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;