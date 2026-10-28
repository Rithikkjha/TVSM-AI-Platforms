"""Phase-2 extractors. Registry: ``repo_docs.extractors.registry``; contract: ``base``."""
from __future__ import annotations

from .base import Evidence, ExtractResult, Extractor, FileTouch, InventoryItem, RepoContext

__all__ = ["Evidence", "ExtractResult", "Extractor", "FileTouch", "InventoryItem", "RepoContext"]
