"""Pytest configuration and shared fixtures for all tests.

This module provides common fixtures for testing Cloud Functions,
Dataflow pipelines, and shared library components.
"""

from collections.abc import Callable, Generator
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from apache_beam.testing.test_pipeline import TestPipeline
import pytest
from requests.exceptions import HTTPError

# =============================================================================
# Type Aliases
# =============================================================================

MockClientDict = dict[str, MagicMock]
MockRequestsDict = dict[str, MagicMock]
ConfigDict = dict[str, str]


# =============================================================================
# Environment Setup
# =============================================================================


@pytest.fixture(autouse=True)
def set_test_environment(monkeypatch: MonkeyPatch) -> None:
    """Set environment variables for testing."""
    monkeypatch.setenv("GCP_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("FUNCTION_REGION", "us-central1")


# =============================================================================
# Google Cloud Storage Fixtures
# =============================================================================


@pytest.fixture
def mock_storage_client() -> Generator[MockClientDict, None, None]:
    """Mock Google Cloud Storage client."""
    with patch("google.cloud.storage.Client") as patched_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        patched_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        mock_blob.exists.return_value = False
        mock_blob.generation = 1
        mock_blob.download_as_text.return_value = ""
        mock_blob.download_as_bytes.return_value = b""

        yield {
            "client": patched_client,
            "bucket": mock_bucket,
            "blob": mock_blob,
        }


@pytest.fixture
def mock_gcs_file_content(
    mock_storage_client: MockClientDict,
) -> Callable[[str | bytes, int], None]:
    """Helper to set mock GCS file content."""

    def set_gcs_content(file_content: str | bytes, generation_number: int = 1) -> None:
        mock_storage_client["blob"].exists.return_value = True
        mock_storage_client["blob"].generation = generation_number

        if isinstance(file_content, bytes):
            mock_storage_client["blob"].download_as_bytes.return_value = file_content
            mock_storage_client[
                "blob"
            ].download_as_text.return_value = file_content.decode()
        else:
            mock_storage_client["blob"].download_as_text.return_value = file_content
            mock_storage_client[
                "blob"
            ].download_as_bytes.return_value = file_content.encode()

    return set_gcs_content


# =============================================================================
# BigQuery Fixtures
# =============================================================================


@pytest.fixture
def mock_bigquery_client() -> Generator[MockClientDict, None, None]:
    """Mock Google Cloud BigQuery client."""
    with patch("google.cloud.bigquery.Client") as patched_client:
        mock_table = MagicMock()
        mock_job = MagicMock()

        patched_client.return_value.get_table.return_value = mock_table
        patched_client.return_value.load_table_from_uri.return_value = mock_job
        patched_client.return_value.query.return_value = mock_job

        mock_job.result.return_value = []
        mock_job.errors = None

        yield {
            "client": patched_client,
            "table": mock_table,
            "job": mock_job,
        }


@pytest.fixture
def mock_bq_query_results(
    mock_bigquery_client: MockClientDict,
) -> Callable[[list[dict[str, Any]]], None]:
    """Helper to set mock BigQuery query results."""

    def set_query_results(result_rows: list[dict[str, Any]]) -> None:
        mock_rows = [MagicMock(**row) for row in result_rows]
        for mock_row, original_row in zip(mock_rows, result_rows, strict=True):
            mock_row.__getitem__ = lambda _, key, row=original_row: row[key]
            mock_row.keys.return_value = original_row.keys()

        mock_bigquery_client["job"].result.return_value = mock_rows

    return set_query_results


# =============================================================================
# Secret Manager Fixtures
# =============================================================================


@pytest.fixture
def mock_secret_manager() -> Generator[MockClientDict, None, None]:
    """Mock Google Cloud Secret Manager client."""
    with patch(
        "google.cloud.secretmanager.SecretManagerServiceClient"
    ) as patched_client:
        mock_response = MagicMock()
        mock_response.payload.data = b"test-secret-value"

        patched_client.return_value.access_secret_version.return_value = mock_response

        yield {
            "client": patched_client,
            "response": mock_response,
        }


@pytest.fixture
def mock_secret_value(
    mock_secret_manager: MockClientDict,
) -> Callable[[str], None]:
    """Helper to set mock secret value."""

    def set_secret_value(secret_value: str) -> None:
        mock_secret_manager["response"].payload.data = secret_value.encode()

    return set_secret_value


# =============================================================================
# Cloud Functions Fixtures
# =============================================================================


@pytest.fixture
def mock_http_request() -> Callable[..., MagicMock]:
    """Create a mock HTTP request for Cloud Functions."""

    def create_mock_request(
        http_method: str = "POST",
        json_payload: dict[str, Any] | None = None,
        request_headers: dict[str, str] | None = None,
        query_args: dict[str, str] | None = None,
    ) -> MagicMock:
        mock_request = MagicMock()
        mock_request.method = http_method
        mock_request.get_json.return_value = json_payload or {}
        mock_request.headers = request_headers or {}
        mock_request.args = query_args or {}
        return mock_request

    return create_mock_request


@pytest.fixture
def mock_cloud_event() -> Callable[..., MagicMock]:
    """Create a mock CloudEvent for event-triggered functions."""

    def create_mock_event(
        event_type: str = "google.cloud.storage.object.v1.finalized",
        bucket_name: str = "test-bucket",
        object_name: str = "test-file.json",
        event_data: dict[str, Any] | None = None,
    ) -> MagicMock:
        mock_event = MagicMock()
        mock_event.data = event_data or {
            "bucket": bucket_name,
            "name": object_name,
            "metageneration": "1",
            "timeCreated": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z",
        }
        mock_event["type"] = event_type
        mock_event["source"] = (
            f"//storage.googleapis.com/projects/_/buckets/{bucket_name}"
        )
        return mock_event

    return create_mock_event


# =============================================================================
# Dataflow / Apache Beam Fixtures
# =============================================================================


@pytest.fixture
def beam_test_pipeline() -> Any:
    """Create an Apache Beam TestPipeline for unit tests."""
    return TestPipeline()


# =============================================================================
# Config Fixtures
# =============================================================================


@pytest.fixture
def sample_config() -> ConfigDict:
    """Provide a sample configuration dictionary."""
    return {
        "project_id": "test-project",
        "dataset_id": "test_dataset",
        "table_id": "test_table",
        "bucket_name": "test-bucket",
        "source_api_url": "https://api.example.com/data",
    }


@pytest.fixture
def mock_config_file(tmp_path: Path, sample_config: ConfigDict) -> Path:
    """Create a temporary config.json file."""
    config_file_path = tmp_path / "config.json"
    config_file_path.write_text(json.dumps(sample_config))
    return config_file_path


# =============================================================================
# HTTP/API Fixtures
# =============================================================================


@pytest.fixture
def mock_requests() -> Generator[MockRequestsDict, None, None]:
    """Mock the requests library for external API calls."""
    with patch("requests.get") as patched_get, patch("requests.post") as patched_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.text = '{"data": []}'
        mock_response.raise_for_status.return_value = None

        patched_get.return_value = mock_response
        patched_post.return_value = mock_response

        yield {
            "get": patched_get,
            "post": patched_post,
            "response": mock_response,
        }


@pytest.fixture
def mock_api_response(
    mock_requests: MockRequestsDict,
) -> Callable[[dict[str, Any] | list[Any], int], None]:
    """Helper to set mock API response."""

    def set_api_response(
        response_data: dict[str, Any] | list[Any],
        status_code: int = 200,
    ) -> None:
        mock_requests["response"].status_code = status_code
        mock_requests["response"].json.return_value = response_data
        mock_requests["response"].text = json.dumps(response_data)

        if status_code >= 400:
            mock_requests["response"].raise_for_status.side_effect = HTTPError()
        else:
            mock_requests["response"].raise_for_status.return_value = None

    return set_api_response


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def freeze_time() -> Any:
    """Freeze time for deterministic testing."""
    try:
        from freezegun import freeze_time as freezegun_freeze_time  # noqa: PLC0415

        return freezegun_freeze_time
    except ImportError:
        pytest.skip("freezegun not installed")
        return None


@pytest.fixture
def capture_logs(caplog: LogCaptureFixture) -> LogCaptureFixture:
    """Capture and assert on log messages."""
    caplog.set_level(logging.INFO)
    return caplog
