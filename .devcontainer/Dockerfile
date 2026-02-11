ARG BASE_IMAGE="mcr.microsoft.com/devcontainers/python:1-3.12-bookworm"
FROM $BASE_IMAGE

# Global environment variables
ENV PYTHONDONTWRITEBYTECODE=1
    PYTHONUNBUFFERED=1
    UV_LINK_MODE=copy

# Install uv & uvx (High-performance Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=ghcr.io/astral-sh/uv:latest /uvx /usr/local/bin/uvx

# Update pip
RUN pip install --no-cache-dir --upgrade pip
