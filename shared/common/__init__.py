"""Shared common utilities for the cloud-landerox-data project."""

import importlib.metadata

from .io import KappaOptions, get_sink, get_source
from .logging import setup_cloud_logging
from .secrets import get_secret

try:
    __version__ = importlib.metadata.version("cloud-landerox-data")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "KappaOptions",
    "__version__",
    "get_secret",
    "get_sink",
    "get_source",
    "setup_cloud_logging",
]
