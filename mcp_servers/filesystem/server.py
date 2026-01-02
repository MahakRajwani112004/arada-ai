"""Filesystem MCP Server.

Provides MCP tools for local filesystem operations:
- read_file: Read file contents
- write_file: Write content to a file
- list_directory: List directory contents

Credentials passed via HTTP header:
- X-Allowed-Paths: Comma-separated list of allowed directory paths
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseMCPServer, tool


class FilesystemServer(BaseMCPServer):
    """MCP Server for local filesystem operations."""

    def __init__(self):
        super().__init__(
            name="filesystem",
            version="1.0.0",
            description="Filesystem MCP Server for local file operations",
        )

    def _validate_path(self, file_path: str, allowed_paths: List[str]) -> Path:
        """Validate that the file path is within allowed directories.

        Args:
            file_path: The path to validate
            allowed_paths: List of allowed base directories

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is not within allowed directories
        """
        resolved = Path(file_path).resolve()

        for allowed in allowed_paths:
            allowed_resolved = Path(allowed).resolve()
            try:
                resolved.relative_to(allowed_resolved)
                return resolved
            except ValueError:
                continue

        raise ValueError(
            f"Path '{file_path}' is not within allowed directories: {allowed_paths}"
        )

    def _get_allowed_paths(self, credentials: Dict[str, str]) -> List[str]:
        """Extract allowed paths from credentials."""
        paths_str = credentials.get("allowed_paths", "")
        if not paths_str:
            # Default to /tmp and /data if not specified
            return ["/tmp", "/data"]
        return [p.strip() for p in paths_str.split(",") if p.strip()]

    @tool(
        name="read_file",
        description="Read the contents of a file. Returns the file content as text.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
            "required": ["path"],
        },
        credential_headers=["X-Allowed-Paths"],
    )
    async def read_file(
        self, credentials: Dict[str, str], path: str, encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """Read file contents."""
        allowed_paths = self._get_allowed_paths(credentials)

        try:
            validated_path = self._validate_path(path, allowed_paths)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        if not validated_path.exists():
            return {"success": False, "error": f"File not found: {path}"}

        if not validated_path.is_file():
            return {"success": False, "error": f"Path is not a file: {path}"}

        try:
            content = validated_path.read_text(encoding=encoding)
            return {
                "success": True,
                "path": str(validated_path),
                "content": content,
                "size": validated_path.stat().st_size,
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

    @tool(
        name="write_file",
        description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
                "create_dirs": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True,
                },
            },
            "required": ["path", "content"],
        },
        credential_headers=["X-Allowed-Paths"],
    )
    async def write_file(
        self,
        credentials: Dict[str, str],
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ) -> Dict[str, Any]:
        """Write content to a file."""
        allowed_paths = self._get_allowed_paths(credentials)

        try:
            validated_path = self._validate_path(path, allowed_paths)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        try:
            if create_dirs:
                validated_path.parent.mkdir(parents=True, exist_ok=True)

            validated_path.write_text(content, encoding=encoding)
            return {
                "success": True,
                "path": str(validated_path),
                "size": validated_path.stat().st_size,
                "message": f"Successfully wrote {len(content)} characters to {path}",
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}

    @tool(
        name="list_directory",
        description="List contents of a directory. Returns files and subdirectories with metadata.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list",
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files (starting with .)",
                    "default": False,
                },
                "recursive": {
                    "type": "boolean",
                    "description": "List recursively (up to 2 levels deep)",
                    "default": False,
                },
            },
            "required": ["path"],
        },
        credential_headers=["X-Allowed-Paths"],
    )
    async def list_directory(
        self,
        credentials: Dict[str, str],
        path: str,
        include_hidden: bool = False,
        recursive: bool = False,
    ) -> Dict[str, Any]:
        """List directory contents."""
        allowed_paths = self._get_allowed_paths(credentials)

        try:
            validated_path = self._validate_path(path, allowed_paths)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        if not validated_path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}

        if not validated_path.is_dir():
            return {"success": False, "error": f"Path is not a directory: {path}"}

        try:
            entries = []

            def list_dir(dir_path: Path, depth: int = 0):
                if depth > 2:  # Max recursion depth
                    return

                for entry in sorted(dir_path.iterdir()):
                    if not include_hidden and entry.name.startswith("."):
                        continue

                    stat = entry.stat()
                    entry_info = {
                        "name": entry.name,
                        "path": str(entry),
                        "type": "directory" if entry.is_dir() else "file",
                        "size": stat.st_size if entry.is_file() else None,
                        "modified": stat.st_mtime,
                    }
                    entries.append(entry_info)

                    if recursive and entry.is_dir():
                        list_dir(entry, depth + 1)

            list_dir(validated_path)

            return {
                "success": True,
                "path": str(validated_path),
                "entries": entries,
                "count": len(entries),
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list directory: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    server = FilesystemServer()
    app = server.app

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
