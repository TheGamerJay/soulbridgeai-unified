import React from 'react';

export default function CharacterSelect({ onSelect }) {
  const handleCharacterSelect = (character) => {
    console.log(`${character} selected`);
    if (onSelect && typeof onSelect === 'function') {
      onSelect(character);
    } else {
      console.error('onSelect is not a function');
    }
  };

  const handleKeyPress = (e, character) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCharacterSelect(character);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8 bg-gradient-to-b from-gray-900 to-black">
      <h1 className="text-4xl font-bold mb-8 text-cyan-400 drop-shadow-lg text-center">
        Choose Your AI Companion
      </h1>
      <p className="text-cyan-300 mb-8 text-center max-w-md">
        Select the companion that resonates with you
      </p>
      
      <div className="flex flex-col sm:flex-row gap-6 items-center">
        <button
          onClick={() => handleCharacterSelect('Blayzo')}
          onKeyDown={(e) => handleKeyPress(e, 'Blayzo')}
          className="px-10 py-4 rounded-xl bg-gradient-to-r from-blue-600 to-blue-800 text-white font-bold shadow-2xl hover:from-blue-500 hover:to-blue-700 transform hover:scale-105 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-300 active:scale-95 min-w-[150px]"
          tabIndex={0}
          role="button"
          aria-label="Select Blayzo as your AI companion"
        >
          💪 Blayzo
        </button>
        
        <div className="text-cyan-400 font-bold text-xl">OR</div>
        
        <button
          onClick={() => handleCharacterSelect('Blayzica')}
          onKeyDown={(e) => handleKeyPress(e, 'Blayzica')}
          className="px-10 py-4 rounded-xl bg-gradient-to-r from-pink-600 to-red-600 text-white font-bold shadow-2xl hover:from-pink-500 hover:to-red-500 transform hover:scale-105 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-pink-300 active:scale-95 min-w-[150px]"
          tabIndex={0}
          role="button"
          aria-label="Select Blayzica as your AI companion"
        >
          💖 Blayzica
        </button>
      </div>
      
      <div className="mt-8 text-cyan-300 text-center text-sm opacity-75 max-w-lg">
        <p>💪 <strong>Blayzo:</strong> Your supportive companion for deep conversations</p>
        <p className="mt-2">💖 <strong>Blayzica:</strong> Your caring assistant for thoughts and feelings</p>
      </div>
    </div>
  );
}
