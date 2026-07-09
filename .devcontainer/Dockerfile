FROM python:latest

# Install PostgreSQL client
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash vscode

WORKDIR /workspace
