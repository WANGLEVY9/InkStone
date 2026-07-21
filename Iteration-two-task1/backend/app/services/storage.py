"""Storage layer for content files.

Provides a Protocol and filesystem implementation for asynchronous
read/write/delete of Markdown content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import aiofiles

DATA_PATH = Path(__file__).parent.parent.parent / "data"


class ContentStorage(Protocol):
    """Protocol for asynchronous content storage operations.

    Implementations handle reading, writing, and deleting content files.
    """

    async def read(self, file_path: Path) -> str:
        """Read content from the given file path.

        Args:
            file_path: Relative path to the content file.

        Returns:
            The file content as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    async def write(self, file_path: Path, content: str) -> None:
        """Write content to the given file path.

        Args:
            file_path: Relative path to the content file.
            content: Text content to persist.
        """
        ...

    async def delete(self, file_path: Path) -> None:
        """Delete the file at the given path.

        Args:
            file_path: Relative path to the content file.
        """
        ...


class FileSystemStorage:
    """Markdown file storage implementation with path-traversal protection."""

    def __init__(self, base_path: Path = DATA_PATH):
        """Initialize storage with a base directory.

        Args:
            base_path: Root directory where all content files are stored.
        """
        self.base_path = base_path

    def _resolve(self, file_path: Path) -> Path:
        """Resolve a relative path against the base path, guarding against traversal.

        Args:
            file_path: Relative path to resolve.

        Returns:
            The absolute, resolved path.

        Raises:
            ValueError: If the resolved path escapes the base directory.
        """
        resolved = (self.base_path / file_path).resolve()
        if not resolved.is_relative_to(self.base_path.resolve()):
            raise ValueError(f"Path traversal detected: {file_path}")
        return resolved

    async def read(self, file_path: Path) -> str:
        """Read text from a file under the base path.

        Args:
            file_path: Relative path to the file.

        Returns:
            The file contents.
        """
        full_path = self._resolve(file_path)
        async with aiofiles.open(full_path, encoding="utf-8") as f:
            return await f.read()

    async def write(self, file_path: Path, content: str) -> None:
        """Write text to a file under the base path atomically.

        Args:
            file_path: Relative path to the file.
            content: Text content to persist.
        """
        full_path = self._resolve(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: write to temp file then rename to avoid corruption
        temp_path = full_path.with_suffix(full_path.suffix + ".tmp")
        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            await f.write(content)
        temp_path.replace(full_path)

    async def delete(self, file_path: Path) -> None:
        """Delete a file under the base path if it exists.

        Args:
            file_path: Relative path to the file.
        """
        full_path = self._resolve(file_path)
        try:
            full_path.unlink()
        except FileNotFoundError:
            pass

    async def exists(self, file_path: Path) -> bool:
        """Check whether a file exists under the base path.

        Args:
            file_path: Relative path to the file.

        Returns:
            True if the file exists, False otherwise.
        """
        return self._resolve(file_path).exists()
