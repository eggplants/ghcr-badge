""".. include:: ../README.md"""  # noqa: D415

import importlib.metadata

from .generate import GHCRBadgeGenerator

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["GHCRBadgeGenerator"]
