# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalar dependencias en un entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="filesystem-mcp" \
      org.opencontainers.image.description="MCP Filesystem server con FastMCP" \
      org.opencontainers.image.version="1.0.0"

# Usuario sin privilegios
RUN useradd --create-home --shell /bin/bash mcpuser

# Copiar entorno virtual y código fuente
COPY --from=builder /opt/venv /opt/venv
COPY src/ /app/src/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FS_ROOT="/workspace" \
    MAX_FILE_SIZE_MB="10"

# Volumen para persistir los archivos
VOLUME ["/workspace"]

# Directorio de trabajo
WORKDIR /app

USER mcpuser

# El MCP se comunica por stdio — no expone puertos
ENTRYPOINT ["python", "src/server.py"]
