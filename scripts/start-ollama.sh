#!/bin/bash

# Start Ollama in background
ollama serve &

# Wait for Ollama to be ready
sleep 10

# Pull the model we need
ollama pull llama3:8b-instruct

# Keep the container running
wait