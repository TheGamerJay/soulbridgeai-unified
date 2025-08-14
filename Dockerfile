FROM ollama/ollama:latest

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_ORIGINS=*

# Expose port
EXPOSE 11434

# Start Ollama directly
CMD ["ollama", "serve"]