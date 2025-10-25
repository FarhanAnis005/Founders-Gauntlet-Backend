# app/services/storage.py
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Union, IO

from app.core.config import UPLOAD_DIR  # UPLOAD_DIR is a Path and mkdir is done in config


def _read_bytes(file_obj: Union[bytes, IO[bytes], object]) -> bytes:
    # Already bytes
    if isinstance(file_obj, (bytes, bytearray)):
        return bytes(file_obj)

    # FastAPI UploadFile has .file (SpooledTemporaryFile)
    f = getattr(file_obj, "file", None)
    if f and hasattr(f, "read"):
        return f.read()

    # Any other file-like object with .read()
    if hasattr(file_obj, "read"):
        return file_obj.read()

    raise TypeError("save_upload() expected bytes, an UploadFile, or a file-like object with .read().")


def save_upload(file_or_bytes: Union[bytes, IO[bytes], object], original_name: str) -> str:
    """
    Saves an uploaded PDF to disk and returns its absolute path.
    Accepts:
      - raw bytes
      - FastAPI UploadFile
      - any file-like object with .read()
    """
    ext = Path(original_name or "").suffix.lower() or ".pdf"
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name

    data = _read_bytes(file_or_bytes)

    with path.open("wb") as out:
        out.write(data)

    return str(path)
