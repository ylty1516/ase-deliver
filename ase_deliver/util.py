from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Sequence


HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def as_path(value: str | os.PathLike[str] | None) -> Path | None:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def parse_hex(color: str) -> tuple[int, int, int, int]:
    raw = color.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) == 6:
        r, g, b = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
        return r, g, b, 255
    if len(raw) == 8:
        r, g, b, a = (
            int(raw[0:2], 16),
            int(raw[2:4], 16),
            int(raw[4:6], 16),
            int(raw[6:8], 16),
        )
        return r, g, b, a
    raise ValueError(f"Invalid color {color!r}; use #RRGGBB")


def to_hex(rgb: Sequence[int], alpha: bool = False) -> str:
    if alpha and len(rgb) >= 4:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}{rgb[3]:02x}"
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def color_dist2(a: Sequence[int], b: Sequence[int]) -> int:
    dr = int(a[0]) - int(b[0])
    dg = int(a[1]) - int(b[1])
    db = int(a[2]) - int(b[2])
    return dr * dr + dg * dg + db * db


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def chunked(seq: Sequence[Any], n: int) -> Iterable[Sequence[Any]]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]
