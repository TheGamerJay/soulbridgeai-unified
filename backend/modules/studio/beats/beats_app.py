# SoulBridge AI - Beats Service
# Real MusicGen + MIDI stems generation + optional Demucs separation
# Professional music production backend

from fastapi import FastAPI, Body, Response
from pydantic import BaseModel
from transformers import AutoProcessor, MusicgenForConditionalGeneration
import torch, tempfile, os, io, zipfile, soundfile as sf
import numpy as np
import pretty_midi, mido, random, subprocess, json

app = FastAPI(title="SoulBridge Beats Service", version="1.0.0")

# Use CPU-friendly MusicGen model (can be upgraded to larger models)
MODEL_ID = "facebook/musicgen-small"
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = MusicgenForConditionalGeneration.from_pretrained(MODEL_ID)
model.to(torch.device("cpu"))

print(f"✅ Loaded MusicGen model: {MODEL_ID}")

class BeatRequest(BaseModel):
    prompt: str
    bpm: int = 94
    key: str = "A minor"
    seconds: int = 15
    demucs: bool = False

def generate_midi_stems(bpm: int, key: str = "A minor"):
    """Generate MIDI stems for drums, bass, chords, and lead"""
    pm = pretty_midi.PrettyMIDI()
    
    # Create instruments
    instruments = {
        "drums": pretty_midi.Instrument(program=0, is_drum=True),
        "bass": pretty_midi.Instrument(program=34),   # Fingered bass
        "chords": pretty_midi.Instrument(program=0),  # Grand piano
        "lead": pretty_midi.Instrument(program=81)    # Saw lead
    }
    
    # Calculate timing
    beat_duration = 60.0 / bpm
    bars = 8  # 8-bar loop
    
    # Generate drum pattern (kick, snare, hi-hat)
    for bar in range(bars):
        bar_start = bar * 4 * beat_duration
        for beat in range(4):
            beat_time = bar_start + beat * beat_duration
            
            # Kick on beats 1 and 3
            if beat in [0, 2]:
                instruments["drums"].notes.append(
                    pretty_midi.Note(100, 36, beat_time, beat_time + 0.1)
                )
            
            # Snare on beats 2 and 4
            if beat in [1, 3]:
                instruments["drums"].notes.append(
                    pretty_midi.Note(90, 38, beat_time, beat_time + 0.1)
                )
            
            # Hi-hat on every eighth note
            for eighth in range(2):
                hat_time = beat_time + eighth * beat_duration / 2
                instruments["drums"].notes.append(
                    pretty_midi.Note(70, 42, hat_time, hat_time + 0.05)
                )
    
    # Generate bass line (root notes)
    root_note = 57 if "A" in key else 60  # A3 or C4
    for bar in range(bars):
        bar_start = bar * 4 * beat_duration
        for beat in range(4):
            note_start = bar_start + beat * beat_duration
            note_end = note_start + beat_duration
            instruments["bass"].notes.append(
                pretty_midi.Note(90, root_note, note_start, note_end)
            )
    
    # Generate chord progression (triads)
    if "minor" in key.lower():
        chord_notes = [57, 60, 64]  # A minor triad
    else:
        chord_notes = [60, 64, 67]  # C major triad
    
    for bar in range(bars):
        bar_start = bar * 4 * beat_duration
        # Whole note chords
        for note in chord_notes:
            instruments["chords"].notes.append(
                pretty_midi.Note(80, note, bar_start, bar_start + 4 * beat_duration)
            )
    
    # Generate lead melody (scale-based)
    scale_notes = [57, 59, 60, 62, 64, 65, 67, 69] if "minor" in key.lower() else [60, 62, 64, 65, 67, 69, 71, 72]
    
    for step in range(32):  # 32 eighth notes
        note_start = step * beat_duration / 2
        note_end = note_start + beat_duration / 2
        note_pitch = random.choice(scale_notes)
        instruments["lead"].notes.append(
            pretty_midi.Note(85, note_pitch, note_start, note_end)
        )
    
    # Add instruments to MIDI
    for instrument in instruments.values():
        pm.instruments.append(instrument)
    
    return pm, instruments

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "soulbridge-beats-service",
        "model": MODEL_ID,
        "device": "cpu"
    }

