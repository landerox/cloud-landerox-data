"""Secret management utilities for Google Cloud Platform.

Ensures zero hardcoded credentials by fetching values from Secret Manager.
"""

from functools import lru_cache
import os

from google.api_core.exceptions import GoogleAPICallError
from google.cloud import secretmanager

from .exceptions import ConfigError, SecretNotFoundError


@lru_cache(maxsize=1)
def _get_client() -> secretmanager.SecretManagerServiceClient:
    """Return a process-wide Secret Manager client.

    Constructing the client performs auth discovery, which is expensive.
    Caching it avoids paying that cost on every ``get_secret`` call.
    """
    return secretmanager.SecretManagerServiceClient()


def _resolve_project(project_id: str | None) -> str:
    project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ConfigError(
            "GCP project is not configured: pass project_id or set "
            "GOOGLE_CLOUD_PROJECT."
        )
    return project


def get_secret(secret_id: str, project_id: str | None = None) -> str:
    """Retrieve a secret value from GCP Secret Manager.

    Args:
        secret_id: The ID/name of the secret to retrieve.
        project_id: GCP project ID. Defaults to ``GOOGLE_CLOUD_PROJECT``.

    Returns:
        The latest version of the secret as a UTF-8 string.

    Raises:
        ConfigError: If no project ID can be resolved from argument or env.
        SecretNotFoundError: If the Secret Manager call fails (missing
            secret, IAM denial, transient API error). The original
            ``GoogleAPICallError`` is chained via ``__cause__``.
    """
    project = _resolve_project(project_id)
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"

    try:
        response = _get_client().access_secret_version(request={"name": name})
    except GoogleAPICallError as err:
        raise SecretNotFoundError(
            f"secret {secret_id} not accessible in project {project}"
        ) from err
    return response.payload.data.decode("UTF-8")
