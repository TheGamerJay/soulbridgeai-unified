import React, { useEffect, useMemo, useState } from "react";

export default function ReferralWidget({ apiBase = "/api/referrals", siteBaseUrl = "" }) {
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);
  const [codeInput, setCodeInput] = useState("");
  const [msg, setMsg] = useState("");
  const [rewards, setRewards] = useState(null);

  const shareLink = useMemo(() => {
    if (!me?.code) return "";
    const base = siteBaseUrl || window.location.origin;
    return `${base}/?ref=${me.code}`;
  }, [me, siteBaseUrl]);

  async function fetchMe() {
    setLoading(true);
    setMsg("");
    try {
      const res = await fetch(`${apiBase}/me`, { credentials: "include" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Failed to load referral info");
      setMe(data);
      
      // Also fetch rewards
      const rewardsRes = await fetch(`${apiBase}/rewards`, { credentials: "include" });
      if (rewardsRes.ok) {
        const rewardsData = await rewardsRes.json();
        setRewards(rewardsData);
      }
    } catch (e) {
      setMsg(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitCode(e) {
    e.preventDefault();
    setMsg("");
    const code = (codeInput || "").trim().toUpperCase();
    if (!code) {
      setMsg("Enter a code first.");
      return;
    }
    try {
      const res = await fetch(`${apiBase}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Could not apply code");
      
      let message = data.message || "Code applied.";
      if (data.new_rewards && data.new_rewards.length > 0) {
        message += ` 🎉 ${data.new_rewards.length} new reward(s) unlocked!`;
      }
      setMsg(message);
      
      await fetchMe();
      setCodeInput("");
    } catch (e) {
      setMsg(e.message);
    }
  }

  function copy(text) {
    navigator.clipboard.writeText(text).then(() => setMsg("Copied!"));
  }

  useEffect(() => {
    fetchMe();
    // If you support auto-apply via URL (?ref=XXXX):
    const params = new URLSearchParams(window.location.search);
    const ref = params.get("ref");
    if (ref) setCodeInput(ref.toUpperCase());
  }, []);

  if (loading) return <div className="ref-card">Loading referral info…</div>;

  const total = me?.stats?.total || 0;
  const unlocked = me?.stats?.unlocked || [];
  const next = me?.stats?.next_unlock || null;

  return (
    <div className="ref-card" style={styles.card}>
      <h3 style={styles.h3}>🎁 Referral Program</h3>

      {/* Your code + share */}
      <div style={styles.block}>
        <div style={styles.label}>Your Referral Code</div>
        <div style={styles.row}>
          <code style={styles.code}>{me?.code || "—"}</code>
          {me?.code && (
            <>
              <button style={styles.btn} onClick={() => copy(me.code)}>Copy Code</button>
              <button style={styles.btn} onClick={() => copy(shareLink)}>Copy Share Link</button>
            </>
          )}
        </div>
        {shareLink ? <div style={styles.small}>Share link: <span style={styles.mono}>{shareLink}</span></div> : null}
      </div>

      {/* Enter a friend's code */}
      <div style={styles.block}>
        <div style={styles.label}>Enter a Friend's Code</div>
        {me?.referred_by_user_id ? (
          <div style={styles.note}>✅ A referral is already linked to your account. Thanks!</div>
        ) : (
          <form onSubmit={submitCode} style={styles.row}>
            <input
              style={styles.input}
              value={codeInput}
              onChange={e => setCodeInput(e.target.value.toUpperCase())}
              placeholder="ABCD1234"
              maxLength={12}
            />
            <button style={styles.btnPrimary} type="submit">Apply</button>
          </form>
        )}
      </div>

      {/* Progress */}
      <div style={styles.block}>
        <div style={styles.label}>Your Referral Progress</div>
        <div style={styles.progressInfo}>
          <div>Total referrals: <strong>{total}</strong></div>
          <div>Unlocked thresholds: <strong>{unlocked.length ? unlocked.join(", ") : "none yet"}</strong></div>
          {next ? (
            <div>Next unlock at <strong>{next.at}</strong> (need <strong>{next.remaining}</strong> more)</div>
          ) : (
            <div>🎉 All current thresholds unlocked!</div>
          )}
        </div>
        
        {/* Progress bar */}
        {next && (
          <div style={styles.progressBarContainer}>
            <div 
              style={{
                ...styles.progressBar,
                width: `${Math.max(10, (total / next.at) * 100)}%`
              }}
            />
          </div>
        )}
      </div>

      {msg ? <div style={styles.msg}>{msg}</div> : null}
      
      {/* Unlocked Rewards */}
      {rewards && rewards.referral_rewards && (
        <div>
          {/* Unlocked Companions (unique characters) */}
          {rewards.referral_rewards.companions && rewards.referral_rewards.companions.length > 0 && (
            <div style={styles.block}>
              <div style={styles.label}>🎉 Your Unlocked Companions</div>
              <div style={styles.rewardGrid}>
                {rewards.referral_rewards.companions.map(companion => (
                  <div key={companion.id} style={{...styles.rewardCard, ...styles.companionCard}}>
                    <img 
                      src={companion.image_url} 
                      alt={companion.name}
                      style={styles.rewardImage}
                      onError={(e) => e.target.style.display = 'none'}
                    />
                    <div style={styles.rewardName}>{companion.name}</div>
                    <div style={styles.rewardTier}>{companion.tier} companion</div>
                    <div style={styles.rewardUnlock}>
                      Unlocked at {companion.threshold} referrals
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unlocked Skins (character variants) */}
          {rewards.referral_rewards.skins && Object.keys(rewards.referral_rewards.skins).length > 0 && (
            <div style={styles.block}>
              <div style={styles.label}>🎨 Your Unlocked Skins</div>
              {Object.entries(rewards.referral_rewards.skins).map(([baseChar, skinData]) => (
                <div key={baseChar} style={styles.skinGroup}>
                  <div style={styles.skinGroupTitle}>{skinData.base_name} Skins:</div>
                  <div style={styles.rewardGrid}>
                    {skinData.unlocked_skins.map(skin => (
                      <div key={skin.id} style={{...styles.rewardCard, ...styles.skinCard}}>
                        <img 
                          src={skin.image} 
                          alt={skin.name}
                          style={styles.rewardImage}
                          onError={(e) => e.target.style.display = 'none'}
                        />
                        <div style={styles.rewardName}>{skin.name}</div>
                        <div style={styles.rewardTier}>{skin.tier} skin</div>
                        <div style={styles.rewardUnlock}>
                          Unlocked at {skin.threshold} referrals
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Help text */}
      <div style={styles.helpText}>
        💡 Share your code with friends to unlock exclusive companions and features!<br />
        🎯 Unlock thresholds: 2 referrals (Blayzike), 5 referrals (Nyxara), 8 referrals (Claude Referral)
      </div>
    </div>
  );
}

const styles = {
  card: { 
    border: "1px solid #e5e7eb", 
    borderRadius: 12, 
    padding: 20, 
    maxWidth: 680, 
    background: "#fff",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    fontFamily: "system-ui, -apple-system, sans-serif"
  },
  h3: { 
    margin: "0 0 16px", 
    color: "#1f2937",
    fontSize: "20px",
    fontWeight: "600"
  },
  block: { 
    marginBottom: 20,
    padding: 16,
    background: "#f9fafb",
    borderRadius: 8,
    border: "1px solid #e5e7eb"
  },
  label: { 
    fontSize: 12, 
    color: "#6b7280", 
    marginBottom: 8, 
    textTransform: "uppercase", 
    letterSpacing: 0.5,
    fontWeight: "600"
  },
  row: { 
    display: "flex", 
    gap: 10, 
    alignItems: "center",
    flexWrap: "wrap"
  },
  code: { 
    fontWeight: "bold", 
    fontSize: 18, 
    padding: "8px 12px", 
    background: "#fff", 
    borderRadius: 8,
    border: "2px solid #3b82f6",
    color: "#3b82f6",
    fontFamily: "monospace",
    letterSpacing: "2px"
  },
  btn: { 
    padding: "8px 12px", 
    borderRadius: 8, 
    border: "1px solid #d1d5db", 
    background: "#f9fafb", 
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "500",
    transition: "all 0.2s",
    ":hover": { background: "#f3f4f6" }
  },
  btnPrimary: { 
    padding: "8px 16px", 
    borderRadius: 8, 
    border: "1px solid #3b82f6", 
    background: "#3b82f6", 
    color: "#fff", 
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
    transition: "all 0.2s"
  },
  input: { 
    padding: "10px 12px", 
    borderRadius: 8, 
    border: "1px solid #d1d5db", 
    flex: 1, 
    fontFamily: "monospace",
    fontSize: "16px",
    letterSpacing: "1px",
    minWidth: "120px"
  },
  small: { 
    fontSize: 12, 
    color: "#6b7280", 
    marginTop: 8,
    wordBreak: "break-all"
  },
  mono: { 
    fontFamily: "monospace",
    background: "#f3f4f6",
    padding: "2px 4px",
    borderRadius: 4
  },
  note: { 
    fontSize: 14, 
    color: "#059669",
    background: "#d1fae5",
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #a7f3d0"
  },
  progressInfo: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    marginBottom: 12
  },
  progressBarContainer: {
    width: "100%",
    height: 8,
    background: "#e5e7eb",
    borderRadius: 4,
    overflow: "hidden"
  },
  progressBar: {
    height: "100%",
    background: "linear-gradient(90deg, #3b82f6, #8b5cf6)",
    borderRadius: 4,
    transition: "width 0.3s ease"
  },
  msg: { 
    marginTop: 12, 
    color: "#1f2937",
    padding: "8px 12px",
    background: "#dbeafe",
    border: "1px solid #93c5fd",
    borderRadius: 6,
    fontSize: "14px"
  },
  helpText: {
    fontSize: 12,
    color: "#6b7280",
    textAlign: "center",
    marginTop: 16,
    fontStyle: "italic"
  },
  rewardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
    gap: 12,
    marginTop: 8
  },
  rewardCard: {
    background: "#fff",
    borderRadius: 8,
    padding: 8,
    textAlign: "center",
    transition: "all 0.2s",
    cursor: "pointer"
  },
  companionCard: {
    border: "2px solid #3b82f6",  // Blue border for companions
    boxShadow: "0 2px 4px rgba(59, 130, 246, 0.1)"
  },
  skinCard: {
    border: "2px solid #8b5cf6",  // Purple border for skins
    boxShadow: "0 2px 4px rgba(139, 92, 246, 0.1)"
  },
  rewardImage: {
    width: 60,
    height: 60,
    objectFit: "cover",
    borderRadius: 6,
    marginBottom: 6
  },
  rewardName: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1f2937",
    marginBottom: 2
  },
  rewardTier: {
    fontSize: 10,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 2
  },
  rewardUnlock: {
    fontSize: 9,
    color: "#059669",
    fontStyle: "italic"
  },
  skinGroup: {
    marginBottom: 16
  },
  skinGroupTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4b5563",
    marginBottom: 8,
    paddingBottom: 4,
    borderBottom: "1px solid #e5e7eb"
  }
};