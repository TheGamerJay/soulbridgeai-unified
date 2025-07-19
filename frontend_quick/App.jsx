import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import IntroScreen from './components/Intro';
import CharacterSelect from './components/CharacterSelect';
import SoulBridgeAI from './components/ChatScreen';
import AdminDashboard from './components/AdminDashboard';
import AdminLogin from './components/AdminLogin';
import UserProfile from './components/UserProfile';

function MainApp() {
  const [step, setStep] = useState(1);
  const [character, setCharacter] = useState("");
  const [darkMode, setDarkMode] = useState(true);
  const [message, setMessage] = useState(""); // Add message state
  const [chat, setChat] = useState([]); // Add chat history

  const handleSelectCharacter = (selected) => {
    setCharacter(selected);
    setStep(3);
  };

  // Function to send message to backend
  const handleSend = async () => {
    if (!message.trim()) return;
    // Add user's message to chat
    setChat([...chat, { sender: "user", text: message }]);
    try {
      const BASE_URL = import.meta.env.VITE_API_URL;
      const response = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, character }),
      });
      const data = await response.json();
      // Add AI response to chat
      setChat([...chat, { sender: "user", text: message }, { sender: "ai", text: data.reply }]);
    } catch (err) {
      // Handle error (optional)
      setChat([...chat, { sender: "user", text: message }, { sender: "ai", text: "Sorry, something went wrong." }]);
    }
    setMessage(""); // Clear input
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
      <div className="flex flex-col min-h-screen items-center justify-center">
        {/* 1. Night mode switch */}
        <div className="flex justify-between w-full p-6">
          {/* Back button on the left */}
          {step > 1 && (
            <button
              className="px-6 py-2 rounded-lg bg-black text-white font-bold shadow hover:bg-gray-800 transition"
              onClick={() => setStep(step - 1)}
            >
              🔙
            </button>
          )}
          {/* Night mode switch on the right */}
          <label className="flex items-center cursor-pointer ml-auto">
            <span
              className="mr-2 font-semibold"
              style={{
                color: step === 3 && character === "Blayzo"
                  ? "#4169e1"
                  : step === 3 && character === "Blayzica"
                  ? "#ff1a1a"
                  : "#22d3ee"
              }}
            >
              {darkMode ? "🌙 Night Mode" : "☀️ Day Mode"}
            </span>
            <input
              type="checkbox"
              checked={darkMode}
              onChange={() => setDarkMode(!darkMode)}
              className="form-checkbox h-5 w-5 accent-cyan-600"
            />
          </label>
        </div>

        {/* 2. Night mode status */}
        <div
          className="font-bold mb-4"
          style={{
            fontSize: "1.125rem",
            color: step === 3 && character === "BlayZo"
              ? "#4169e1"
              : step === 3 && character === "Blayzica"
              ? "#ff1a1a"
              : undefined
          }}
        >
          {darkMode
            ? step === 3 && character === "Blayzo"
              ? <span style={{ color: "#4169e1" }}>Night Mode is ON</span>
              : step === 3 && character === "Blayzica"
              ? <span style={{ color: "#ff1a1a" }}>Night Mode is ON</span>
              : "Night Mode is ON"
            : step === 3 && character === "Blayzo"
              ? <span style={{ color: "#4169e1" }}>Day Mode is ON</span>
              : step === 3 && character === "Blayzica"
              ? <span style={{ color: "#ff1a1a" }}>Day Mode is ON</span>
              : "Day Mode is ON"}
        </div>

        {/* Conditional rendering for steps */}
        {step === 1 && <IntroScreen onNext={() => setStep(2)} />}
        {step === 2 && <CharacterSelect onSelect={handleSelectCharacter} />}
        {step === 3 && character === "Blayzo" && (
          <>
            {/* Selected Character */}
            <p className="text-lg mb-[6rem]" style={{ color: "#4169e1" }}>
              Selected Character: <span className="font-bold">Blayzo</span>
            </p>
            {/* Blayzo is ready to chat */}
            <h1
              className="text-2xl font-extrabold text-center mb-[6rem] drop-shadow-lg"
              style={{ fontSize: "1.4rem", color: "#4169e1" }}
            >
              Blayzo is ready to chat
            </h1>
            {/* Greeting */}
            <div className="w-full max-w-xl mb-[6rem] rounded-lg border border-cyan-400 bg-black bg-opacity-70 flex items-center">
              <span
                className="font-bold"
                style={{
                  fontSize: "1.3rem",
                  lineHeight: "1.2",
                  fontWeight: "bold",
                  color: "#4169e1"
                }}
              >
                Hey, I'm Blayzo – your SoulBridge companion. I've got you, no matter what's on your mind. Let's talk.
              </span>
              <span className="ml-2 text-2xl" style={{ color: "#4169e1" }}>💬</span>
            </div>
            {/* Text box and Send button */}
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="w-full max-w-xl p-3 mb-[6rem] rounded-lg border border-cyan-400 bg-transparent"
              style={{ fontSize: "1rem", color: "#4169e1" }}
            />
            <button
              className="mb-[6rem] px-6 py-2 rounded-lg bg-black text-white font-bold shadow hover:bg-gray-800 transition"
              onClick={handleSend}
            >
              Send
            </button>
            {/* Show chat history */}
            <div className="w-full max-w-xl mb-4">
              {chat.map((msg, idx) => (
                <div key={idx} style={{ color: msg.sender === "ai" ? "#4169e1" : "#fff" }}>
                  <b>{msg.sender === "ai" ? "Blayzo" : "You"}:</b> {msg.text}
                </div>
              ))}
            </div>
            {/* SoulBridgeAI Chat label */}
            <div
              className="w-full max-w-xl mb-[6rem] rounded-lg border border-cyan-400 bg-black bg-opacity-70"
              style={{ fontSize: "1.7rem", color: "#4169e1" }}
            >
              SoulBridgeAI Chat
            </div>
          </>
        )}
        {step === 3 && character === "Blayzica" && (
          <>
            {/* Selected Character */}
            <p className="text-lg mb-[6rem]" style={{ color: "#ff1a1a" }}>
              Selected Character: <span className="font-bold">Blayzica</span>
            </p>
            {/* Blayzica is ready to chat */}
            <h1
              className="text-2xl font-extrabold text-center mb-[6rem] drop-shadow-lg"
              style={{ fontSize: "1.4rem", color: "#ff1a1a" }}
            >
              Blayzica is ready to chat
            </h1>
            {/* Greeting */}
            <div className="w-full max-w-xl mb-[6rem] rounded-lg border border-cyan-400 bg-black bg-opacity-70 flex items-center">
              <span
                className="font-bold"
                style={{
                  fontSize: "1.3rem",
                  lineHeight: "1.2",
                  fontWeight: "bold",
                  color: "#ff1a1a"
                }}
              >
                Hi! I'm Blayzica – your Soulbridge personal assistant, I'm here for your thoughts, feelings or just to vibe.
              </span>
              <span className="ml-2 text-2xl">💖</span>
            </div>
            {/* Text box and Send button */}
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Type your message..."
              className="w-full max-w-xl p-3 mb-[6rem] rounded-lg border border-cyan-400 bg-transparent"
              style={{ fontSize: "1rem", color: "#ff1a1a" }}
            />
            <button
              className="mb-[6rem] px-6 py-2 rounded-lg bg-black text-white font-bold shadow hover:bg-gray-800 transition"
              onClick={handleSend}
            >
              Send
            </button>
            {/* Show chat history */}
            <div className="w-full max-w-xl mb-4">
              {chat.map((msg, idx) => (
                <div key={idx} style={{ color: msg.sender === "ai" ? "#ff1a1a" : "#fff" }}>
                  <b>{msg.sender === "ai" ? "Blayzica" : "You"}:</b> {msg.text}
                </div>
              ))}
            </div>
            {/* SoulBridgeAI Chat label */}
            <div
              className="w-full max-w-xl mb-[6rem] rounded-lg border border-cyan-400 bg-black bg-opacity-70"
              style={{ fontSize: "1.7rem", color: "#ff1a1a" }}
            >
              SoulBridgeAI Chat
            </div>
          </>
        )}
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
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/user-profile" element={<UserProfile />} />
      </Routes>
    </Router>
  );
}
