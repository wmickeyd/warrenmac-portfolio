# ========================================================
# Stage 1: Build stage (compile dependencies)
# ========================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# ========================================================
# Stage 2: Hardened Runtime stage
# ========================================================
FROM python:3.11-slim AS runtime

# Security hardening environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Create non-root user and group with explicit UID/GID
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /home/appuser appuser && \
    mkdir -p /home/appuser /app && \
    chown -R appuser:appgroup /home/appuser /app

WORKDIR /app

# Copy installed wheels from builder
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copy application backend code
COPY --chown=appuser:appgroup backend /app/backend

# Copy frontend static assets
COPY --chown=appuser:appgroup frontend /app/frontend

# Drop privileges to non-root
USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
