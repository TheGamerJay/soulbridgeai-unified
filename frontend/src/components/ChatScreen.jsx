import React, { useState, useEffect } from 'react';

export default function ChatScreen({ character }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const characterInfo = {
    'Blayzo': {
      color: '#4169e1',
      image: '/Blayzo.png',
      greeting: "Hey, I'm Blayzo – your SoulBridge companion. I got you, no matter what's on your mind. Let's talk. 💬"
    },
    'Blayzica': {
      color: '#ff1a1a', 
      image: '/Blayzica.png',
      greeting: "Hi! I'm Blayzica – your SoulBridge personal assistant. I'm here for your thoughts, feelings or just to vibe. 💖"
    }
  };

  const currentChar = characterInfo[character] || characterInfo['Blayzo'];

  useEffect(() => {
    // Add initial greeting message
    setMessages([{
      sender: character,
      text: currentChar.greeting,
      timestamp: new Date()
    }]);
  }, [character, currentChar.greeting]);

  const handleSend = async () => {
    if (input.trim() === '') return;
    
    const userMessage = { sender: 'You', text: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate API call to backend
    try {
      const response = await fetch('http://127.0.0.1:8080/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          character: character
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          sender: character,
          text: data.reply || `Thanks for sharing that with me. As ${character}, I'm here to support you.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        sender: character,
        text: `I'm sorry, I'm having trouble connecting right now. But I'm still here for you!`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      maxWidth: '800px',
      margin: '0 auto',
      padding: '1rem',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '1rem',
        background: 'linear-gradient(145deg, rgba(0,0,0,0.8), rgba(15,23,42,0.9))',
        borderRadius: '15px',
        border: `2px solid ${currentChar.color}`,
        marginBottom: '1rem'
      }}>
        <img
          src={currentChar.image}
          alt={character}
          style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            border: `2px solid ${currentChar.color}`,
            marginRight: '1rem'
          }}
        />
        <div>
          <h2 style={{
            fontSize: '1.5rem',
            color: currentChar.color,
            margin: '0',
            fontWeight: '600'
          }}>
            {character}
          </h2>
          <p style={{
            color: 'rgba(255, 255, 255, 0.7)',
            margin: '0',
            fontSize: '0.9rem'
          }}>
            {isTyping ? 'Typing...' : 'Online'}
          </p>
        </div>
      </div>

      {/* Messages Container */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        background: 'rgba(0, 0, 0, 0.3)',
        borderRadius: '15px',
        marginBottom: '1rem'
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: 'flex',
            justifyContent: msg.sender === 'You' ? 'flex-end' : 'flex-start',
            marginBottom: '1rem'
          }}>
            <div style={{
              maxWidth: '70%',
              padding: '12px 16px',
              borderRadius: '18px',
              background: msg.sender === 'You' 
                ? 'linear-gradient(135deg, #22d3ee, #0891b2)' 
                : `linear-gradient(135deg, ${currentChar.color}, ${currentChar.color}cc)`,
              color: '#fff',
              fontSize: '1rem',
              lineHeight: '1.4'
            }}>
              <strong style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                {msg.sender}:
              </strong>
              <div style={{ marginTop: '4px' }}>
                {msg.text}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div style={{
            display: 'flex',
            justifyContent: 'flex-start',
            marginBottom: '1rem'
          }}>
            <div style={{
              padding: '12px 16px',
              borderRadius: '18px',
              background: `linear-gradient(135deg, ${currentChar.color}, ${currentChar.color}cc)`,
              color: '#fff',
              fontSize: '1rem'
            }}>
              <em>{character} is typing...</em>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        padding: '1rem',
        background: 'rgba(0, 0, 0, 0.5)',
        borderRadius: '15px',
        border: `1px solid ${currentChar.color}40`
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={`Message ${character}...`}
          disabled={isTyping}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: '25px',
            border: `2px solid ${currentChar.color}40`,
            background: 'rgba(0, 0, 0, 0.7)',
            color: '#fff',
            fontSize: '1rem',
            outline: 'none',
            transition: 'border-color 0.3s ease'
          }}
          onFocus={(e) => e.target.style.borderColor = currentChar.color}
          onBlur={(e) => e.target.style.borderColor = `${currentChar.color}40`}
        />
        <button
          onClick={handleSend}
          disabled={isTyping || !input.trim()}
          style={{
            padding: '12px 24px',
            borderRadius: '25px',
            border: 'none',
            background: input.trim() && !isTyping 
              ? `linear-gradient(135deg, ${currentChar.color}, ${currentChar.color}cc)`
              : 'rgba(107, 114, 128, 0.5)',
            color: '#fff',
            fontWeight: '600',
            cursor: input.trim() && !isTyping ? 'pointer' : 'not-allowed',
            transition: 'all 0.3s ease',
            fontSize: '1rem'
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}