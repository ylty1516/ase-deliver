from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from . import __version__


STEAM_LIBRARY_HINTS = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf"),
    Path(r"C:\Program Files\Steam\steamapps\libraryfolders.vdf"),
    Path(r"D:\steam\steamapps\libraryfolders.vdf"),
    Path(r"D:\Steam\steamapps\libraryfolders.vdf"),
    Path(r"E:\Steam\steamapps\libraryfolders.vdf"),
    Path(r"F:\Steam\steamapps\libraryfolders.vdf"),
]


def _exe_from_library(root: Path) -> Path | None:
    candidate = root / "steamapps" / "common" / "Aseprite" / "Aseprite.exe"
    if candidate.is_file():
        return candidate
    # Linux / mac fallbacks inside a Steam library
    for name in ("aseprite", "Aseprite"):
        unix = root / "steamapps" / "common" / "Aseprite" / name
        if unix.is_file():
            return unix
    return None


def _parse_libraryfolders(vdf: Path) -> list[Path]:
    if not vdf.is_file():
        return []
    text = vdf.read_text(encoding="utf-8", errors="ignore")
    paths = []
    for match in re.finditer(r'"path"\s*"([^"]+)"', text):
        paths.append(Path(match.group(1).replace("\\\\", "\\")))
    return paths


def find_aseprite() -> Path | None:
    env = os.environ.get("ASEPRITE") or os.environ.get("ASEPRITE_PATH")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    which = shutil.which("aseprite") or shutil.which("Aseprite")
    if which:
        return Path(which)
    hardcoded = [
        Path(r"F:\SteamLibrary\steamapps\common\Aseprite\Aseprite.exe"),
        Path(r"C:\Program Files\Aseprite\Aseprite.exe"),
        Path.home() / "scoop" / "apps" / "aseprite" / "current" / "Aseprite.exe",
    ]
    for item in hardcoded:
        if item.is_file():
            return item
    seen: set[Path] = set()
    for vdf in STEAM_LIBRARY_HINTS:
        for lib in _parse_libraryfolders(vdf):
            if lib in seen:
                continue
            seen.add(lib)
            found = _exe_from_library(lib)
            if found:
                return found
    # Scan drive-letter SteamLibrary folders without walking the world.
    for letter in "CDEFGHI":
        for name in ("SteamLibrary", "Steam", "steam"):
            lib = Path(f"{letter}:\\{name}")
            found = _exe_from_library(lib)
            if found:
                return found
    return None


def doctor() -> dict:
    ase = find_aseprite()
    pillow_ok = True
    pillow_ver = ""
    try:
        import PIL

        pillow_ver = getattr(PIL, "__version__", "")
    except Exception as exc:  # pragma: no cover
        pillow_ok = False
        pillow_ver = str(exc)
    return {
        "ok": pillow_ok,
        "version": __version__,
        "python": sys.executable,
        "pythonVersion": sys.version.split()[0],
        "pillow": pillow_ok,
        "pillowVersion": pillow_ver,
        "aseprite": str(ase) if ase else None,
        "asepriteFound": bool(ase),
        "hint": None
        if ase
        else "Aseprite not found. Set ASEPRITE to Aseprite.exe. Compile still works without it.",
    }
