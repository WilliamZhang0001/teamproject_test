# Multi-stage Dockerfile for DoE-Assist

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.9-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY api/ ./api/
COPY database/ ./database/
COPY ml_engine/ ./ml_engine/
COPY literature_mining/ ./literature_mining/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose ports
EXPOSE 8000 8001 8002

# Default command
CMD ["python", "scripts/start_services.py"]
