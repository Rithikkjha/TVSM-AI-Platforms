"""Atomic steering file writer.

Writes steering file content to disk using tempfile + os.replace() to
ensure no partial writes corrupt files on disk.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from config.settings import get_settings
from webhook_pipeline.llm_analyzer import SteeringUpdate

logger = logging.getLogger(__name__)


def write_steering_files(
    repo_name: str,
    updates: list[SteeringUpdate],
    steering_dir: Path | None = None,
) -> list[str]:
    """Write updated steering files atomically.

    Uses ``tempfile.NamedTemporaryFile`` + ``os.replace()`` to ensure
    no partial writes corrupt the steering file on disk.

    Args:
        repo_name: Repository name (used as subdirectory name).
        updates: List of steering updates to write.
        steering_dir: Override for the base steering directory.

    Returns:
        List of file paths that were successfully written.
    """
    settings = get_settings()
    base_dir = steering_dir or Path(settings.kiro_steering_dir)
    repo_dir = base_dir / repo_name

    # Create directory if it doesn't exist
    repo_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[str] = []
    for update in updates:
        target_path = repo_dir / f"{update.file_type}.md"

        # Atomic write: write to temp file in same directory, then rename
        fd = tempfile.NamedTemporaryFile(
            mode="w",
            dir=str(repo_dir),
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        )
        try:
            fd.write(update.content)
            fd.flush()
            os.fsync(fd.fileno())
            fd.close()
            os.replace(fd.name, target_path)
            written_paths.append(str(target_path))
            logger.info("Wrote steering file: %s", target_path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(fd.name)
            except OSError:
                pass
            raise

    return written_paths


__all__ = [
    "write_steering_files",
]
