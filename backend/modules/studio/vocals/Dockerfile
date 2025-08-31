FROM python:3.10
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install core Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    numpy \
    soundfile \
    pyyaml \
    requests

# Install PyTorch CPU (DiffSinger compatible)
RUN pip install --no-cache-dir \
    torch==1.13.1+cpu \
    torchaudio==0.13.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Clone DiffSinger repository
RUN git clone https://github.com/MoonInTheRiver/DiffSinger.git /app/DiffSinger

# Install DiffSinger dependencies
WORKDIR /app/DiffSinger
RUN pip install --no-cache-dir -r requirements.txt || true

# Return to app directory
WORKDIR /app
COPY vocals_app.py .

# Set environment variables
ENV DS_HOME=/models/diffsinger
ENV PYTHONPATH=/app/DiffSinger

EXPOSE 7002
CMD ["uvicorn", "vocals_app:app", "--host", "0.0.0.0", "--port", "7002"]