FROM python:3.12-slim

# Install PostgreSQL and MQTT client tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mosquitto-clients \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash vscode

WORKDIR /workspace