@app.post("/generate")
def generate_beat(request: BeatRequest):
    """Generate beat with MusicGen + MIDI stems + optional Demucs separation"""
    
    print(f"🎵 Generating beat: {request.prompt} ({request.bpm} BPM, {request.key})")
    
    try:
        # 1. Generate audio with MusicGen
        inputs = processor(
            text=[request.prompt], 
            padding=True, 
            return_tensors="pt"
        )
        
        # Calculate tokens needed for duration (approximately 50 tokens per second)
        max_tokens = request.seconds * 50
        
        audio_values = model.generate(
            **inputs, 
            do_sample=True, 
            guidance_scale=3.0, 
            max_new_tokens=max_tokens
        )
        
        # Extract mono audio
        audio = audio_values[0, 0].cpu().numpy()
        sample_rate = model.config.audio_encoder.sampling_rate if hasattr(model.config, "audio_encoder") else 32000
        
        print(f"✅ Generated {len(audio)/sample_rate:.1f}s audio at {sample_rate}Hz")
        
        # 2. Generate MIDI stems
        midi_file, instruments = generate_midi_stems(request.bpm, request.key)
        
        print(f"✅ Generated MIDI stems: {list(instruments.keys())}")
        
        # 3. Create output package
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save main audio
            audio_path = os.path.join(temp_dir, "beat.wav")
            sf.write(audio_path, audio, sample_rate)
            
            # Save individual MIDI tracks
            midi_paths = {}
            for name, instrument in instruments.items():
                single_midi = pretty_midi.PrettyMIDI()
                single_midi.instruments.append(instrument)
                midi_path = os.path.join(temp_dir, f"{name}.mid")
                single_midi.write(midi_path)
                midi_paths[name] = midi_path
            
            # Optional Demucs stems separation
            stems_dir = None
            if request.demucs:
                print("🎛️ Running Demucs stem separation...")
                stems_output = os.path.join(temp_dir, "stems")
                try:
                    subprocess.run([
                        "python", "-m", "demucs.separate", 
                        "-d", "cpu", 
                        "-o", stems_output, 
                        audio_path
                    ], check=True, timeout=300)
                    stems_dir = stems_output
                    print("✅ Demucs separation completed")
                except subprocess.TimeoutExpired:
                    print("⚠️ Demucs separation timed out")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ Demucs separation failed: {e}")
            
            # Package everything into ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add main beat
                zip_file.write(audio_path, "beat.wav")
                
                # Add MIDI stems
                for name, path in midi_paths.items():
                    zip_file.write(path, f"{name}.mid")
                
                # Add Demucs stems if available
                if stems_dir and os.path.exists(stems_dir):
                    for root, dirs, files in os.walk(stems_dir):
                        for file in files:
                            if file.endswith('.wav'):
                                file_path = os.path.join(root, file)
                                arc_name = f"stems/{file}"
                                zip_file.write(file_path, arc_name)
                
                # Add metadata
                metadata = {
                    "prompt": request.prompt,
                    "bpm": request.bpm,
                    "key": request.key,
                    "duration_seconds": request.seconds,
                    "sample_rate": sample_rate,
                    "includes_demucs": request.demucs and stems_dir is not None,
                    "generated_by": "SoulBridge AI Mini Studio"
                }
                zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            zip_buffer.seek(0)
            
            print(f"📦 Beat package created ({len(zip_buffer.getvalue())} bytes)")
            
            return Response(
                content=zip_buffer.read(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=beat_{request.bpm}bpm.zip"}
            )
    
    except Exception as e:
        print(f"❌ Beat generation failed: {e}")
        return Response(
            status_code=500,
            content=f"Beat generation failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7001)