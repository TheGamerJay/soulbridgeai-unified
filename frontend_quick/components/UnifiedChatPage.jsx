// UnifiedChatPage.jsx - Option A: Visual consolidation while preserving tier isolation
import { useState, useEffect } from "react";
import { Send } from "lucide-react";

export default function UnifiedChatPage({ userPlan = "bronze", trialActive = false }) {
  const [messages, setMessages] = useState([
    { id: 1, sender: "bot", text: "Hello! How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // TIER-SPECIFIC FEATURES - Each tier sees different features/limits
  const getFeatures = (plan, trial) => {
    const baseFeatures = [
      {
        icon: "🧠", 
        label: "Decoder", 
        route: "decoder",
        tag: plan === 'gold' ? "∞" : plan === 'silver' ? "15/day" : "3/day",
        available: true,
        tier: "bronze"
      },
      {
        icon: "🔮", 
        label: "Fortune", 
        route: "fortune",
        tag: plan === 'gold' ? "999" : plan === 'silver' ? "8/day" : "3/day",
        available: true,
        tier: "bronze"
      },
      {
        icon: "⭐", 
        label: "Horoscope", 
        route: "horoscope",
        tag: plan === 'gold' ? "∞" : plan === 'silver' ? "10/day" : "3/day",
        available: true,
        tier: "bronze"
      },
      {
        icon: "✍️", 
        label: "Creative Writer", 
        route: "creative-writing",
        tag: plan === 'bronze' ? "3/day" : plan === 'silver' ? "15/day" : "∞",
        available: true,
        tier: "bronze"
      },
      {
        icon: "🤖", 
        label: "AI Companions", 
        route: plan === 'bronze' ? "chat/gamerjay_bronze" : plan === 'silver' ? "chat/sky_silver" : "chat/crimson_gold",
        tag: `${plan.charAt(0).toUpperCase() + plan.slice(1)} Access`,
        available: true,
        tier: plan
      }
    ];

    // Add premium features based on tier
    if (plan !== 'bronze' || trial) {
      baseFeatures.push(
        {
          icon: "🎤", 
          label: "Voice Journal", 
          route: "voice-journaling",
          tag: plan === 'bronze' && !trial ? "🔒 Premium" : "Available",
          available: plan !== 'bronze' || trial,
          tier: "silver"
        },
        {
          icon: "🎨", 
          label: "AI Images", 
          route: "ai-image-generation",
          tag: plan === 'bronze' && !trial ? "🔒 Premium" : plan === 'gold' ? "∞" : "10/month",
          available: plan !== 'bronze' || trial,
          tier: "silver"
        },
        {
          icon: "❤️", 
          label: "Relationships", 
          route: "relationship-profiles",
          tag: plan === 'bronze' && !trial ? "🔒 Premium" : "Available",
          available: plan !== 'bronze' || trial,
          tier: "silver"
        },
        {
          icon: "🧘", 
          label: "Meditations", 
          route: "emotional-meditations",
          tag: plan === 'bronze' && !trial ? "🔒 Premium" : "Available",
          available: plan !== 'bronze' || trial,
          tier: "silver"
        }
      );
    }

    // Add Gold exclusive features
    if (plan === 'gold' || (trial && plan === 'bronze')) {
      baseFeatures.push({
        icon: "🎵", 
        label: "Mini Studio", 
        route: "mini-studio",
        tag: plan === 'gold' || trial ? "Available" : "🔒 Gold Only",
        available: plan === 'gold' || trial,
        tier: "gold"
      });
    }

    return baseFeatures;
  };

  const features = getFeatures(userPlan, trialActive);

  const handleFeatureClick = (feature) => {
    if (!feature.available) {
      // Show upgrade modal for locked features
      alert(`This feature requires ${feature.tier === 'silver' ? 'Silver' : 'Gold'} tier. Upgrade now?`);
      window.location.href = '/plan-selection';
      return;
    }
    
    // Navigate to existing route (preserves all backend logic)
    window.location.href = `/${feature.route}`;
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { id: Date.now(), sender: "user", text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Use existing chat API (preserves all backend logic)
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: input })
      });

      const data = await response.json();
      
      if (data.success) {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          sender: "bot",
          text: data.response
        }]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: "bot",
        text: "Sorry, I'm having technical difficulties. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  // TIER-SPECIFIC STYLING
  const getTierColors = (plan) => {
    switch (plan) {
      case 'bronze':
        return {
          primary: '#00FFFF',
          secondary: '#1a1a1a',
          gradient: 'from-cyan-500 to-cyan-600'
        };
      case 'silver':
        return {
          primary: '#C0C0C0',
          secondary: '#1a1a1a',
          gradient: 'from-gray-400 to-gray-500'
        };
      case 'gold':
        return {
          primary: '#FFD700',
          secondary: '#1a1a1a',
          gradient: 'from-yellow-400 to-yellow-500'
        };
      default:
        return {
          primary: '#00FFFF',
          secondary: '#1a1a1a',
          gradient: 'from-cyan-500 to-cyan-600'
        };
    }
  };

  const colors = getTierColors(userPlan);

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-900">
      {/* Top bar with tier-specific feature chips */}
      <div className="sticky top-0 z-20 w-full bg-gray-900/95 backdrop-blur supports-[backdrop-filter]:bg-gray-900/80 shadow-sm">
        {/* Tier indicator */}
        <div className="text-center py-2 text-sm font-medium text-white">
          <span style={{ color: colors.primary }}>
            {userPlan.charAt(0).toUpperCase() + userPlan.slice(1)} Tier
          </span>
          {trialActive && (
            <span className="ml-2 px-2 py-1 rounded-full bg-green-500/20 text-green-300 text-xs">
              Trial Active
            </span>
          )}
        </div>
        
        {/* Feature chips */}
        <div className="max-w-6xl mx-auto px-3 py-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {features.map((f, i) => {
            const isPremium = f.tag?.includes('🔒');
            const isInfinity = f.tag === "∞" || f.tag === "999";
            const isAvailable = f.available;
            
            return (
              <button
                key={i}
                onClick={() => handleFeatureClick(f)}
                className={`group flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm font-medium ring-1 ring-white/10 transition-all
                  ${isAvailable 
                    ? "bg-gray-900 hover:bg-gray-800 cursor-pointer" 
                    : "bg-gray-800 hover:bg-gray-700 cursor-pointer opacity-75"
                  } text-white`}
                style={{
                  borderColor: isAvailable ? colors.primary : '#666'
                }}
              >
                <span className="flex items-center gap-1.5">
                  <span className="text-base">{f.icon}</span>
                  <span className="truncate">{f.label}</span>
                </span>

                {isInfinity && isAvailable && (
                  <span className="ml-2 rounded-md px-1.5 py-0.5 text-xs font-semibold bg-emerald-400/15 text-emerald-300 ring-1 ring-emerald-400/30">
                    {f.tag}
                  </span>
                )}
                {isPremium && (
                  <span className="ml-2 rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-amber-400/15 text-amber-300 ring-1 ring-amber-400/30">
                    Locked
                  </span>
                )}
                {!isPremium && !isInfinity && f.tag && (
                  <span 
                    className="ml-2 rounded-md px-1.5 py-0.5 text-xs font-semibold ring-1"
                    style={{
                      backgroundColor: `${colors.primary}15`,
                      color: colors.primary,
                      borderColor: `${colors.primary}30`
                    }}
                  >
                    {f.tag}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.sender !== "user" && (
                <div 
                  className="w-8 h-8 shrink-0 mr-2 rounded-full text-white grid place-items-center"
                  style={{
                    background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`
                  }}
                >
                  🤖
                </div>
              )}
              <div
                className={`px-4 py-2 rounded-2xl max-w-[80%] shadow-sm ${
                  msg.sender === "user"
                    ? `text-white`
                    : "bg-white text-gray-800 ring-1 ring-gray-200"
                }`}
                style={{
                  background: msg.sender === "user" ? colors.primary : undefined,
                  color: msg.sender === "user" ? colors.secondary : undefined
                }}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div 
                className="w-8 h-8 shrink-0 mr-2 rounded-full text-white grid place-items-center"
                style={{
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.secondary})`
                }}
              >
                🤖
              </div>
              <div className="px-4 py-2 rounded-2xl bg-white text-gray-800 ring-1 ring-gray-200">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input row */}
      <div className="border-t bg-white">
        <div className="max-w-3xl mx-auto w-full p-3 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message your AI companion..."
            className="flex-1 px-4 py-3 rounded-full border border-gray-200 focus:outline-none focus:ring-2"
            style={{ 
              '--tw-ring-color': colors.primary + '50'
            }}
            onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            className="h-12 w-12 rounded-full text-white grid place-items-center transition-colors"
            style={{
              background: colors.primary,
              opacity: loading ? 0.5 : 1
            }}
            aria-label="Send"
            title="Send"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}