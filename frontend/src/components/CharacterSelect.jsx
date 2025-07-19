import React from 'react';

export default function CharacterSelect({ onSelect }) {
  const companions = [
    {
      name: 'Blayzo',
      image: '/Blayzo.png',
      description: 'Wise and calm mentor',
      color: '#4169e1'
    },
    {
      name: 'Blayzica',
      image: '/Blayzica.png', 
      description: 'Energetic and empathetic assistant',
      color: '#ff1a1a'
    }
  ];

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
      <h1 style={{
        fontSize: '3rem',
        fontWeight: '700',
        marginBottom: '3rem',
        color: '#22d3ee',
        textShadow: '0 0 30px rgba(34, 211, 238, 0.8)',
        textAlign: 'center'
      }}>
        Choose Your AI Companion
      </h1>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '2rem',
        maxWidth: '800px',
        width: '100%'
      }}>
        {companions.map((companion) => (
          <div
            key={companion.name}
            onClick={() => onSelect(companion.name)}
            style={{
              background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
              border: `2px solid ${companion.color}`,
              borderRadius: '20px',
              padding: '2rem',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              backdropFilter: 'blur(20px)',
              boxShadow: `0 8px 32px ${companion.color}40`
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-10px)';
              e.target.style.boxShadow = `0 16px 40px ${companion.color}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 8px 32px ${companion.color}40`;
            }}
          >
            <img
              src={companion.image}
              alt={companion.name}
              style={{
                width: '150px',
                height: '150px',
                borderRadius: '50%',
                marginBottom: '1.5rem',
                border: `3px solid ${companion.color}`,
                objectFit: 'cover'
              }}
            />
            <h2 style={{
              fontSize: '2rem',
              fontWeight: '600',
              color: companion.color,
              marginBottom: '1rem'
            }}>
              {companion.name}
            </h2>
            <p style={{
              fontSize: '1.1rem',
              color: 'rgba(255, 255, 255, 0.8)',
              marginBottom: '1.5rem'
            }}>
              {companion.description}
            </p>
            <button
              style={{
                padding: '12px 30px',
                fontSize: '1.1rem',
                fontWeight: '600',
                background: `linear-gradient(135deg, ${companion.color}, ${companion.color}cc)`,
                color: '#fff',
                border: 'none',
                borderRadius: '25px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                textTransform: 'uppercase',
                letterSpacing: '1px'
              }}
            >
              Choose {companion.name}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}