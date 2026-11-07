# Multi-stage Dockerfile for production-ready FastAPI deployment
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md ./
COPY sentinel_review ./sentinel_review
RUN python -m pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN adduser --disabled-password --gecos '' appuser
COPY --from=builder /install /usr/local
COPY --from=builder /app /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1
CMD ["uvicorn", "sentinel_review.api:app", "--host", "0.0.0.0", "--port", "8000"]
