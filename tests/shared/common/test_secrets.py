"""Unit tests for shared.common.secrets."""

from _pytest.monkeypatch import MonkeyPatch

from shared.common.secrets import get_secret


def test_get_secret_uses_env_project_id(
    monkeypatch: MonkeyPatch, mock_secret_manager
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
    mock_secret_manager,
    mock_secret_value,
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


def test_get_secret_falls_back_to_unknown_when_no_project(
    monkeypatch: MonkeyPatch, mock_secret_manager
) -> None:
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    _ = get_secret("api-key")

    mock_secret_manager[
        "client"
    ].return_value.access_secret_version.assert_called_once_with(
        request={"name": "projects/unknown/secrets/api-key/versions/latest"}
    )
