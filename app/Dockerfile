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
# Stage 2: Compile Tailwind CSS (standalone CLI, no Node)
# ========================================================
FROM debian:bookworm-slim AS css-builder

ARG TARGETARCH
ARG TAILWIND_VERSION=v4.3.3
ARG TAILWIND_SHA256_X64=dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a
ARG TAILWIND_SHA256_ARM64=55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Download the pinned binary for the target platform and verify its checksum
RUN case "${TARGETARCH:-amd64}" in \
      amd64) TW_ARCH=x64;   TW_SHA="${TAILWIND_SHA256_X64}" ;; \
      arm64) TW_ARCH=arm64; TW_SHA="${TAILWIND_SHA256_ARM64}" ;; \
      *) echo "Unsupported arch: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl -fsSL -o /usr/local/bin/tailwindcss \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-${TW_ARCH}" && \
    echo "${TW_SHA}  /usr/local/bin/tailwindcss" | sha256sum -c - && \
    chmod +x /usr/local/bin/tailwindcss

WORKDIR /src
COPY frontend ./frontend
RUN tailwindcss -i frontend/src/input.css -o frontend/styles.css --minify && \
    rm -rf frontend/src

# ========================================================
# Stage 3: Hardened Runtime stage
# ========================================================
FROM python:3.11-slim AS runtime

# Security hardening environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    MLFLOW_TRACKING_DIR=/tmp/mlflow \
    MLFLOW_HOME=/tmp/mlflow \
    GIT_PYTHON_REFRESH=quiet

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

# Copy frontend static assets (with compiled CSS, without Tailwind sources)
COPY --from=css-builder --chown=appuser:appgroup /src/frontend /app/frontend

# Drop privileges to non-root
USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
