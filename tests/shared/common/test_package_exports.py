"""Verify that all public symbols in shared.common are importable."""

import shared.common


def test_all_exports_are_importable() -> None:
    for name in shared.common.__all__:
        assert hasattr(shared.common, name), (
            f"{name} listed in __all__ but not importable"
        )
