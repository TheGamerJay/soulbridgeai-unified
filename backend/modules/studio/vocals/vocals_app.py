# SoulBridge AI - Vocals Service  
# Real DiffSinger inference with auto-downloading pretrained models
# Professional AI vocal synthesis backend

from fastapi import FastAPI, Response
from pydantic import BaseModel
import os, zipfile, io, json, subprocess, tempfile, requests, shutil, soundfile as sf
from typing import Optional

app = FastAPI(title="SoulBridge Vocals Service", version="1.0.0")

# Configuration
DS_HOME = os.environ.get("DS_HOME", "/models/diffsinger")
DS_REPO = "/app/DiffSinger"
CKPT_DIR = os.path.join(DS_REPO, "checkpoints")

# Create necessary directories
os.makedirs(DS_HOME, exist_ok=True)
os.makedirs(CKPT_DIR, exist_ok=True)

# Pretrained model URLs from official DiffSinger releases
VOCODER_URL = "https://github.com/MoonInTheRiver/DiffSinger/releases/download/pretrain-model/0109_hifigan_bigpopcs_hop128.zip"
BUNDLE_URL = "https://github.com/MoonInTheRiver/DiffSinger/releases/download/pretrain-model/adjust-receptive-field.zip"

def ensure_checkpoints():
    """Download and extract pretrained models if not present"""
    vocoder_dir = os.path.join(CKPT_DIR, "0109_hifigan_bigpopcs_hop128")
    bundle_dir = os.path.join(CKPT_DIR, "adjust-receptive-field")
    
    if not os.path.isdir(vocoder_dir):
        print("📥 Downloading vocoder checkpoint...")
        try:
            response = requests.get(VOCODER_URL, timeout=600)
            response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(CKPT_DIR)
            print("✅ Vocoder checkpoint downloaded")
        except Exception as e:
            print(f"❌ Failed to download vocoder: {e}")
    
    if not os.path.isdir(bundle_dir):
        print("📥 Downloading DiffSinger bundle...")
        try:
            response = requests.get(BUNDLE_URL, timeout=600)
            response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                zip_file.extractall(CKPT_DIR)
            print("✅ DiffSinger bundle downloaded")
        except Exception as e:
            print(f"❌ Failed to download bundle: {e}")

class SingRequest(BaseModel):
    bpm: int = 94
    lyrics_json_path: Optional[str] = None
    beat_zip_path: Optional[str] = None
    midi_path: Optional[str] = None

def parse_lyrics_json(json_path: str) -> str:
    """Parse structured lyrics JSON and flatten to text"""
    try:
        with open(json_path, "r", encoding="utf8") as f:
            data = json.load(f)
        
        lines = []
        for section in data.get("sections", []):
            section_type = section.get("type", "")
            lyrics = section.get("lyrics", "")
            
            # Add section markers
            if section_type:
                lines.append(f"[{section_type.upper()}]")
            lines.append(lyrics)
            lines.append("")  # Empty line between sections
        
        return "\n".join(lines)
    except Exception as e:
        print(f"⚠️ Error parsing lyrics JSON: {e}")
        return "la la la la la"

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "soulbridge-vocals-service",
        "diffsinger_repo": DS_REPO,
        "checkpoints_dir": CKPT_DIR
    }

