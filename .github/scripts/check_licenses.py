"""Fail CI when an installed dependency falls outside the license allowlist.

Reads the JSON output of ``pip-licenses --format=json`` and enforces a
permissive-only policy. Strong copyleft (GPL/AGPL/SSPL) and unknown
licenses block the merge unless the package is explicitly allowlisted.

Usage:
    pip-licenses --format=json > licenses.json
    python .github/scripts/check_licenses.py licenses.json

Exit codes:
    0 -- all dependencies use allowed licenses.
    1 -- at least one dependency violates the policy.
    2 -- bad arguments or unreadable input.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

# Permissive license keywords. A license declaration is accepted when at
# least one keyword matches each split part (and no forbidden keyword
# appears). Word boundaries protect against substring traps such as LGPL
# matching GPL.
_PERMISSIVE_RE = re.compile(
    r"\b("
    r"MIT|BSD|Apache|ISC|MPL|Mozilla|Python Software Foundation|PSF|"
    r"Unlicense|Public\s+Domain|Zope|Universal Permissive|HPND|Zlib|"
    r"CC0|0BSD"
    r")\b",
    re.IGNORECASE,
)
# Strong copyleft and source-available licenses we will not ship.
# Word boundaries make GPL not match LGPL/AGPL (those need their own match).
_FORBIDDEN_RE = re.compile(
    r"\b(GPL|AGPL|LGPL|SSPL|EUPL|Commons Clause)\b",
    re.IGNORECASE,
)

# Packages allowlisted by name when their metadata reports an unhelpful
# license string (UNKNOWN / dual-licensed). Keep this list small and
# justified: each entry is a maintained dependency we trust.
_PACKAGE_ALLOWLIST: frozenset[str] = frozenset(
    {
        # google-crc32c ships license info in setup.py classifiers but
        # pip-licenses returns UNKNOWN. Upstream is Apache-2.0:
        # https://github.com/googleapis/python-crc32c/blob/main/LICENSE
        "google-crc32c",
    }
)


def _split_licenses(license_field: str) -> list[str]:
    """Split combined license declarations into individual SPDX-ish tokens.

    Accepts the separators that *unambiguously* mean "multiple licenses":
    ``;``, ``/``, `` OR ``, `` AND ``. Comma is intentionally excluded
    because metadata strings like ``Apache License, Version 2.0`` are a
    single license, not two.
    """
    parts = re.split(r"\s*(?:;|/| OR | AND )\s*", license_field)
    return [p for p in parts if p]


def _is_allowed(license_field: str) -> bool:
    if not license_field or license_field.strip().upper() == "UNKNOWN":
        return False
    for part in _split_licenses(license_field):
        if _FORBIDDEN_RE.search(part):
            return False
        if not _PERMISSIVE_RE.search(part):
            return False
    return True


def main(path: Path) -> int:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as err:
        print(f"::error::cannot read {path}: {err}", file=sys.stderr)
        return 2

    if not isinstance(data, list):
        print("::error::expected a JSON array from pip-licenses", file=sys.stderr)
        return 2

    violations: list[tuple[str, str]] = []
    for entry in data:
        name = entry.get("Name", "<unknown>")
        license_str = entry.get("License", "UNKNOWN") or "UNKNOWN"
        if name in _PACKAGE_ALLOWLIST:
            continue
        if not _is_allowed(license_str):
            violations.append((name, license_str))

    if violations:
        for name, lic in violations:
            print(
                f"::error title=License policy::"
                f"{name} uses non-allowlisted license: {lic}",
                file=sys.stderr,
            )
        print(
            f"::error::License compliance failed: {len(violations)} of "
            f"{len(data)} dependencies violate the policy.",
            file=sys.stderr,
        )
        return 1

    print(
        f"::notice title=License policy::"
        f"All {len(data)} dependencies use allowlisted licenses."
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
