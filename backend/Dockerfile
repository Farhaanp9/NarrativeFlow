FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ../README.md ./
RUN uv sync --frozen --no-dev

COPY narrativeflow/ narrativeflow/

FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app /app

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "narrativeflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
