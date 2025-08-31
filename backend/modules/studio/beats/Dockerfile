FROM python:3.10
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    torch==2.3.1+cpu \
    torchaudio==2.3.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu \
    transformers>=4.41.0 \
    accelerate \
    huggingface_hub \
    soundfile \
    numpy \
    pretty_midi \
    mido \
    note_seq \
    demucs

COPY beats_app.py .
EXPOSE 7001
CMD ["uvicorn", "beats_app:app", "--host", "0.0.0.0", "--port", "7001"]