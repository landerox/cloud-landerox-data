# Global ARGs must be declared before the first FROM so they can drive
# stage selection. BuildKit does not allow variable expansion inside a
# `COPY --from=image:${VAR}` directive, so we resolve the uv image once
# in a named stage and copy from that name later.
#
# BASE_IMAGE is pinned by digest (multi-arch manifest list) for bit-exact
# reproducibility. The human-readable tag stays in the value so the line
# is still grep-friendly. To bump:
#   docker buildx imagetools inspect mcr.microsoft.com/devcontainers/python:1-3.13-bookworm
# and copy the top-level Digest into the @sha256: suffix below. Also
# update the matching arg in devcontainer.json.
ARG BASE_IMAGE="mcr.microsoft.com/devcontainers/python:1-3.13-bookworm@sha256:0aa711e570b306c02946cdda67587ce8c65978dbb65691341cbcfd4854dfcfff"
# UV_IMAGE is pinned by digest (multi-arch manifest list) for bit-exact
# reproducibility. The human-readable tag stays inline so the line is
# still grep-friendly. To bump:
#   docker buildx imagetools inspect ghcr.io/astral-sh/uv:<new-tag>
# and copy the top-level Digest into the @sha256: suffix below.
ARG UV_IMAGE="ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a"

# Stage 1: pull the uv binaries from the official Astral image at the
# pinned version. This stage is discarded after the COPY below; only the
# two binaries land in the final image.
FROM $UV_IMAGE AS uv-source

# Stage 2: the actual devcontainer image.
FROM $BASE_IMAGE

# Global environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

# Bring uv & uvx in from the named stage above.
COPY --from=uv-source /uv /usr/local/bin/uv
COPY --from=uv-source /uvx /usr/local/bin/uvx

# Install Google Cloud CLI and Pub/Sub emulator
# pipefail guards the curl|gpg pipeline so a network failure aborts the layer.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# The MS Python base image ships an apt source for yarn whose signing key
# periodically expires and breaks `apt-get update`. We don't use yarn here,
# so strip the file before any update runs.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        gnupg \
        curl \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        google-cloud-cli \
        google-cloud-cli-pubsub-emulator \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Devcontainer images do not expose a long-running service, so a runtime
# health probe has nothing meaningful to check. Declaring NONE is
# explicit (vs inheriting from the base) and silences Trivy DS-0026.
HEALTHCHECK NONE

# Drop privileges. The base image ships a `vscode` user (UID 1000); the
# devcontainer.json `remoteUser` already enforces it for IDE sessions,
# but without this directive `docker run` defaults to root. (Trivy DS-0002.)
USER vscode