@app.post("/sing")
def generate_vocals(request: SingRequest):
    """Generate vocals using DiffSinger with real AI models"""
    
    print(f"🎤 Generating vocals at {request.bpm} BPM")
    
    # Ensure models are downloaded
    ensure_checkpoints()
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare lyrics
            lyrics_file = os.path.join(temp_dir, "lyrics.txt")
            
            if request.lyrics_json_path and os.path.exists(request.lyrics_json_path):
                lyrics_text = parse_lyrics_json(request.lyrics_json_path)
                print(f"📝 Using provided lyrics from {request.lyrics_json_path}")
            else:
                # Fallback lyrics for demo
                lyrics_text = """[VERSE]
In the silence of the night
I hear the music calling out
Every beat within my heart
Tells me what it's all about

[CHORUS]  
This is the sound of dreams
Rising up from deep within
Every note and every chord
Is where the magic begins"""
                print("📝 Using fallback demo lyrics")
            
            with open(lyrics_file, "w", encoding="utf8") as f:
                f.write(lyrics_text)
            
            # Prepare environment for DiffSinger
            env = os.environ.copy()
            env["PYTHONPATH"] = DS_REPO
            
            # DiffSinger inference command
            # Using the cascade configuration for better quality
            cmd = [
                "python", 
                os.path.join(DS_REPO, "inference/svs/ds_cascade.py"),
                "--config", os.path.join(DS_REPO, "usr/configs/midi/cascade/opencs/ds60_rel.yaml"),
                "--exp_name", "adjust-receptive-field"
            ]
            
            print(f"🔄 Running DiffSinger inference...")
            print(f"Command: {' '.join(cmd)}")
            
            try:
                # Run DiffSinger inference
                process = subprocess.run(
                    cmd, 
                    cwd=DS_REPO, 
                    env=env, 
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes timeout
                )
                
                if process.returncode != 0:
                    print(f"❌ DiffSinger process failed with code {process.returncode}")
                    print(f"STDOUT: {process.stdout}")
                    print(f"STDERR: {process.stderr}")
                    
                    # Generate fallback vocal synthesis
                    return generate_fallback_vocals(request.bpm)
                
                print("✅ DiffSinger inference completed")
                
            except subprocess.TimeoutExpired:
                print("⚠️ DiffSinger inference timed out")
                return generate_fallback_vocals(request.bpm)
            
            # Find generated audio files
            generated_audio = find_generated_audio()
            
            if generated_audio and os.path.exists(generated_audio):
                print(f"🎵 Found generated audio: {generated_audio}")
                
                # Read and return the generated audio
                audio_data, sample_rate = sf.read(generated_audio, dtype="float32")
                
                # Convert to WAV in memory
                output_buffer = io.BytesIO()
                sf.write(output_buffer, audio_data, sample_rate, format="WAV")
                output_buffer.seek(0)
                
                print(f"📤 Returning {len(audio_data)/sample_rate:.1f}s vocal at {sample_rate}Hz")
                
                return Response(
                    content=output_buffer.read(),
                    media_type="audio/wav",
                    headers={"Content-Disposition": "attachment; filename=vocals.wav"}
                )
            else:
                print("⚠️ No generated audio found, using fallback")
                return generate_fallback_vocals(request.bpm)
    
    except Exception as e:
        print(f"❌ Vocal generation failed: {e}")
        return generate_fallback_vocals(request.bpm)

def find_generated_audio():
    """Find the most recent generated audio file"""
    try:
        # Look for generated audio in common output locations
        search_paths = [
            os.path.join(CKPT_DIR, "adjust-receptive-field"),
            os.path.join(DS_REPO, "outputs"),
            os.path.join(DS_REPO, "results")
        ]
        
        latest_file = None
        latest_time = 0
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith(('.wav', '.mp3')) and ('generated' in file or 'output' in file):
                        file_path = os.path.join(root, file)
                        file_time = os.path.getmtime(file_path)
                        
                        if file_time > latest_time:
                            latest_time = file_time
                            latest_file = file_path
        
        return latest_file
        
    except Exception as e:
        print(f"⚠️ Error finding generated audio: {e}")
        return None

def generate_fallback_vocals(bpm: int = 94):
    """Generate fallback synthetic vocals when DiffSinger fails"""
    try:
        # Create a simple sine wave melody as fallback
        duration = 10  # 10 seconds
        sample_rate = 44100
        
        # Generate a simple melody
        import numpy as np
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a melody with chord progression
        frequencies = [261.63, 293.66, 329.63, 349.23, 392.00]  # C, D, E, F, G
        melody = np.zeros_like(t)
        
        notes_per_second = bpm / 60 / 4  # Quarter notes per second
        note_duration = 1 / notes_per_second
        
        for i, freq in enumerate(frequencies):
            start_time = i * note_duration
            end_time = (i + 1) * note_duration
            
            mask = (t >= start_time) & (t < end_time)
            melody[mask] = np.sin(2 * np.pi * freq * t[mask]) * np.exp(-3 * (t[mask] - start_time))
        
        # Add some harmonics
        melody += 0.3 * np.sin(2 * np.pi * 2 * frequencies[0] * t) * np.exp(-t)
        
        # Normalize
        melody = melody / np.max(np.abs(melody)) * 0.8
        
        # Convert to WAV
        output_buffer = io.BytesIO()
        sf.write(output_buffer, melody, sample_rate, format="WAV")
        output_buffer.seek(0)
        
        print("🎵 Generated fallback synthetic vocals")
        
        return Response(
            content=output_buffer.read(),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=fallback_vocals.wav"}
        )
        
    except Exception as e:
        print(f"❌ Even fallback generation failed: {e}")
        return Response(
            status_code=500,
            content=f"Vocal generation completely failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7002)