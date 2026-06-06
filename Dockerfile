# Dockerfile — London Civic Agent
# Build:  docker build -t london-civic-agent .
# Run:    docker run --gpus all -p 5050:5050 -p 8000:8000 london-civic-agent
#
# GPU access requires the NVIDIA Container Toolkit:
#   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Avoid interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3-pip \
        curl \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip --no-cache-dir

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ src/

# Copy data directory (JSON configs and RAG corpus)
COPY data/ data/

# Copy scraper database if present (optional — for dashboard)
COPY scraper/fixmystreet.db scraper/fixmystreet.db

# Expose ports: 5050 (dashboard), 8000 (API)
EXPOSE 5050 8000

# Environment defaults (override at runtime)
ENV MODEL_PROVIDER=mock
ENV PYTHONUNBUFFERED=1

# Default: start the dashboard
CMD ["python", "-m", "src.dashboard.app"]
