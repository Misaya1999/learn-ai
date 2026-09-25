FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt \
    && groupadd --system learnai \
    && useradd --system --gid learnai --home-dir /app learnai

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN mkdir -p /app/storage/documents \
    && chown -R learnai:learnai /app \
    && chmod 0555 /app/docker-entrypoint.sh

USER learnai

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
