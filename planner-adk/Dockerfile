FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirement.txt ./requirement.txt
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

# Expose the new port
EXPOSE 8002

# Run FastAPI app on port 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
