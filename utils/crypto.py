"""Cryptographic and utility functions."""

import hashlib
from pathlib import Path
from datetime import datetime, timezone


def file_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_tx_hash(previous_hash: str, payload: str, timestamp: str) -> str:
    """Build transaction hash from previous hash, payload, and timestamp."""
    content = f"{previous_hash}|{payload}|{timestamp}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if filename has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
