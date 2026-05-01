"""Unit tests for shared.common.secrets."""

from collections.abc import Callable
from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch
from google.api_core.exceptions import PermissionDenied
import pytest

from shared.common.exceptions import ConfigError, SecretNotFoundError
from shared.common.secrets import get_secret

# Local aliases mirror tests/conftest.py so this file stays self-contained
# while satisfying Pyright's parameter-annotation rule.
_ClientDict = dict[str, MagicMock]
_SetSecret = Callable[[str], None]


def test_get_secret_uses_env_project_id(
    monkeypatch: MonkeyPatch, mock_secret_manager: _ClientDict
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")

    value = get_secret("api-key")

    assert value == "test-secret-value"
    mock_secret_manager[
        "client"
    ].return_value.access_secret_version.assert_called_once_with(
        request={"name": "projects/env-project/secrets/api-key/versions/latest"}
    )


def test_get_secret_prefers_explicit_project_id(
    monkeypatch: MonkeyPatch,
    mock_secret_manager: _ClientDict,
    mock_secret_value: _SetSecret,
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")
    mock_secret_value("explicit-secret")

    value = get_secret("api-key", project_id="explicit-project")

    assert value == "explicit-secret"
    mock_secret_manager[
        "client"
    ].return_value.access_secret_version.assert_called_once_with(
        request={"name": "projects/explicit-project/secrets/api-key/versions/latest"}
    )


def test_get_secret_raises_when_no_project_configured(
    monkeypatch: MonkeyPatch, mock_secret_manager: _ClientDict
) -> None:
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    with pytest.raises(ConfigError, match="GCP project is not configured"):
        get_secret("api-key")

    mock_secret_manager["client"].return_value.access_secret_version.assert_not_called()


def test_get_secret_caches_client_across_calls(
    monkeypatch: MonkeyPatch, mock_secret_manager: _ClientDict
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")

    get_secret("api-key")
    get_secret("other-key")

    assert mock_secret_manager["client"].call_count == 1


def test_get_secret_wraps_google_api_call_error(
    monkeypatch: MonkeyPatch, mock_secret_manager: _ClientDict
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")
    underlying = PermissionDenied("denied")
    mock_secret_manager[
        "client"
    ].return_value.access_secret_version.side_effect = underlying

    with pytest.raises(SecretNotFoundError, match="api-key") as exc_info:
        get_secret("api-key")

    assert exc_info.value.__cause__ is underlying
    assert exc_info.value.reason_code == "secret_not_found"
