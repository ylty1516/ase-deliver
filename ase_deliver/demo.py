from __future__ import annotations

from pathlib import Path
from typing import Any

from .images import rasterize_pixels
from .spec import format_cel_name, raw_dir, save_spec, sources_cfg
from .templates import get_template
from .util import dump_json, ensure_dir

MAP = {
    ".": None,
    "o": "#63c74d",
    "s": "#3e8948",
    "h": "#a7f070",
    "e": "#181425",
    "w": "#ffffff",
    "d": "#265c42",
}


def _px(*rows: str) -> dict[str, Any]:
    width = max(len(r) for r in rows)
    padded = [r.ljust(width, ".")[:width] for r in rows]
    if width != 16 or len(padded) != 16:
        raise ValueError(f"demo frame must be 16x16, got {width}x{len(padded)}")
    return {"map": MAP, "rows": padded}


# 16x16 slime. Four idle bounce frames + four in-place hops as "walk".
FRAMES: dict[str, list[dict[str, Any]]] = {
    "idle": [
        _px(
            "................",
            "................",
            "................",
            "......hhhh......",
            "....hhoooooh....",
            "...hooooooooh...",
            "..hooowwwoooh...",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "..hodsooosdoh...",
            "...hosssoooh....",
            "....dsssssd.....",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            "................",
            "......hhhh......",
            "....hhoooooh....",
            "...hooooooooh...",
            "..hoooooooooh...",
            "..hooowwwoooh...",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "...hodsoosdoh...",
            "....hossssoh....",
            ".....dssssd.....",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            ".....hhhhhh.....",
            "....hooooooh....",
            "...hooooooooh...",
            "..hooooooooooh..",
            "..hooowwwooooh..",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "...hooooooooh...",
            "....hodssdoh....",
            ".....hosssoh....",
            "......dsssd.....",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            "................",
            "......hhhh......",
            "....hhoooooh....",
            "...hooooooooh...",
            "..hoooooooooh...",
            "..hooowwwoooh...",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "...hodsoosdoh...",
            "....hossssoh....",
            ".....dssssd.....",
            "................",
            "................",
            "................",
        ),
    ],
    "walk": [
        _px(
            "................",
            "................",
            ".......hhhh.....",
            ".....hhooooh....",
            "....hooooooh....",
            "...hooowwoooh...",
            "...hooweeeewoh..",
            "...hooweeeewoh..",
            "...hooooooooh...",
            "....hodssooh....",
            "....sssoooh.....",
            ".....dsss.......",
            "................",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            "......hhhh......",
            "....hhoooooh....",
            "...hooooooooh...",
            "..hooowwwoooh...",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "...hodoooosd....",
            "....sssssoo.....",
            "......dsss......",
            "................",
            "................",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            "................",
            ".....hhhh.......",
            "....hoooohh.....",
            "....hooooooh....",
            "...hoowwoooh....",
            "..howeewooh.....",
            "..howeewooh.....",
            "...hooooooh.....",
            "....hoossdh.....",
            ".....hoosss.....",
            ".......sssd.....",
            "................",
            "................",
            "................",
            "................",
        ),
        _px(
            "................",
            "......hhhh......",
            "....hhoooooh....",
            "...hooooooooh...",
            "..hooowwwoooh...",
            "..hooweeeeewoh..",
            "..hooweeeeewoh..",
            "..hooooooooooh..",
            "...hodoooosd....",
            "....oosssss.....",
            "......sssd......",
            "................",
            "................",
            "................",
            "................",
            "................",
        ),
    ],
}


def write_demo_sources(root: Path, spec: dict[str, Any]) -> list[str]:
    raw = ensure_dir(raw_dir(root, spec))
    written: list[str] = []
    pattern = sources_cfg(spec)["pattern"]
    for tag, frames in FRAMES.items():
        for i, payload in enumerate(frames):
            filename = format_cel_name(pattern, tag=tag, frame=i, layer="sprite")
            png_path = raw / filename
            json_path = png_path.with_suffix(".json")
            dump_json(json_path, payload)
            rasterize_pixels(payload).save(png_path)
            written.append(str(png_path))
    return written


def make_demo_spec(name: str = "slime") -> dict[str, Any]:
    spec = get_template("character-platformer")
    spec["name"] = name
    spec["kind"] = "character"
    spec["view"] = "side"
    spec["description"] = "a round green slime with two big eyes, no legs, facing right"
    spec["canvas"] = {"width": 16, "height": 16}
    spec["palette"] = "endesga-32"
    spec["grid"] = {"width": 16, "height": 16}
    spec["pivot"] = {"x": 8, "y": 16}
    spec["tags"] = [
        {"name": "idle", "frames": 4, "duration": 140},
        {"name": "walk", "frames": 4, "duration": 90},
    ]
    spec["layers"] = [{"name": "sprite"}]
    return spec


def seed_demo_project(root: Path, name: str = "slime") -> dict[str, Any]:
    spec = make_demo_spec(name)
    ensure_dir(root)
    save_spec(root, spec)
    ensure_dir(root / "raw")
    ensure_dir(root / "clean")
    ensure_dir(root / "out")
    files = write_demo_sources(root, spec)
    return {"spec": spec, "files": files}
