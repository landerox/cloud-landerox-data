"""Tests that lock the docs against the code surface they describe.

These prevent the slow drift where a new symbol, reason code, or workflow
is added but its corresponding documentation entry is forgotten -- the
exact failure mode that triggered Phase 0 of the cleanup.
"""

from pathlib import Path

from shared.common import __all__ as PUBLIC_API
from shared.common import exceptions

REPO_ROOT = Path(__file__).resolve().parents[1]

# Meta symbols that legitimately do not need a README entry.
_README_EXEMPT: frozenset[str] = frozenset({"__version__"})


def test_shared_readme_lists_every_public_export() -> None:
    readme = (REPO_ROOT / "shared" / "README.md").read_text(encoding="utf-8")
    missing = sorted(
        name for name in PUBLIC_API if name not in _README_EXEMPT and name not in readme
    )
    assert not missing, (
        f"shared/README.md does not mention these public exports: {missing}"
    )


def _collected_reason_codes() -> set[str]:
    codes: set[str] = set()
    for value in vars(exceptions).values():
        if (
            isinstance(value, type)
            and issubclass(value, exceptions.CloudLanderoxError)
            and "reason_code" in value.__dict__
        ):
            codes.add(value.reason_code)
    return codes


def test_every_reason_code_appears_in_error_handling_doc() -> None:
    text = (REPO_ROOT / "docs/guides/error-handling.md").read_text(encoding="utf-8")
    codes = _collected_reason_codes()
    missing = sorted(code for code in codes if code not in text)
    assert not missing, (
        f"docs/guides/error-handling.md does not reference these reason "
        f"codes: {missing}"
    )


def test_every_workflow_is_listed_in_cicd_doc() -> None:
    cicd = (REPO_ROOT / "docs/cicd.md").read_text(encoding="utf-8")
    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    missing = sorted(wf.name for wf in workflows if wf.name not in cicd)
    assert not missing, f"docs/cicd.md does not list these workflows: {missing}"


def test_every_adr_is_listed_in_adr_index() -> None:
    adr_dir = REPO_ROOT / "docs" / "adr"
    index = (adr_dir / "README.md").read_text(encoding="utf-8")
    adrs = sorted(p.name for p in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    missing = sorted(name for name in adrs if name not in index)
    assert not missing, f"docs/adr/README.md does not list these ADRs: {missing}"
