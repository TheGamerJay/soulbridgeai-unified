const vscode = require('vscode');

function activate(context) {
  let disposable = vscode.commands.registerCommand('mini-assistant.start', function () {
    const panel = vscode.window.createWebviewPanel(
      'miniAssistant',
      'Mini Assistant',
      vscode.ViewColumn.One,
      { enableScripts: true }
    );

    panel.webview.html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mini Assistant</title>
</head>
<body style="font-family:sans-serif;padding:16px;background:#1e1e1e;color:white;">
  <div style="display:flex;align-items:center;margin-bottom:16px;">
    <h2 style="margin:0;">🧠 Mini Assistant</h2>
    <div id="status" style="margin-left:auto;padding:4px 8px;border-radius:4px;font-size:12px;">🟢 Ready</div>
  </div>
  
  <div id="rateLimit" style="display:none;background:#ff6b6b;color:white;padding:8px;border-radius:6px;margin-bottom:16px;">
    🚨 <strong>Claude Rate Limited</strong> - Mini Helper mode active. Reduced functionality but still operational!
  </div>
  
  <label>📂 File Path (optional):</label><br>
  <input type="text" id="file" style="width:100%;padding:8px;background:#2d2d2d;color:white;border:1px solid #444;border-radius:4px;" placeholder="Enter file path for editing..."><br><br>
  
  <label>🧠 Prompt:</label><br>
  <textarea id="prompt" rows="6" style="width:100%;padding:8px;background:#2d2d2d;color:white;border:1px solid #444;border-radius:4px;" placeholder="Ask me anything about your code..."></textarea><br><br>
  
  <div style="display:flex;gap:8px;">
    <button onclick="send()" id="sendBtn" style="background:#00b894;color:white;padding:8px 12px;border:none;border-radius:6px;flex-grow:1;">Send to Assistant</button>
    <button onclick="checkStatus()" style="background:#6c5ce7;color:white;padding:8px 12px;border:none;border-radius:6px;">Check Status</button>
  </div>
  
  <pre id="output" style="margin-top:20px;background:#2d2d2d;padding:10px;border-radius:6px;max-height:400px;overflow:auto;white-space:pre-wrap;"></pre>

  <script>
    const vscode = acquireVsCodeApi();
    let isRateLimited = false;
    
    function updateStatus(limited, message = '') {
      const status = document.getElementById('status');
      const rateLimitDiv = document.getElementById('rateLimit');
      const sendBtn = document.getElementById('sendBtn');
      
      if (limited) {
        status.textContent = '🔴 Rate Limited';
        status.style.background = '#ff6b6b';
        rateLimitDiv.style.display = 'block';
        sendBtn.textContent = 'Send to Mini Helper';
        sendBtn.style.background = '#fd9644';
        isRateLimited = true;
      } else {
        status.textContent = '🟢 Ready';
        status.style.background = '#00b894';
        rateLimitDiv.style.display = 'none';
        sendBtn.textContent = 'Send to Assistant';
        sendBtn.style.background = '#00b894';
        isRateLimited = false;
      }
      
      if (message) {
        document.getElementById('output').textContent = message;
      }
    }
    
    function send() {
      const file = document.getElementById('file').value;
      const prompt = document.getElementById('prompt').value;
      
      if (!prompt.trim()) {
        document.getElementById('output').textContent = '❌ Please enter a prompt';
        return;
      }
      
      document.getElementById('output').textContent = '🤔 Thinking...';
      vscode.postMessage({ command: 'sendPrompt', file, prompt });
    }
    
    function checkStatus() {
      document.getElementById('output').textContent = '📊 Checking status...';
      vscode.postMessage({ command: 'checkStatus' });
    }
    
    window.addEventListener('message', event => {
      const message = event.data;
      
      if (message.command === 'response') {
        document.getElementById('output').textContent = message.output;
        
        // Check if response indicates rate limiting
        if (message.output.includes('Rate limit') || message.output.includes('Mini Helper')) {
          updateStatus(true);
        } else if (message.output.includes('Claude 3 Haiku used successfully')) {
          updateStatus(false);
        }
      }
      
      if (message.command === 'statusUpdate') {
        updateStatus(message.rateLimited, message.statusMessage);
      }
    });
    
    // Check status on load
    setTimeout(checkStatus, 1000);
  </script>
</body>
</html>`;

    panel.webview.onDidReceiveMessage(
      async (message) => {
        try {
          if (message.command === 'sendPrompt') {
            const res = await fetch('http://localhost:5000/api/mini-assistant', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                message: message.prompt,
                file: message.file
              })
            });
            const data = await res.json();
            
            let output = data.output || data.response || '[No output]';
            
            // Check for rate limit indicators in response
            const isRateLimited = output.includes('Rate limit') || 
                                 output.includes('Mini Helper') || 
                                 output.includes('🚨') ||
                                 output.includes('🤖');
            
            panel.webview.postMessage({ 
              command: 'response', 
              output: output,
              rateLimited: isRateLimited
            });
            
          } else if (message.command === 'checkStatus') {
            // Check status endpoint
            try {
              const res = await fetch('http://localhost:5000/api/mini-assistant-status');
              const data = await res.json();
              
              const statusMessage = `📊 Status Check Complete
              
Backend: ${data.backend_status || 'Unknown'}
Claude API: ${data.claude_status || 'Unknown'}
Rate Limited: ${data.rate_limited ? 'Yes' : 'No'}
Last Updated: ${data.timestamp || 'Unknown'}`;
              
              panel.webview.postMessage({ 
                command: 'statusUpdate',
                rateLimited: data.rate_limited || false,
                statusMessage: statusMessage
              });
              
            } catch (err) {
              panel.webview.postMessage({ 
                command: 'statusUpdate',
                rateLimited: false,
                statusMessage: '❌ Could not check status: ' + err.message
              });
            }
          }
        } catch (err) {
          panel.webview.postMessage({ 
            command: 'response', 
            output: '❌ Error: ' + err.message,
            rateLimited: false
          });
        }
      },
      undefined,
      context.subscriptions
    );
  });

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = { activate, deactivate };