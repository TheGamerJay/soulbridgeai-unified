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
        <img
          src={logo}
          alt="SoulBridgeAI Logo"
          style={{ width: '350px', height: '350px' }}
          className="mb-6 rounded-full shadow-2xl border-4 border-cyan-400 object-cover object-center hover:border-cyan-300 transition-all duration-300 transform hover:scale-105"
        />
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
