"""Fail-closed SHA-256 helpers for public reproduction artifacts."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CHUNK_SIZE = 1024 * 1024


class IntegrityError(ValueError):
    """An artifact digest did not match its declared SHA-256 authority."""


def validate_sha256(expected: str) -> str:
    if _SHA256.fullmatch(expected) is None:
        raise ValueError("expected digest must be 64 lowercase hexadecimal SHA-256 characters")
    return expected


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError("artifact file does not exist")
    if not path.is_file():
        if path.is_dir():
            raise IsADirectoryError("artifact path is a directory")
        raise ValueError("artifact path is not a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256_bytes(data: bytes, expected: str) -> str:
    validate_sha256(expected)
    actual = sha256_bytes(data)
    if actual != expected:
        raise IntegrityError("byte artifact SHA-256 mismatch")
    return actual


def verify_sha256_file(path: Path, expected: str) -> str:
    validate_sha256(expected)
    actual = sha256_file(path)
    if actual != expected:
        raise IntegrityError("file artifact SHA-256 mismatch")
    return actual
