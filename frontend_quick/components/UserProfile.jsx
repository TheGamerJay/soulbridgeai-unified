import React, { useState, useEffect } from 'react';

const UserProfile = () => {
  const [user, setUser] = useState(null);
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalMessages: 0,
    totalSessions: 0,
    daysActive: 0
  });

  const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://soulbridgeai.com/api';

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      // Use fallback authentication check only
      const sessionUser = sessionStorage.getItem('soulbridge_user');
      if (sessionUser) {
        const userData = JSON.parse(sessionUser);
        setUser(userData);
        await loadUserProfile(userData.uid || 'dev-user');
      } else {
        redirectToLogin();
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
      redirectToLogin();
    }
  };

  const loadUserProfile = async (userId) => {
    try {
      setLoading(true);
      
      // Try to load user data from API
      const response = await fetch(`${apiBaseUrl}/users/${userId}`);
      
      if (response.ok) {
        const result = await response.json();
        const userInfo = result.user;
        setUserData(userInfo);
        
        // Calculate statistics
        const messageCount = userInfo.chatHistory ? userInfo.chatHistory.length : 0;
        const sessionCount = Math.ceil(messageCount / 10) || 1;
        const daysSinceCreation = userInfo.createdDate ? 
          Math.ceil((Date.now() - new Date(userInfo.createdDate)) / (1000 * 60 * 60 * 24)) : 1;
        
        setStats({
          totalMessages: messageCount,
          totalSessions: sessionCount,
          daysActive: daysSinceCreation
        });
      } else {
        // If user not found in API, create a basic profile
        await createUserProfile(userId);
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const createUserProfile = async (userId) => {
    try {
      const response = await fetch(`${apiBaseUrl}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: user?.email || 'anonymous@soulbridge.ai',
          companion: 'Blayzo'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setUserData(result.user);
      }
    } catch (error) {
      console.error('Failed to create user profile:', error);
    }
  };

  const downloadChatHistory = async () => {
    try {
      if (!userData || !userData.chatHistory || userData.chatHistory.length === 0) {
        alert('No chat history found to download.');
        return;
      }

      // Use API data only (Firebase disabled)

      // Fallback to API data
      const chatData = userData.chatHistory;
      const exportData = {
        exportDate: new Date().toISOString(),
        userID: userData.userID,
        email: userData.email,
        companion: userData.companion,
        totalMessages: chatData.length,
        chatHistory: chatData
      };

      downloadFile(exportData, 'my_chat_history.json');
      
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download chat history. Please try again.');
    }
  };

  const downloadFile = (data, filename) => {
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  const exportAllUserData = async () => {
    try {
      if (!userData) {
        alert('No user data available to export.');
        return;
      }

      const exportData = {
        exportDate: new Date().toISOString(),
        userProfile: userData,
        statistics: stats,
        settings: userData.settings || {},
        source: 'SoulBridge AI Profile Export'
      };

      downloadFile(exportData, `soulbridge_profile_${userData.userID}_${Date.now()}.json`);
      
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export user data. Please try again.');
    }
  };

  const clearChatHistory = async () => {
    if (!window.confirm('Are you sure you want to clear your chat history? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/users/${userData.userID}/chat`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // Update local state
        setUserData(prev => ({ ...prev, chatHistory: [] }));
        setStats(prev => ({ ...prev, totalMessages: 0, totalSessions: 1 }));
        alert('Chat history cleared successfully!');
        
        // Firebase clearing disabled
      } else {
        alert('Failed to clear chat history. Please try again.');
      }
    } catch (error) {
      console.error('Clear history failed:', error);
      alert('Failed to clear chat history. Please try again.');
    }
  };

  const redirectToLogin = () => {
    alert('Please log in to view your profile.');
    window.location.href = '/';
  };

  const goHome = () => {
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%)',
        color: '#22d3ee',
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
      }}>
        <div style={{
          fontSize: '1.5rem',
          textAlign: 'center'
        }}>
          Loading your profile...
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'linear-gradient(135deg, #000000 0%, #0f172a 50%, #1e293b 100%)',
      color: '#22d3ee',
      minHeight: '100vh',
      padding: '20px',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }}>
      {/* Back Button */}
      <button
        onClick={goHome}
        style={{
          position: 'fixed',
          top: '20px',
          left: '20px',
          background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
          color: '#000',
          padding: '12px 20px',
          borderRadius: '25px',
          border: 'none',
          fontWeight: 'bold',
          cursor: 'pointer',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        <span>←</span>
        <span>Back to Home</span>
      </button>

      <div style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '80px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{
            fontSize: '3rem',
            color: '#22d3ee',
            textShadow: '0 0 30px rgba(34, 211, 238, 0.8)',
            marginBottom: '0.5rem',
            fontWeight: '700'
          }}>My Profile</h1>
          <p style={{
            fontSize: '1.2rem',
            color: 'rgba(255, 255, 255, 0.7)',
            marginBottom: '2rem'
          }}>Manage your SoulBridge AI experience</p>
        </div>

        {/* Profile Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
          gap: '2rem',
          marginBottom: '2rem'
        }}>
          {/* User Information Panel */}
          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)',
            transition: 'all 0.4s ease'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>👤 User Information</h2>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.9rem',
                marginBottom: '0.25rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>User ID</div>
              <div style={{
                color: '#22d3ee',
                fontSize: '1.1rem',
                fontWeight: '600',
                marginBottom: '1rem',
                wordBreak: 'break-word'
              }}>{userData?.userID || user?.uid || 'Unknown'}</div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.9rem',
                marginBottom: '0.25rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>Email Address</div>
              <div style={{
                color: '#22d3ee',
                fontSize: '1.1rem',
                fontWeight: '600',
                marginBottom: '1rem',
                wordBreak: 'break-word'
              }}>{userData?.email || user?.email || 'Not provided'}</div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.9rem',
                marginBottom: '0.25rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>Account Created</div>
              <div style={{
                color: '#22d3ee',
                fontSize: '1.1rem',
                fontWeight: '600',
                marginBottom: '1rem'
              }}>
                {userData?.createdDate ? 
                  new Date(userData.createdDate).toLocaleDateString() : 
                  'Unknown'
                }
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{
                color: 'rgba(255, 255, 255, 0.7)',
                fontSize: '0.9rem',
                marginBottom: '0.25rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>Subscription Status</div>
              <div style={{
                display: 'inline-block',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '0.9rem',
                fontWeight: '600',
                marginTop: '0.5rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                background: userData?.subscriptionStatus === 'free' ? 'rgba(107, 114, 128, 0.3)' :
                           userData?.subscriptionStatus === 'plus' ? 'rgba(255, 215, 0, 0.3)' :
                           'rgba(147, 51, 234, 0.3)',
                color: userData?.subscriptionStatus === 'free' ? '#9ca3af' :
                       userData?.subscriptionStatus === 'plus' ? '#ffd700' :
                       '#9333ea',
                border: `1px solid ${
                  userData?.subscriptionStatus === 'free' ? 'rgba(156, 163, 175, 0.3)' :
                  userData?.subscriptionStatus === 'plus' ? 'rgba(255, 215, 0, 0.5)' :
                  'rgba(147, 51, 234, 0.5)'
                }`
              }}>
                {userData?.subscriptionStatus || 'Free'}
              </div>
            </div>

            {/* Statistics */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
              gap: '1rem',
              marginTop: '1rem'
            }}>
              {[
                { label: 'Messages', value: stats.totalMessages },
                { label: 'Sessions', value: stats.totalSessions },
                { label: 'Days Active', value: stats.daysActive }
              ].map((stat, index) => (
                <div key={index} style={{
                  textAlign: 'center',
                  padding: '1rem',
                  background: 'rgba(34, 211, 238, 0.1)',
                  borderRadius: '12px',
                  border: '1px solid rgba(34, 211, 238, 0.2)'
                }}>
                  <span style={{
                    fontSize: '1.8rem',
                    fontWeight: '700',
                    color: '#22d3ee',
                    display: 'block',
                    marginBottom: '0.25rem'
                  }}>{stat.value}</span>
                  <span style={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    fontSize: '0.8rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>{stat.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Current Companion Panel */}
          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)',
            transition: 'all 0.4s ease'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>🤖 Current Companion</h2>
            
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '1rem',
              background: 'rgba(34, 211, 238, 0.1)',
              borderRadius: '12px',
              margin: '1rem 0'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                fontWeight: 'bold',
                color: '#000'
              }}>
                {userData?.companion?.charAt(0) || 'B'}
              </div>
              <div>
                <h3 style={{
                  color: '#22d3ee',
                  margin: '0 0 0.25rem 0',
                  fontSize: '1.2rem'
                }}>{userData?.companion || 'Blayzo'}</h3>
                <p style={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  margin: '0',
                  fontSize: '0.9rem'
                }}>
                  {userData?.companion === 'Blayzo' ? 'Wise and calm mentor' :
                   userData?.companion === 'Blayzica' ? 'Energetic and empathetic assistant' :
                   userData?.companion === 'Blayzion' ? 'Mystical cosmic guide' :
                   userData?.companion === 'Blayzia' ? 'Radiant healing energy' :
                   userData?.companion === 'Violet' ? 'Mystical spiritual guide' :
                   userData?.companion === 'Crimson' ? 'Fierce protective warrior' :
                   'Your AI companion'}
                </p>
              </div>
            </div>

            <button
              onClick={goHome}
              style={{
                width: '100%',
                padding: '12px 20px',
                margin: '8px 0',
                background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
                color: '#000',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              🔄 Change Companion
            </button>
          </div>

          {/* Data Management Panel */}
          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)',
            transition: 'all 0.4s ease'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>📁 Data Management</h2>
            
            <button
              onClick={downloadChatHistory}
              style={{
                width: '100%',
                padding: '12px 20px',
                margin: '8px 0',
                background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
                color: '#000',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              📥 Download Chat History
            </button>

            <button
              onClick={exportAllUserData}
              style={{
                width: '100%',
                padding: '12px 20px',
                margin: '8px 0',
                background: 'linear-gradient(135deg, #6b7280, #4b5563)',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              📦 Export All Data
            </button>

            <button
              onClick={clearChatHistory}
              style={{
                width: '100%',
                padding: '12px 20px',
                margin: '8px 0',
                background: 'linear-gradient(135deg, #6b7280, #4b5563)',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              🗑️ Clear Chat History
            </button>
          </div>

          {/* Support Panel */}
          <div style={{
            background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '20px',
            padding: '2rem',
            backdropFilter: 'blur(20px)',
            transition: 'all 0.4s ease'
          }}>
            <h2 style={{
              color: '#22d3ee',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>🆘 Support</h2>
            
            <button
              onClick={() => window.location.href = 'mailto:dagamerjay13@gmail.com?subject=SoulBridge AI Support'}
              style={{
                width: '100%',
                padding: '12px 20px',
                margin: '8px 0',
                background: 'linear-gradient(135deg, #6b7280, #4b5563)',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              📧 Contact Support
            </button>

            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              background: 'rgba(34, 211, 238, 0.1)',
              borderRadius: '8px'
            }}>
              <div style={{
                color: '#22d3ee',
                fontWeight: '600',
                marginBottom: '0.5rem'
              }}>Support Email</div>
              <div style={{
                color: 'rgba(255, 255, 255, 0.9)'
              }}>dagamerjay13@gmail.com</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;