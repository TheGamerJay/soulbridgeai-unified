import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Intro from './components/Intro';
import CharacterSelect from './components/CharacterSelect';
import ChatScreen from './components/ChatScreen';
import AdminLogin from './components/AdminLogin';
import UserProfile from './components/UserProfile';

function MainApp() {
  const [step, setStep] = useState(1);
  const [character, setCharacter] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  const handleSelectCharacter = (selected) => {
    setCharacter(selected);
    setStep(3);
  };

  return (
    <div
      style={{
        backgroundColor: darkMode ? "#000" : "#fff",
        color: "#22d3ee",
        minHeight: "100vh",
        width: "100%",
        transition: "background-color 0.3s, color 0.3s"
      }}
    >
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {/* Navigation and controls */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          width: '100%',
          padding: '1.5rem',
          position: 'fixed',
          top: 0,
          zIndex: 100,
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)'
        }}>
          {/* Back button on the left */}
          {step > 1 && (
            <button
              onClick={() => setStep(step - 1)}
              style={{
                padding: '12px 24px',
                borderRadius: '25px',
                background: 'linear-gradient(135deg, #374151, #1f2937)',
                color: '#fff',
                border: 'none',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                fontSize: '1rem'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(55, 65, 81, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
            >
              🔙 Back
            </button>
          )}
          {/* Night mode switch on the right */}
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            marginLeft: 'auto'
          }}>
            <span style={{
              marginRight: '12px',
              fontWeight: '600',
              color: step === 3 && character === "Blayzo"
                ? "#4169e1"
                : step === 3 && character === "Blayzica"
                ? "#ff1a1a"
                : "#22d3ee"
            }}>
              {darkMode ? "🌙 Night Mode" : "☀️ Day Mode"}
            </span>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
              style={{
                width: '20px',
                height: '20px',
                accentColor: '#22d3ee'
              }}
            />
          </label>
        </div>

        {/* Conditional rendering for steps */}
        {step === 1 && <Intro onNext={() => setStep(2)} />}
        {step === 2 && <CharacterSelect onSelect={handleSelectCharacter} />}
        {step === 3 && <ChatScreen character={character} />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/user-profile" element={<UserProfile />} />
      </Routes>
    </Router>
  );
}