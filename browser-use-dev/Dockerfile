FROM python:3.11-slim
 
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl gnupg unzip wget git libnss3 libxss1 libasound2 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxcomposite1 libxrandr2 \
    libgbm1 libgtk-3-0 libxdamage1 libxfixes3 libx11-xcb1 libxext6 libxrender1 \
    xvfb x11vnc supervisor net-tools fluxbox python3-pip \
    && rm -rf /var/lib/apt/lists/*
 
# Install noVNC and websockify
RUN mkdir -p /usr/share/novnc && \
    git clone https://github.com/novnc/noVNC.git /usr/share/novnc && \
    git clone https://github.com/novnc/websockify.git /usr/share/novnc/utils/websockify && \
    pip install /usr/share/novnc/utils/websockify
 
# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Install Playwright and Chromium with proper font dependencies
RUN pip install playwright
RUN apt-get update && apt-get install -y \
    fonts-liberation fonts-noto-color-emoji fonts-noto-cjk \
    fonts-freefont-ttf fonts-unifont xfonts-scalable xfonts-cyrillic \
    && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium
 
# Copy application code and supervisor config
COPY app /app
COPY app/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
 
# Set working directory
WORKDIR /app
 
# Set the display for Xvfb
ENV DISPLAY=:99
 
# Start supervisor to manage all processes
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]