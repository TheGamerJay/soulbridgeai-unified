# Install Ollama for Free AI Users

## Step 1: Install Ollama (Windows)

1. **Download Ollama**: Go to https://ollama.com/download and download the Windows installer
2. **Run the installer**: Follow the installation wizard
3. **Verify installation**: Open Command Prompt and run:
   ```bash
   ollama --version
   ```

## Step 2: Pull AI Model

Open Command Prompt and run:
```bash
# Download a good quality model (recommended)
ollama pull llama3:8b-instruct

# Alternative: Smaller/faster model
ollama pull mistral:7b-instruct
```

## Step 3: Set Environment Variables

Add these to your environment variables:
```bash
LLM_BASE=http://localhost:11434
FREE_COMPANION_MODEL=llama3:8b-instruct
COMP_MAX_TOKENS=350
```

**How to set on Windows:**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Click "New" under "System Variables"
4. Add each variable above

## Step 4: Start Ollama Service

Ollama should start automatically. If not:
```bash
ollama serve
```

## Step 5: Test Installation

1. **Test Ollama directly**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Test via your app**:
   - Visit: http://localhost:5000/api/llm/health
   - Should show: `{"success": true, "models": ["llama3:8b-instruct"]}`

3. **Test with free user**:
   - Login as free user
   - Ask: "What is 5 + 5?"
   - Should get AI response instead of template

## What This Gives You

✅ **Free users get real AI conversations** (not templates)
✅ **Zero OpenAI costs** (runs locally)
✅ **Better first impressions** → higher conversion rates
✅ **Automatic fallback** to templates if Ollama is down
✅ **Clear upgrade path** to Growth/Max for faster AI

## Troubleshooting

**Ollama not starting:**
```bash
# Check if running
ollama list

# Restart service
ollama serve
```

**Model not found:**
```bash
# List installed models
ollama list

# Pull the model again
ollama pull llama3:8b-instruct
```

**Port conflicts:**
- Default port is 11434
- Change with: `OLLAMA_HOST=0.0.0.0:11435`

## Production Deployment

For production, consider:
- Running Ollama in Docker
- Using a dedicated AI server
- Load balancing multiple Ollama instances
- Monitoring memory usage (models use 4-8GB RAM)