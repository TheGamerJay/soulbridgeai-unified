import React, { useState } from 'react';

export default function ChatScreen({ character }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  const handleSend = () => {
    if (input.trim() === '') return;
    setMessages([...messages, { sender: 'You', text: input }]);
    setInput('');
  };

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Greeting always uses the selected character */}
      <div className="font-bold text-2xl mb-4" style={{ fontSize: "2rem" }}>
        Hey, I'm {character} – your SoulBridge companion. I got you, no matter what's on your mind. Let's talk. 💬
      </div>
      <h1 className="text-2xl font-extrabold text-center mb-2 text-cyan-400 drop-shadow-lg">
        {character} is ready to chat
      </h1>
      <p className="text-lg mb-6 text-cyan-400">
        Selected Character: <span className="font-bold">{character}</span>
      </p>
      <div className="w-80 mb-4 flex flex-col items-center">
        {messages.map((msg, idx) => (
          <div key={idx} className="mb-2 text-center text-cyan-300">
            <strong>{msg.sender}:</strong> <span>{msg.text}</span>
          </div>
        ))}
      </div>
      <input 
        type="text" 
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder="Type your message..." 
        className="p-2 rounded-lg text-black w-80 mb-4 border-2 border-cyan-400 focus:border-cyan-600 focus:outline-none text-center"
      />
      <button 
        className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold py-2 px-4 rounded mb-4 shadow-lg transition-colors duration-200"
        onClick={handleSend}
      >
        Send
      </button>
    </div>
  );
}
