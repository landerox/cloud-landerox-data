"""
Secret management utilities for Google Cloud Platform.

Ensures zero hardcoded credentials by fetching values from Secret Manager.
"""

import os

from google.cloud import secretmanager


def get_secret(secret_id: str, project_id: str | None = None) -> str:
    """
    Retrieves a secret value from GCP Secret Manager.

    Args:
        secret_id: The ID/Name of the secret to retrieve.
        project_id: GCP Project ID. Defaults to GOOGLE_CLOUD_PROJECT env var.

    Returns:
        The latest version of the secret value as a string.
    """
    client = secretmanager.SecretManagerServiceClient()
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or "unknown"
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
