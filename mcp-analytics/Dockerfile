FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="clinica-analytics-mcp" \
      org.opencontainers.image.description="MCP Analytics server para clínica ambulatoria con FastMCP" \
      org.opencontainers.image.version="1.0.0"

RUN useradd --create-home --shell /bin/bash mcpuser

COPY --from=builder /opt/venv /opt/venv
COPY src/ /app/src/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH="/data/crud.db"

WORKDIR /app

USER mcpuser

ENTRYPOINT ["python", "src/server.py"]