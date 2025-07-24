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
    'Hey, I’m <strong>SoulBridgeAI</strong> — your emotional support companion. 💙<br>What’s on your mind today?'
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
  console.log(`Auto-muting user for message ${messageId}`);
  // Implementation would connect to backend moderation API
}

function logEvent(event) {
  console.log(`Community Event: ${event} at ${new Date().toISOString()}`);
}