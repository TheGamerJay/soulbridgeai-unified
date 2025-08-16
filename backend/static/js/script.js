document.addEventListener("DOMContentLoaded", () => {
  // DOM
  const chatBox  = document.getElementById("chat-messages");
  const form     = document.getElementById("chat-form");
  const input    = document.getElementById("messageInput");
  const sendBtn  = document.getElementById("sendBtn");
  const micBtn   = document.getElementById("micBtn");
  const themeBtn = document.getElementById("themeBtn");
  const clearBtn = document.getElementById("clearBtn");

  // Helpers
  const scroll = () => (chatBox.scrollTop = chatBox.scrollHeight);
  const now    = () =>
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const nl2br  = (t) => t.replace(/\n/g, "<br>");

  function bubble(role, html) {
    const wrap   = document.createElement("div");
    wrap.className = `message ${role}-message`;
    wrap.innerHTML = `
      <div class="chat-avatar">
        ${role === "user" ? '<i class="fas fa-user"></i>' : '<i class="fas fa-heart"></i>'}
      </div>
      <div class="bubble">${html}<div class="timestamp">${now()}</div></div>`;
    chatBox.appendChild(wrap);
    scroll();
  }

  // Typing indicator
  let typingWrap = null;
  const showTyping = () => {
    typingWrap = document.createElement("div");
    typingWrap.className = "message ai-message message-typing";
    typingWrap.innerHTML = `
      <div class="chat-avatar"><i class="fas fa-heart"></i></div>
      <div class="bubble">
        <span class="dot">•</span><span class="dot">•</span><span class="dot">•</span>
      </div>`;
    chatBox.appendChild(typingWrap);
    scroll();
  };
  const hideTyping = () => typingWrap && typingWrap.remove();

  // AI welcome
  bubble(
    "ai",
    'Hey, I'm <strong>SoulBridgeAI</strong> — your emotional support companion. 💙<br>What's on your mind today?<br><br>💡 <em>New:</em> <a href="/companions" style="color: var(--primary); text-decoration: none;">Choose a different companion</a> or <a href="/group-therapy" style="color: var(--primary); text-decoration: none;">join group therapy</a>!'
  );

  // Speech synthesis for AI replies
  const speak = (text) => {
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1; utter.pitch = 1; utter.lang = "en-US";
      window.speechSynthesis.speak(utter);
    } catch {}
  };

  // Main send
  async function send(msg) {
    if (!msg.trim()) return;
    bubble("user", nl2br(msg));
    input.value = "";
    showTyping();

    try {
      const res = await fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      hideTyping();
      const reply = data.success ? data.response : `⚠️ ${data.error}`;
      bubble("ai", nl2br(reply));
      speak(reply);
    } catch (err) {
      hideTyping();
      bubble("ai", "⚠️ Network error, please try again.");
    }
  }

  // Form submit / btn click / Enter
  form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
  sendBtn.addEventListener("click", () => send(input.value));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });

  // Theme toggle
  themeBtn.addEventListener("click", () => {
    const html = document.documentElement;
    const isDark = html.getAttribute("data-bs-theme") === "dark";
    html.setAttribute("data-bs-theme", isDark ? "light" : "dark");
  });

  // Clear chat
  clearBtn.addEventListener("click", () => (chatBox.innerHTML = ""));

  // Voice-to-text (if browser supports)
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new Rec();
    rec.lang = "en-US"; rec.interimResults = false;
    micBtn.addEventListener("click", () => {
      micBtn.classList.toggle("active");
      if (micBtn.classList.contains("active")) {
        rec.start();
      } else rec.stop();
    });
    rec.onresult = (e) => {
      const txt = e.results[0][0].transcript;
      input.value = txt; micBtn.classList.remove("active"); send(txt);
    };
    rec.onerror = () => micBtn.classList.remove("active");
  } else {
    micBtn.disabled = true; micBtn.title = "Voice input not supported";
  }
});

// ==========================
// 🌐 SoulBridgeAI Community & Profile System
// ==========================

// ✅ Profile Enhancements
const userProfile = {
  displayName: "Jaay El Nene",
  profilePicture: "/assets/profiles/default.png",
  bio: "Hopeful dreamer building bridges with words",
  checkInStreak: 14,
  referralPoints: 25,
  subscription: {
    tier: "Growth",
    startedOn: "2025-07-01",
    renewsOn: "2025-08-01",
    daysRemaining: 8
  }
};

// ✅ Community Access Control
function handleCommunityAccess(user) {
  const btn = document.querySelector("#community-btn");

  if (user.status.community_ban === true) {
    btn.disabled = true;
    btn.innerText = "Access Denied";
    btn.addEventListener("click", () => {
      alert("You have been banned from the community for violating our guidelines.");
    });
  }
}

