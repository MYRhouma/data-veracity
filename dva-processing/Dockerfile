FROM python:3.12-slim AS build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

# Set working directory
WORKDIR /app/

# Install dependencies
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./dva-processing/uv.lock,target=uv.lock \
    --mount=type=bind,source=./dva-processing/pyproject.toml,target=pyproject.toml \
    uv sync \
        --frozen \
	--no-install-project \
	--compile-bytecode \
	--no-editable

# Copy app files
COPY ./dva-processing/ /app/

# Sync project
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --frozen \
	--compile-bytecode \
	--no-editable

# ----------------------------------------------------------------
FROM python:3.12-slim

# Install netcat for healthcheck
RUN apt-get update && \
    apt-get install -y \
        --no-install-recommends \
	netcat-openbsd=1.* \
    && rm -rf /var/lib/apt/lists/

# Copy built project
COPY --from=build --chown=app:app /app/.venv/ /app/.venv/

# Run app
ENTRYPOINT ["/app/.venv/bin/dva-processing"]

EXPOSE 5000/tcp
