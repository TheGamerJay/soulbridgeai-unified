import React from 'react';
const logo = '/logo.jpg';

export default function Intro({ onNext }) {
  const handleStartClick = (e) => {
    e.preventDefault();
    console.log('Start button clicked');
    if (onNext && typeof onNext === 'function') {
      onNext();
    } else {
      console.error('onNext is not a function');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleStartClick(e);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8 bg-gradient-to-b from-gray-900 to-black">
      <div className="w-full max-w-lg flex flex-col items-center">
        <div className="flex flex-col items-center mb-6">
          <img
            src="/logos/Blayzo_premium.png"
            alt="Blayzo Premium AI Chat"
            style={{ width: '180px', height: '180px', borderRadius: '50%', boxShadow: '0 2px 32px #00e6ff44', border: '4px solid #00e6ff' }}
            className="object-cover object-center mb-3"
          />
          <span className="text-cyan-300 font-bold text-lg">Blayzo_premium</span>
          <span className="text-green-400 font-semibold text-sm mt-1">Online and ready to chat</span>
        </div>
        <h1 className="text-4xl font-extrabold mb-8 text-cyan-400 drop-shadow-lg text-center animate-pulse">
          Welcome to SoulBridgeAI
        </h1>
        <button
          onClick={handleStartClick}
          onKeyDown={handleKeyPress}
          className="mt-6 px-12 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-bold shadow-2xl hover:from-cyan-400 hover:to-blue-400 transform hover:scale-105 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-cyan-300 active:scale-95"
          tabIndex={0}
          role="button"
          aria-label="Start your SoulBridge AI journey"
        >
          🚀 Start Your Journey
        </button>
        <p className="mt-4 text-cyan-300 text-center text-sm opacity-75">
          Click to begin your AI companion experience
        </p>
      </div>
    </div>
  );
}
