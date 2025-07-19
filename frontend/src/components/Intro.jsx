import React from 'react';

export default function Intro({ onNext }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }}>
      <div style={{
        width: '100%',
        maxWidth: '600px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center'
      }}>
        <img
          src="/IntroLogo.png"
          alt="SoulBridgeAI Logo"
          style={{ 
            width: '400px', 
            height: '400px',
            marginBottom: '2rem',
            borderRadius: '50%',
            boxShadow: '0 0 50px rgba(34, 211, 238, 0.5)',
            border: '4px solid #22d3ee',
            objectFit: 'cover'
          }}
        />
        <h1 style={{
          fontSize: '3rem',
          fontWeight: '700',
          marginBottom: '1rem',
          color: '#22d3ee',
          textShadow: '0 0 30px rgba(34, 211, 238, 0.8)',
          background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          Welcome to SoulBridgeAI
        </h1>
        <p style={{
          fontSize: '1.2rem',
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '3rem',
          lineHeight: '1.6'
        }}>
          Your AI companion platform for meaningful conversations and emotional support
        </p>
        <button
          onClick={onNext}
          style={{
            padding: '15px 40px',
            fontSize: '1.2rem',
            fontWeight: '600',
            background: 'linear-gradient(135deg, #22d3ee, #0891b2)',
            color: '#000',
            border: 'none',
            borderRadius: '50px',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 8px 25px rgba(34, 211, 238, 0.3)',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'translateY(-3px)';
            e.target.style.boxShadow = '0 12px 35px rgba(34, 211, 238, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = '0 8px 25px rgba(34, 211, 238, 0.3)';
          }}
        >
          Begin Your Journey
        </button>
      </div>
    </div>
  );
}