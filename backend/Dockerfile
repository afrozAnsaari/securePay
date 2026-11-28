# SecurePay API image.
#
# Build:  docker build -t securepay-api ./backend
# Run:    docker run --env-file backend/.env -p 8000:8000 securepay-api
#
# Base images are pinned by digest so every build uses exactly the same OS
# and Python. To update: docker pull python:3.11-slim, then copy the new
# digest from `docker inspect --format '{{index .RepoDigests 0}}' python:3.11-slim`.

# ---- build stage: install dependencies into a virtualenv (never shipped) ----
FROM python:3.11-slim@sha256:7032841967d07aa3353905945dc186901c89b6b319c61425f4439f677a4a8a34 AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---- runtime stage: only the virtualenv and the app code ----
FROM python:3.11-slim@sha256:7032841967d07aa3353905945dc186901c89b6b319c61425f4439f677a4a8a34

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Uvicorn reads these, so the platform can override them without a new image.
    # Render sets PORT; locally it is 8000. WEB_CONCURRENCY = number of worker processes.
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    WEB_CONCURRENCY=2 \
    LOG_FORMAT=json

WORKDIR /app

# Run as an unprivileged user, never root.
RUN useradd --create-home --uid 10001 app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app scripts ./scripts
COPY --chown=app:app src ./src

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"UVICORN_PORT\", \"8000\")}/health/live', timeout=2)"

# Exec form (a JSON list, no shell in between), so Docker's stop signal
# (SIGTERM) reaches uvicorn directly and it can finish in-flight requests.
# --no-access-log: our middleware already logs every request with its
# request ID, so uvicorn's plain-text access log would only duplicate it.
CMD ["uvicorn", "src.api.app:app", \
     "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--timeout-graceful-shutdown", "20", \
     "--no-access-log"]
