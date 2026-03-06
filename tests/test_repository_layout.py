"""Repository-structure tests for the public baseline layout."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_placeholder_directories_exist() -> None:
    expected_directories = (
        "functions/ingestion",
        "functions/trigger",
        "dataflow/pipelines",
        "tests/functions",
        "tests/dataflow",
    )

    for relative_path in expected_directories:
        assert (REPO_ROOT / relative_path).is_dir()


def test_examples_directories_are_not_part_of_baseline() -> None:
    disallowed_directories = (
        "functions/examples",
        "dataflow/examples",
    )

    for relative_path in disallowed_directories:
        assert not (REPO_ROOT / relative_path).exists()
