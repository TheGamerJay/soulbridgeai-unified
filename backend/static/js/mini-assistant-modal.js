// Mini Assistant Modal (global)
(function(){
    // Create modal HTML
    const modal = document.createElement('div');
    modal.id = 'miniAssistantModal';
    modal.style = `
        display: none; position: fixed; z-index: 9999; left: 0; top: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.65); align-items: center; justify-content: center;`
    ;
    modal.innerHTML = `
      <div style="background: #181c1f; color: #e1e1e1; border-radius: 12px; box-shadow: 0 8px 32px #000a; width: 420px; max-width: 95vw; padding: 0; overflow: hidden; font-family: inherit;">
        <div style="background: #23282b; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;">
          <span style="font-weight: bold; font-size: 1.1rem;">🧠 Mini Assistant</span>
          <button id="miniAssistantClose" style="background: none; border: none; color: #e1e1e1; font-size: 1.3rem; cursor: pointer;">×</button>
        </div>
        <div id="miniAssistantStatus" style="padding: 8px 20px; font-size: 0.95rem; color: #00d4aa;">Checking status...</div>
        <div style="padding: 16px 20px;">
          <input id="miniAssistantFile" type="text" placeholder="File path (optional)" style="width: 100%; margin-bottom: 10px; padding: 8px; border-radius: 6px; border: 1px solid #333; background: #23282b; color: #e1e1e1;" />
          <textarea id="miniAssistantPrompt" rows="3" placeholder="Ask me anything about your code..." style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #333; background: #23282b; color: #e1e1e1;"></textarea>
          <button id="miniAssistantSend" style="margin-top: 12px; width: 100%; background: #00d4aa; color: #181c1f; border: none; border-radius: 6px; padding: 10px 0; font-weight: bold; font-size: 1rem; cursor: pointer;">Send to Assistant</button>
          <button id="miniAssistantCheck" style="margin-top: 8px; width: 100%; background: #23282b; color: #00d4aa; border: 1px solid #00d4aa; border-radius: 6px; padding: 8px 0; font-size: 0.95rem; cursor: pointer;">Check Status</button>
          <div id="miniAssistantResponse" style="margin-top: 18px; min-height: 40px; font-size: 0.98rem; color: #e1e1e1;"></div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Show/hide modal
    function showModal() { modal.style.display = 'flex'; checkStatus(); }
    function hideModal() { modal.style.display = 'none'; }
    document.getElementById('miniAssistantClose').onclick = hideModal;
    window.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.style.display === 'flex') hideModal();
    });

    // Keyboard shortcut: Ctrl+Shift+M
    window.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'm') {
        e.preventDefault();
        showModal();
      }
    });

    // Status check
    async function checkStatus() {
      const statusDiv = document.getElementById('miniAssistantStatus');
      statusDiv.textContent = 'Checking status...';
      try {
        const res = await fetch('/api/mini-assistant-status');
        console.log('Mini Assistant Status Response:', res.status, res.statusText);
        const data = await res.json();
        console.log('Mini Assistant Status Data:', data);
        if (data.success) {
          statusDiv.textContent = data.claude_available ? '🧠 Claude Ready' : '🟢 Ready';
          statusDiv.style.color = data.claude_available ? '#00d4aa' : '#00d4aa';
        } else {
          statusDiv.textContent = '❌ Offline';
          statusDiv.style.color = '#e74c3c';
        }
      } catch (error) {
        console.error('Mini Assistant Status Error:', error);
        statusDiv.textContent = '❌ Could not check status: fetch failed';
        statusDiv.style.color = '#e74c3c';
      }
    }
    document.getElementById('miniAssistantCheck').onclick = checkStatus;

    // Send to Assistant
    document.getElementById('miniAssistantSend').onclick = async function() {
      const prompt = document.getElementById('miniAssistantPrompt').value.trim();
      const file = document.getElementById('miniAssistantFile').value.trim();
      const responseDiv = document.getElementById('miniAssistantResponse');
      const sendButton = document.getElementById('miniAssistantSend');
      
      if (!prompt) {
        responseDiv.textContent = 'Please enter a prompt.';
        return;
      }
      
      // Disable button and show loading
      sendButton.disabled = true;
      sendButton.textContent = 'Processing...';
      responseDiv.textContent = '🧠 Thinking... (This may take 30-60 seconds if using fallback AI)';
      
      try {
        // Add timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes timeout
        
        const res = await fetch('/api/mini-assistant', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: prompt, file }),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!res.ok) {
          throw new Error(`Server error: ${res.status} ${res.statusText}`);
        }
        
        const data = await res.json();
        if (data.success) {
          responseDiv.textContent = data.response;
          // Clear the input after successful response
          document.getElementById('miniAssistantPrompt').value = '';
        } else {
          responseDiv.textContent = '❌ ' + (data.error || 'Assistant error');
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          responseDiv.textContent = '❌ Request timed out after 2 minutes. Try a shorter prompt or check your connection.';
        } else {
          responseDiv.textContent = '❌ Could not connect to backend: ' + error.message;
        }
        console.error('Mini Assistant Error:', error);
      } finally {
        // Re-enable button
        sendButton.disabled = false;
        sendButton.textContent = 'Send to Assistant';
      }
    };
})();
