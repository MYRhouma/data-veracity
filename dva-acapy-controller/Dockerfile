FROM python:3.12-slim AS build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/
# Install netcat for healthcheck
RUN apt-get update && apt-get install -y netcat-openbsd

# Set working directory
WORKDIR /app/

# Install dependencies
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./dva-acapy-controller/uv.lock,target=uv.lock \
    --mount=type=bind,source=./dva-acapy-controller/pyproject.toml,target=pyproject.toml \
    uv sync \
        --frozen \
	--no-install-project \
	--compile-bytecode \
	--no-editable

# Copy app files
COPY ./dva-acapy-controller/ /app/

# Sync project
RUN \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync \
        --frozen \
	--compile-bytecode \
	--no-editable

# Run app
CMD ["uv", "run", "uvicorn", "dva_acapy_controller.controller:app", "--host", "0.0.0.0", "--port", "8050", "--log-level", "debug"]
