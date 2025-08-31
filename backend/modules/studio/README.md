# SoulBridge AI - Mini Studio

Professional music production system with real AI models integrated into SoulBridge's modular architecture.

## Features

🎵 **Real AI Music Production**
- **MusicGen** for beat generation with MIDI stems
- **DiffSinger** for AI vocal synthesis  
- **OpenAI** for structured lyrics with Responses API
- **Demucs** for audio stem separation (optional)

🏗️ **Professional Architecture**
- Docker microservices (API, Beats, Vocals, Database)
- PostgreSQL with proper schemas and asset tracking
- File storage with version management
- Credit-based pricing system

🔐 **SoulBridge Integration**
- Gold tier exclusive access
- Artistic time credit system
- Session-based authentication
- Usage tracking and limits

## Quick Start

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and set your OPENAI_API_KEY
   ```

2. **Start services:**
   ```bash
   docker compose up --build
   ```

3. **Services will be available at:**
   - API: http://localhost:8080
   - Beats: http://localhost:7001
   - Vocals: http://localhost:7002

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SoulBridge    │    │   Mini Studio   │    │   AI Services   │
│   Main App      │ -> │   API Gateway   │ -> │   (Docker)      │
│                 │    │                 │    │                 │
│ • Auth          │    │ • Node/Express  │    │ • MusicGen     │
│ • Credits       │    │ • PostgreSQL    │    │ • DiffSinger   │
│ • Tier Control  │    │ • File Storage  │    │ • OpenAI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### SoulBridge Integration
- `GET /mini-studio` - Main studio interface (Gold tier required)
- `GET /api/mini-studio/status` - Get credits and service health
- `POST /api/mini-studio/project` - Ensure user project exists

### Music Production
- `POST /api/mini-studio/lyrics/generate` - Generate lyrics (5 credits)
- `POST /api/mini-studio/beats/compose` - Create beats + MIDI (10 credits)
- `POST /api/mini-studio/vocals/sing` - Synthesize vocals (10-25 credits)
- `POST /api/mini-studio/upload` - Upload user assets

### Library Management
- `GET /api/mini-studio/library` - Get user's music library
- `DELETE /api/mini-studio/library/<id>` - Delete asset
- `GET /api/mini-studio/export/<id>` - Download/export asset

## Credit System

**Lyrics Generation:** 5 credits
- Uses OpenAI Responses API with structured outputs
- Generates complete song structure with sections

**Beat Composition:** 10 credits  
- MusicGen generates audio (15-30 seconds)
- MIDI stems for drums, bass, chords, lead
- Optional Demucs separation (+0 credits)

**Vocal Synthesis:** Dynamic pricing
- Base: 10 credits
- +5 if no lyrics provided (auto-generates)
- +10 if no beat provided (uses silence)
- Uses DiffSinger for AI vocal synthesis

## Docker Services

### API Service (Node.js)
- Express.js with file upload support
- PostgreSQL integration
- SoulBridge authentication
- Asset management and storage

### Beats Service (Python + MusicGen)
- FastAPI with MusicGen transformers
- CPU-optimized for deployment
- MIDI stem generation
- Optional Demucs separation

### Vocals Service (Python + DiffSinger)
- FastAPI with DiffSinger inference
- Auto-downloads pretrained models
- Fallback synthesis for reliability
- Supports structured lyrics input

## Integration with SoulBridge

The Mini Studio module integrates seamlessly with SoulBridge's existing systems:

1. **Authentication:** Uses SoulBridge session management
2. **Credits:** Integrates with artistic time system
3. **Tier Control:** Gold tier exclusive with trial support
4. **Routes:** Flask blueprints for clean integration

## Development

### Local Development
```bash
# Start only database
docker compose up postgres

# Run services locally for development
cd api && npm install && npm run dev
cd beats && python beats_app.py
cd vocals && python vocals_app.py
```

### Production Deployment
```bash
# Full production stack
docker compose up --build -d

# Check service health
curl http://localhost:8080/health
curl http://localhost:7001/health
curl http://localhost:7002/health
```

## Model Information

- **MusicGen Small:** ~1.5GB, CPU-friendly, good quality
- **DiffSinger:** Professional vocal synthesis, auto-downloads checkpoints
- **OpenAI:** GPT-4 with structured outputs for lyrics

## File Structure

```
backend/modules/studio/
├── __init__.py              # Module exports
├── studio_service.py        # SoulBridge integration service
├── routes.py               # Flask blueprint routes
├── docker-compose.yml      # Full stack orchestration
├── .env.example           # Environment configuration
│
├── api/                   # Node.js API service
│   ├── Dockerfile
│   ├── package.json
│   ├── db.sql
│   └── src/index.js
│
├── beats/                 # Python MusicGen service
│   ├── Dockerfile
│   └── beats_app.py
│
├── vocals/                # Python DiffSinger service
│   ├── Dockerfile
│   └── vocals_app.py
│
├── storage/              # Asset storage (mounted volume)
└── models/               # AI model cache (mounted volume)
```

This professional Mini Studio system transforms SoulBridge into a complete music production platform with real AI capabilities!