// ✅ Community Moderation System
const communityRules = {
  profanityFilter: true,
  toxicityDetection: true,
  maxWarnings: 2,
  actionsOnViolations: (user) => {
    user.warnings++;
    if (user.warnings === 1) {
      notifyUser("Warning issued for inappropriate behavior.");
    } else if (user.warnings >= 2) {
      user.status.community_ban = true;
      handleCommunityAccess(user);
      notifyUser("You have been banned from the community.");
    }
  }
};

// Moderation queue for reports
let moderationQueue = [];

// ✅ User Reporting System
function reportMessage(messageId, reason, reporterId) {
  const validReasons = ["Inappropriate", "Hateful", "Harmful", "Crisis"];
  if (!validReasons.includes(reason)) return;

  moderationQueue.push({
    messageId,
    reason,
    reporterId,
    timestamp: Date.now(),
    reviewed: false
  });

  // Optional: Auto-mute if too many flags on same message
  const flaggedCount = moderationQueue.filter(r => r.messageId === messageId).length;
  if (flaggedCount >= 3) autoMuteUser(messageId);

  logEvent("Report filed for moderation.");
}

// ✅ Display Name + Avatar in Community
function renderCommunityPost(post) {
  return `
    <div class="community-post">
      <img src="${post.user.profilePicture}" class="avatar" />
      <div class="content">
        <strong>${post.user.displayName}</strong>
        <p>${sanitize(post.content)}</p>
      </div>
    </div>
  `;
}

// ✅ Referral + Rewards
function updateReferralPoints(user, points) {
  user.referralPoints += points;
  notifyUser(`🎁 You earned ${points} Soul Points!`);
}

// ✅ Profile Panel UI Hook
function renderUserProfile(user) {
  return `
    <div class="profile-panel">
      <img src="${user.profilePicture}" class="avatar-lg" />
      <h2>${user.displayName}</h2>
      <p>${user.bio}</p>
      <p>🔥 Streak: ${user.checkInStreak} days</p>
      <p>🎁 Points: ${user.referralPoints}</p>
      <p>📅 Subscription: ${user.subscription.tier}</p>
      <p>🔄 Renews in ${user.subscription.daysRemaining} days</p>
    </div>
  `;
}

// ✅ Utility: Sanitize input
function sanitize(text) {
  return text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Helper functions for community system
function notifyUser(message) {
  // Integration with existing notification system
  if (typeof showNotification !== 'undefined') {
    showNotification(message);
  } else {
    alert(message);
  }
}

function autoMuteUser(messageId) {
  // Auto-mute logic for flagged users
  // Implementation would connect to backend moderation API
}

function logEvent(event) {
}

// ==========================
// 🎭 AI Personality Modes System
// ==========================

let personalityModes = {};
let currentPersonalityMode = null;

// Load personality modes on page load
async function loadPersonalityModes() {
  try {
    const response = await fetch('/api/personality-modes');
    const data = await response.json();
    
    if (data.success) {
      personalityModes = data.modes;
      renderPersonalityModeSelector();
    } else {
      console.warn('Personality modes not available:', data.error);
    }
  } catch (error) {
    console.error('Failed to load personality modes:', error);
  }
}

// Render personality mode selector in chat interface
function renderPersonalityModeSelector() {
  const chatContainer = document.querySelector('#chat-messages').parentElement;
  
  // Create personality mode selector if it doesn't exist
  let selector = document.querySelector('#personality-mode-selector');
  if (!selector) {
    selector = document.createElement('div');
    selector.id = 'personality-mode-selector';
    selector.className = 'personality-mode-selector';
    selector.innerHTML = `
      <div class="mode-header">
        <span>🎭 Personality Mode:</span>
        <select id="personality-mode-select">
          <option value="">Default</option>
        </select>
      </div>
    `;
    
    // Insert before chat form
    const chatForm = document.querySelector('#chat-form');
    chatForm.parentElement.insertBefore(selector, chatForm);
  }
  
  // Populate options
  const select = selector.querySelector('#personality-mode-select');
  select.innerHTML = '<option value="">Default</option>';
  
  Object.entries(personalityModes).forEach(([key, mode]) => {
    const option = document.createElement('option');
    option.value = key;
    option.textContent = `${mode.name} - ${mode.description}`;
    select.appendChild(option);
  });
  
  // Add change handler
  select.addEventListener('change', (e) => {
    currentPersonalityMode = e.target.value || null;
  });
}

// Modify the send function to include personality mode
const originalSend = window.send || function() {};
window.send = function(message) {
  if (typeof originalSend === 'function') {
    // If there's an existing send function, call it with personality mode
    return originalSend(message, currentPersonalityMode);
  }
  
  // Fallback send implementation with personality mode
  fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      character: window.selectedCharacter || 'Blayzo',
      personality_mode: currentPersonalityMode
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      bubble('ai', data.response);
    } else {
      bubble('ai', 'Sorry, I encountered an error. Please try again.');
    }
  })
  .catch(error => {
    console.error('Chat error:', error);
    bubble('ai', 'Sorry, I encountered an error. Please try again.');
  });
};

