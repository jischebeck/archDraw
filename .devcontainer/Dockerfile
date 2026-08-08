FROM python:3.14-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 1. Install system utilities and Node.js (v20 LTS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    procps \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Astral uv (Fast Python Package Installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Install OpenCode globally via npm
RUN npm install -g opencode-ai@latest

# 4. Install Omnigent globally using uv
RUN uv pip install --system omnigent

# Install the Python language server
RUN npm install -g pyright

# Install OpenCode
RUN npm install -g opencode

# Set workspace directory
WORKDIR /workspace
