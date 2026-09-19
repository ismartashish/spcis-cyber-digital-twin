# ============================================================
# Stage 1: Build React Frontend
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ .

RUN npm run build


# ============================================================
# Stage 2: Python FastAPI Backend
# ============================================================
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install non-PyTorch dependencies
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn>=0.23.0" \
    "numpy>=1.24" \
    "PyYAML>=6.0" \
    "gymnasium>=0.29" \
    "stable-baselines3>=2.0" \
    "z3-solver>=4.12"

# CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

# Copy backend
COPY . .

# Copy built React frontend into backend
COPY --from=frontend-build /frontend/dist /app/frontend/dist

EXPOSE 8000

# Render provides PORT
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]