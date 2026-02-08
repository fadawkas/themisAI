# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=180 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1

# libgomp1 is needed by faiss-cpu
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install CPU-only PyTorch first, then the rest (with retries)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary \
      --index-url https://download.pytorch.org/whl/cpu \
      torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 && \
    for i in 1 2 3 4 5; do \
      pip install --prefer-binary -r requirements.txt && break || sleep 10; \
    done

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--reload"]
