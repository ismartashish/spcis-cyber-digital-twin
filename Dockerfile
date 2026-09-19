FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install normal dependencies first
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

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]