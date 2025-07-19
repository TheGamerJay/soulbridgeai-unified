import React from 'react';
const logo = '/logo.jpg';

export default function Intro({ onNext }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8">
      <div className="w-full max-w-lg flex flex-col items-center">
        <img
          src={logo}
          alt="SoulBridgeAI Logo"
          style={{ width: '550px', height: '450px' }}
          className="mb-6 rounded-full shadow-lg border-4 border-cyan-400 object-cover object-center"
        />
        <h1 className="text-3xl font-extrabold mb-6 text-cyan-400 drop-shadow-lg text-center">
          Welcome to SoulBridgeAI
        </h1>
        <button
          onClick={onNext}
          className="mt-6 px-8 py-3 rounded-xl bg-cyan-500 text-black font-bold shadow-lg hover:bg-cyan-400 transition"
        >
          Start
        </button>
      </div>
    </div>
  );
}
