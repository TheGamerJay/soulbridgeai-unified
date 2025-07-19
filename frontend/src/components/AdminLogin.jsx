import { useState } from "react";
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
import app from "../firebase-config.js";

const auth = getAuth(app);

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const devEmail = "GamerJay@gmail.com";
  const devPassword = "Yariel13"; // Fixed typo from "Variel13"

  async function handleLogin() {
    if (!email || !password) {
      setMessage("Please enter both email and password");
      return;
    }

    setIsLoading(true);
    setMessage("Logging in...");

    try {
      // First try Firebase login
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      setMessage("Firebase Login Successful - Redirecting...");
      console.log("Firebase login:", userCredential.user);
      
      // Store session and redirect
      sessionStorage.setItem('soulbridge_admin', JSON.stringify({
        email: userCredential.user.email,
        uid: userCredential.user.uid,
        loginTime: new Date().toISOString(),
        isFirebase: true
      }));
      
      setTimeout(() => {
        window.location.href = '/admin';
      }, 1000);

    } catch (error) {
      console.log("Firebase login failed, trying dev credentials...", error);
      
      // Fallback to static dev login
      if (email === devEmail && password === devPassword) {
        setMessage("Dev Login Successful - Redirecting...");
        console.log("Dev login successful");
        
        // Store dev session and redirect
        sessionStorage.setItem('soulbridge_admin', JSON.stringify({
          email: email,
          uid: 'dev-admin',
          loginTime: new Date().toISOString(),
          isDev: true
        }));
        
        setTimeout(() => {
          window.location.href = '/admin';
        }, 1000);
      } else {
        setMessage(`Invalid Login - ${error.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div style={{
      background: 'radial-gradient(circle, #0f2027, #203a43, #2c5364)',
      color: '#22d3ee',
      minHeight: '100vh',
      padding: '20px',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      {/* Back Button */}
      <button
        onClick={() => window.location.href = '/'}
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
          fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        }}
      >
        ← Back
      </button>

      <div style={{
        background: 'rgba(0, 0, 0, 0.7)',
        padding: '40px',
        borderRadius: '20px',
        border: '2px solid #22d3ee',
        boxShadow: '0 0 50px #22d3ee',
        width: '100%',
        maxWidth: '450px',
        textAlign: 'center',
        backdropFilter: 'blur(20px)'
      }}>
        <h1 style={{
          fontSize: '3rem',
          marginBottom: '10px',
          color: '#22d3ee',
          textShadow: '0 0 30px rgba(34, 211, 238, 0.8)',
          fontWeight: '700'
        }}>
          SoulBridge AI
        </h1>
        
        <h2 style={{
          fontSize: '1.2rem',
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '40px',
          fontWeight: 'normal'
        }}>
          Admin Login
        </h2>
        
        <input
          type="email"
          placeholder="Admin Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '15px 20px',
            margin: '10px 0',
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#22d3ee',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '12px',
            fontSize: '1.1rem',
            boxSizing: 'border-box',
            transition: 'all 0.3s ease',
            outline: 'none'
          }}
          onFocus={(e) => e.target.style.borderColor = '#22d3ee'}
          onBlur={(e) => e.target.style.borderColor = 'rgba(34, 211, 238, 0.3)'}
        />
        
        <input
          type="password"
          placeholder="Admin Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '15px 20px',
            margin: '10px 0',
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#22d3ee',
            border: '2px solid rgba(34, 211, 238, 0.3)',
            borderRadius: '12px',
            fontSize: '1.1rem',
            boxSizing: 'border-box',
            transition: 'all 0.3s ease',
            outline: 'none'
          }}
          onFocus={(e) => e.target.style.borderColor = '#22d3ee'}
          onBlur={(e) => e.target.style.borderColor = 'rgba(34, 211, 238, 0.3)'}
        />
        
        <button
          onClick={handleLogin}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '15px 25px',
            margin: '20px 0',
            background: isLoading ? 
              'linear-gradient(135deg, #6b7280, #4b5563)' : 
              'linear-gradient(135deg, #22d3ee, #0891b2)',
            color: '#000',
            border: 'none',
            borderRadius: '12px',
            fontWeight: '700',
            fontSize: '1.1rem',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            opacity: isLoading ? 0.7 : 1
          }}
          onMouseEnter={(e) => {
            if (!isLoading) {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 8px 25px rgba(34, 211, 238, 0.5)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isLoading) {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = 'none';
            }
          }}
        >
          {isLoading ? 'Logging in...' : 'Login to Dashboard'}
        </button>
        
        {message && (
          <div style={{
            background: message.includes('Successful') ? 'rgba(34, 197, 94, 0.1)' : 
                       message.includes('Invalid') ? 'rgba(239, 68, 68, 0.1)' : 
                       'rgba(34, 211, 238, 0.1)',
            borderLeft: `4px solid ${
              message.includes('Successful') ? '#22c55e' : 
              message.includes('Invalid') ? '#ef4444' : 
              '#22d3ee'
            }`,
            padding: '15px',
            margin: '15px 0',
            borderRadius: '0 8px 8px 0',
            fontFamily: "'Courier New', monospace",
            fontSize: '0.95rem',
            textAlign: 'left'
          }}>
            {message}
          </div>
        )}
        
        <div style={{
          marginTop: '25px',
          padding: '15px',
          background: 'rgba(34, 211, 238, 0.1)',
          borderRadius: '8px',
          border: '1px solid rgba(34, 211, 238, 0.2)'
        }}>
          <div style={{
            color: '#22d3ee',
            fontWeight: '600',
            marginBottom: '5px',
            fontSize: '0.9rem'
          }}>
            Development Credentials
          </div>
          <div style={{
            color: 'rgba(255, 255, 255, 0.8)',
            fontSize: '0.85rem',
            fontFamily: "'Courier New', monospace"
          }}>
            GamerJay@gmail.com / Yariel13
          </div>
        </div>
      </div>
    </div>
  );
}