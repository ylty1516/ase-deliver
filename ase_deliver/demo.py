from __future__ import annotations

from pathlib import Path
from typing import Any

from .demo_art import (
    SLIME_PALETTE,
    chest_frame,
    coin_frame,
    potion_frame,
    slime_idle,
    slime_jump,
    slime_walk,
    spark_frames,
    sword_frame,
)
from .hero_art import HERO_PALETTE, hero_attack, hero_idle
from .spec import format_cel_name, raw_dir, save_spec, sources_cfg
from .templates import get_template
from .util import dump_json, ensure_dir


def _write_canvases(root: Path, spec: dict[str, Any], sequences: dict[str, list]) -> list[str]:
    raw = ensure_dir(raw_dir(root, spec))
    pattern = sources_cfg(spec)["pattern"]
    written: list[str] = []
    for tag, frames in sequences.items():
        for i, canvas in enumerate(frames):
            filename = format_cel_name(pattern, tag=tag, frame=i, layer="sprite")
            png_path = raw / filename
            json_path = png_path.with_suffix(".json")
            payload = canvas.to_payload()
            dump_json(json_path, payload)
            canvas.to_image().save(png_path)
            written.append(str(png_path))
    return written


def make_demo_spec(name: str = "slime") -> dict[str, Any]:
    spec = get_template("character-platformer")
    spec["name"] = name
    spec["kind"] = "character"
    spec["view"] = "side"
    spec["description"] = "a glossy round green slime with big shiny eyes, facing right, 32x32 game sprite"
    spec["canvas"] = {"width": 32, "height": 32}
    spec["colorMode"] = "indexed"
    spec["palette"] = SLIME_PALETTE
    spec["grid"] = {"width": 16, "height": 16}
    spec["pivot"] = {"x": 16, "y": 32}
    spec["tags"] = [
        {"name": "idle", "frames": 6, "duration": 120},
        {"name": "walk", "frames": 6, "duration": 80},
        {"name": "jump", "frames": 4, "duration": 90},
    ]
    spec["layers"] = [{"name": "sprite"}]
    spec["sources"]["anchor"] = "bottom-center"
    spec["sources"]["padding"] = 1
    spec["sources"]["scaleMode"] = "none"
    spec["sources"]["cornerKey"] = False
    spec["sources"]["keyColors"] = []
    return spec


def write_demo_sources(root: Path, spec: dict[str, Any]) -> list[str]:
    sequences = {
        "idle": slime_idle(6),
        "walk": slime_walk(6),
        "jump": slime_jump(),
    }
    return _write_canvases(root, spec, sequences)


def seed_demo_project(root: Path, name: str = "slime") -> dict[str, Any]:
    spec = make_demo_spec(name)
    ensure_dir(root)
    save_spec(root, spec)
    ensure_dir(root / "raw")
    ensure_dir(root / "clean")
    ensure_dir(root / "out")
    files = write_demo_sources(root, spec)
    return {"spec": spec, "files": files}


def make_props_spec(name: str = "props") -> dict[str, Any]:
    spec = get_template("prop")
    spec["name"] = name
    spec["kind"] = "prop"
    spec["canvas"] = {"width": 32, "height": 32}
    spec["palette"] = SLIME_PALETTE
    spec["pivot"] = {"x": 16, "y": 32}
    spec["tags"] = [
        {"name": "potion", "frames": 2, "duration": 160},
        {"name": "coin", "frames": 4, "duration": 90},
        {"name": "chest", "frames": 1, "duration": 200},
        {"name": "sword", "frames": 1, "duration": 200},
        {"name": "spark", "frames": 6, "duration": 70},
    ]
    spec["layers"] = [{"name": "sprite"}]
    spec["sources"]["anchor"] = "center"
    spec["sources"]["padding"] = 1
    spec["sources"]["scaleMode"] = "none"
    spec["sources"]["cornerKey"] = False
    spec["sources"]["keyColors"] = []
    return spec


def seed_props_project(root: Path, name: str = "props") -> dict[str, Any]:
    spec = make_props_spec(name)
    ensure_dir(root)
    save_spec(root, spec)
    ensure_dir(root / "raw")
    ensure_dir(root / "clean")
    ensure_dir(root / "out")
    sequences = {
        "potion": [potion_frame(0), potion_frame(1)],
        "coin": [coin_frame(i / 4 * 3.1416) for i in range(4)],
        "chest": [chest_frame()],
        "sword": [sword_frame()],
        "spark": spark_frames(),
    }
    files = _write_canvases(root, spec, sequences)
    return {"spec": spec, "files": files}


def make_hero_spec(name: str = "hero") -> dict[str, Any]:
    spec = get_template("character-platformer")
    spec["name"] = name
    spec["kind"] = "character"
    spec["view"] = "side"
    spec["description"] = "side-view chibi hero in a blue tunic, brown hair, red cape, longsword, facing right"
    spec["canvas"] = {"width": 48, "height": 48}
    spec["colorMode"] = "indexed"
    spec["palette"] = HERO_PALETTE
    spec["grid"] = {"width": 16, "height": 16}
    spec["pivot"] = {"x": 22, "y": 48}
    spec["tags"] = [
        {"name": "idle", "frames": 4, "duration": 140},
        {"name": "attack", "frames": 6, "duration": 70},
    ]
    spec["layers"] = [{"name": "sprite"}]
    spec["sources"]["anchor"] = "bottom-center"
    spec["sources"]["padding"] = 1
    spec["sources"]["scaleMode"] = "none"
    spec["sources"]["cornerKey"] = False
    spec["sources"]["keyColors"] = []
    return spec


def seed_hero_project(root: Path, name: str = "hero") -> dict[str, Any]:
    spec = make_hero_spec(name)
    ensure_dir(root)
    save_spec(root, spec)
    ensure_dir(root / "raw")
    ensure_dir(root / "clean")
    ensure_dir(root / "out")
    files = _write_canvases(
        root,
        spec,
        {
            "idle": hero_idle(),
            "attack": hero_attack(),
        },
    )
    return {"spec": spec, "files": files}
