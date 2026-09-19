import json
from pathlib import Path
from typing import Any


def markdown_relative_path(html_relative: str) -> Path:
    return Path(html_relative).with_suffix(".md")


def load_source_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing download manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
