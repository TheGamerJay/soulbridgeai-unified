#!/bin/sh

# Start Ollama in background
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 15

# Pull the model we need
echo "Pulling llama3:8b-instruct model..."
ollama pull llama3:8b-instruct || echo "Model pull failed, continuing..."

# Keep the container running
echo "Ollama is ready!"
wait