// Run this in browser DevTools Console to clear trial localStorage flags
console.log('🧹 Clearing trial localStorage flags...');

// List current localStorage items
console.log('Current localStorage:');
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    console.log(`  ${key}: ${localStorage.getItem(key)}`);
}

// Clear trial-related flags
localStorage.removeItem('trialUsed');
localStorage.removeItem('trialActive');
localStorage.removeItem('trialExpiry');
localStorage.removeItem('trial_used_permanently');

console.log('✅ Trial localStorage flags cleared!');
console.log('🔄 Refresh the page to test the 5-hour trial again');