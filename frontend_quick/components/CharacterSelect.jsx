import React from 'react';

export default function CharacterSelect({ onSelect }) {
  return (
    <div className="flex flex-col items-center justify-center">
      <h1 className="text-3xl font-bold mb-6 text-cyan-400">Select Your Character</h1>
      <button
        onClick={() => onSelect('Blayzo')}
        className="mt-4 px-8 py-3 rounded-xl bg-cyan-500 text-black font-bold shadow-lg hover:bg-cyan-400 transition"
      >
        Blayzo
      </button>
      <button
        onClick={() => onSelect('Blayzica')}
        className="mt-4 px-8 py-3 rounded-xl bg-cyan-500 text-black font-bold shadow-lg hover:bg-cyan-400 transition"
      >
        Blayzica
      </button>
    </div>
  );
}
