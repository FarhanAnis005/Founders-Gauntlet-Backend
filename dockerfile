# ---------- base ----------
    FROM python:3.11-slim AS base
    ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1
    
    # common libs for wheels + SSL + mimetypes + (optional) PDFs
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl bash ca-certificates libmagic1 libffi-dev \
     && rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    
    # ---------- deps ----------
    FROM base AS deps
    COPY requirements.txt /app/requirements.txt
    RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt
    
    # prisma (python) client if you use it
    COPY prisma /app/prisma
    RUN python -m pip install prisma && python -m prisma generate
    
    # ---------- runtime ----------
    FROM base AS runtime
    # bring in site-packages & scripts from deps layer
    COPY --from=deps /usr/local/lib/python3.11 /usr/local/lib/python3.11
    COPY --from=deps /usr/local/bin /usr/local/bin
    
    # app source
    COPY . /app
    
    # process manager to run API + worker
    RUN pip install supervisor
    
    # Healthcheck (basic) — expects /health route below
    HEALTHCHECK --interval=30s --timeout=5s \
      CMD curl -fsS http://127.0.0.1:${PORT:-7860}/health || exit 1
    
    # Hugging Face sets PORT env; default 7860 helps local runs
    EXPOSE 7860
    
    # Allow changing ASGI module without rebuilding
    ENV APP_MODULE=app.main:app
    
    CMD ["supervisord", "-c", "/app/supervisord.conf"]
    