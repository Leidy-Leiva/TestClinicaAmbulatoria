# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Runtime stage
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="agent-orquestador" \
      org.opencontainers.image.description="Agente Orquestador para Cierre de Turno" \
      org.opencontainers.image.version="1.0.0"

RUN useradd --create-home --shell /bin/bash agentuser

COPY --from=builder /opt/venv /opt/venv
COPY . /app/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

USER agentuser

ENTRYPOINT ["python", "agent.py"]