// Initialize personality modes when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(loadPersonalityModes, 1000); // Load after main chat interface
});

// ==========================
// 🏆 Gamification & Achievement System
// ==========================

let userProfile = null;
let achievements = [];

// Load user achievements and profile
async function loadAchievements() {
  try {
    const response = await fetch('/api/achievements');
    const data = await response.json();
    
    if (data.success) {
      userProfile = data.profile;
      achievements = data.achievements;
      displayUserLevel();
    } else {
      console.warn('Achievements not available:', data.error);
    }
  } catch (error) {
    console.error('Failed to load achievements:', error);
  }
}

// Display user level and progress
function displayUserLevel() {
  if (!userProfile) return;

  // Create or update level display
  let levelDisplay = document.querySelector('#user-level-display');
  if (!levelDisplay) {
    levelDisplay = document.createElement('div');
    levelDisplay.id = 'user-level-display';
    levelDisplay.className = 'user-level-display';
    
    // Insert at top of chat interface
    const chatContainer = document.querySelector('#chat-messages').parentElement;
    chatContainer.insertBefore(levelDisplay, chatContainer.firstChild);
  }
  
  levelDisplay.innerHTML = `
    <div class="level-info">
      <div class="level-badge">
        <span class="level-number">${userProfile.level}</span>
        <span class="level-title">${userProfile.title}</span>
      </div>
      <div class="level-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${calculateProgressPercentage()}%"></div>
        </div>
        <span class="progress-text">${userProfile.total_points} points</span>
      </div>
      <button class="achievements-btn" onclick="showAchievementsModal()">
        🏆 Achievements (${achievements.filter(a => a.earned).length})
      </button>
    </div>
  `;
}

// Calculate progress percentage to next level
function calculateProgressPercentage() {
  if (!userProfile || userProfile.progress_to_next_level === 0) return 100;
  
  const currentLevelPoints = userProfile.total_points - userProfile.progress_to_next_level;
  const nextLevelPoints = userProfile.total_points;
  const totalForLevel = nextLevelPoints - currentLevelPoints;
  
  return Math.min(100, ((userProfile.total_points - currentLevelPoints) / totalForLevel) * 100);
}

// Show achievements modal
function showAchievementsModal() {
  let modal = document.querySelector('#achievements-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'achievements-modal';
    modal.className = 'achievements-modal';
    document.body.appendChild(modal);
  }
  
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h2>🏆 Your Achievements</h2>
        <button class="close-btn" onclick="closeAchievementsModal()">&times;</button>
      </div>
      <div class="modal-body">
        <div class="achievements-grid">
          ${achievements.map(achievement => `
            <div class="achievement-card ${achievement.earned ? 'earned' : 'locked'}">
              <div class="achievement-icon">${achievement.icon}</div>
              <div class="achievement-info">
                <h3>${achievement.name}</h3>
                <p>${achievement.description}</p>
                <div class="rarity ${achievement.rarity.toLowerCase()}">${achievement.rarity_info.name}</div>
                ${achievement.earned ? 
                  '<div class="earned-badge">✓ Earned</div>' : 
                  '<div class="locked-badge">🔒 Locked</div>'
                }
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
  
  modal.style.display = 'flex';
}

// Close achievements modal
function closeAchievementsModal() {
  const modal = document.querySelector('#achievements-modal');
  if (modal) {
    modal.style.display = 'none';
  }
}

// Show achievement notification
function showAchievementNotification(achievementId) {
  const achievement = achievements.find(a => a.badge_id === achievementId);
  if (!achievement) return;
  
  const notification = document.createElement('div');
  notification.className = 'achievement-notification';
  notification.innerHTML = `
    <div class="notification-content">
      <div class="notification-icon">🏆</div>
      <div class="notification-text">
        <strong>Achievement Unlocked!</strong>
        <br>${achievement.icon} ${achievement.name}
      </div>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

// Check for new achievements after user activity
async function checkForNewAchievements(activityData = {}) {
  try {
    const response = await fetch('/api/check-achievements', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(activityData)
    });
    
    const data = await response.json();
    if (data.success && data.newly_earned.length > 0) {
      // Show notifications for new achievements
      data.newly_earned.forEach(achievementId => {
        showAchievementNotification(achievementId);
      });
      
      // Reload achievements and update display
      await loadAchievements();
    }
  } catch (error) {
    console.error('Failed to check achievements:', error);
  }
}

// Initialize gamification system
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    loadAchievements();
    
    // Check achievements after first message
    const originalSend = window.send;
    if (originalSend) {
      window.send = function(message, personalityMode) {
        const result = originalSend.call(this, message, personalityMode);
        
        // Track activity for achievements
        checkForNewAchievements({
          messages_sent: 1,
          last_activity: new Date().toISOString()
        });
        
        return result;
      };
    }
  }, 1500);
});