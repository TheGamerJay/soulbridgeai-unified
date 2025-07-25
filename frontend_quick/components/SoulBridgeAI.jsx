import React from "react";

export default function SoulBridgeAI({ character }) {
  let greeting = "";
  let emoji = "";

  if (character === "Blayzo") {
    greeting = "Hey, I'm Blayzo – your SoulBridge companion. I got you, no matter what's on your mind. Let's talk.";
    emoji = "💬";
  } else if (character === "Blayzica") {
    greeting = "Hi! I'm Blayzica – your SoulBridge personal assistant. I'm here for your thoughts, feelings or just to vibe.";
    emoji = "💖";
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <h1 className="text-xl font-bold text-cyan-400 mb-2">SoulBridgeAI Chat</h1>
      <p className="text-cyan-300 mb-2">{greeting} <span className="text-2xl">{emoji}</span></p>
      <p className="text-cyan-300">Selected Character: {character}</p>
    </div>
  );
}
