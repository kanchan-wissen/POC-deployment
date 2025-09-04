FROM docker.n8n.io/n8nio/n8n:latest

# Set timezone
ENV GENERIC_TIMEZONE=Asia/Kolkata

# Critical environment variables for Cloud Run
ENV N8N_HOST=0.0.0.0
ENV N8N_PORT=5678

# Start n8n
CMD ["n8n"]