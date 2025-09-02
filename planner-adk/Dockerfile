# --- planner/Dockerfile ---
FROM python:3.11-slim
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
 
WORKDIR /app
 
# deps
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt
 
# app
COPY . .
 
EXPOSE 8002
 
# optional: nicer shutdowns
STOPSIGNAL SIGINT
 
# simple TCP healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD python -c "import socket,sys; s=socket.socket(); s.settimeout(3); s.connect(('127.0.0.1',8001)); s.close()"
 
# IMPORTANT: correct JSON-form CMD
CMD ["python","-m","uvicorn","main:app","--host","0.0.0.0","--port","8002","--proxy-headers"]
 
