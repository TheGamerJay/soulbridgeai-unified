FROM ollama/ollama:latest

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_ORIGINS=*

# Create startup script
COPY scripts/start-ollama.sh /start-ollama.sh
RUN chmod +x /start-ollama.sh

# Expose port
EXPOSE 11434

# Start Ollama and pull model
CMD ["/start-ollama.sh"]