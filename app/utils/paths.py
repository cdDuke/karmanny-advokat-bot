from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from app.config import Settings


def ensure_runtime_dirs(settings: Settings) -> None:
    for path in (settings.data_dir, settings.downloads_dir, settings.generated_dir, settings.logs_dir):
        path.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-zА-Яа-я0-9._-]+", "_", name).strip("._")
    return cleaned or "file"


def unique_path(directory: Path, original_name: str) -> Path:
    suffix = Path(original_name).suffix
    stem = safe_filename(Path(original_name).stem)
    return directory / f"{stem}_{uuid4().hex[:12]}{suffix}"
