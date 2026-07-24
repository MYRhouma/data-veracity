FROM python:3.12-slim AS build

# Install uv (mirrors dva-processing/Dockerfile style)
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

WORKDIR /app/

# Install dependencies (cached layer)
RUN \
    --mount=type=cache,target=/root/.cache/uv2 \
    --mount=type=bind,source=./vla-manager-api/pyproject.toml,target=pyproject.toml \
    uv pip install --system \
        "fastapi~=0.136.3" \
        "asyncpg>=0.30.0" \
        "pydantic>=2.10.6" \
        "pydantic-settings>=2.5.0" \
        "structlog>=25.1.0" \
        "uvicorn>=0.34.3" \
        "chevron>=0.14"

# Copy app files
COPY ./vla-manager-api/ /app/

# ----------------------------------------------------------------
FROM python:3.12-slim

# netcat for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd=1.* \
    && rm -rf /var/lib/apt/lists/

# Install uvicorn in the runtime stage (mirrors build stage)
COPY --from=build /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy installed packages + source from build stage
COPY --from=build --chown=app:app /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build --chown=app:app /app/src /app/src
COPY --from=build --chown=app:app /app/pyproject.toml /app/pyproject.toml

WORKDIR /app

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

# Hand-written OpenAPI spec — served at /swagger/openapi.yaml
COPY ./docs/spec/vla-manager-api.yaml /app/openapi.yaml
ENV VLA_MANAGER_OPENAPI_FILE=/app/openapi.yaml

# Run app via uvicorn. ``vla_manager_api.main:app`` is the FastAPI
# instance at module scope (see ``main.py``).
ENTRYPOINT ["uvicorn", "vla_manager_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000/tcp