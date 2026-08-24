from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from . import SCHEMA
from .palettes import resolve_palette
from .util import dump_json, load_json

KINDS = ("character", "prop", "tileset", "ui", "fx", "portrait", "concept")
COLOR_MODES = ("rgba", "indexed")
DIRECTIONS = {
    "forward": 0,
    "reverse": 1,
    "pingpong": 2,
    "ping-pong": 2,
    "pingpong-reverse": 3,
    "ping-pong-reverse": 3,
}
ANCHORS = (
    "center",
    "bottom-center",
    "bottom-left",
    "bottom-right",
    "top-center",
    "top-left",
    "top-right",
    "center-left",
    "center-right",
)


class SpecError(ValueError):
    pass


def spec_path(project: Path) -> Path:
    if project.is_file() and project.suffix.lower() in {".json"}:
        return project
    return project / "spec.json"


def load_spec(project: Path) -> dict[str, Any]:
    path = spec_path(project)
    if not path.is_file():
        raise SpecError(f"Missing spec.json at {path}")
    spec = load_json(path)
    if not isinstance(spec, dict):
        raise SpecError("spec.json must be an object")
    return spec


def save_spec(project: Path, spec: dict[str, Any]) -> Path:
    path = spec_path(project)
    dump_json(path, spec)
    return path


def project_dir(project: Path) -> Path:
    path = Path(project)
    if path.is_file():
        return path.parent
    return path


def sources_cfg(spec: dict[str, Any]) -> dict[str, Any]:
    src = dict(spec.get("sources") or {})
    src.setdefault("dir", "raw")
    src.setdefault("cleanDir", "clean")
    src.setdefault("pattern", "{tag}_{frame:02d}.png")
    src.setdefault("cornerKey", True)
    src.setdefault("keyColors", ["#FF00FF", "#00FF00"])
    src.setdefault("tolerance", 28)
    src.setdefault("anchor", "bottom-center")
    src.setdefault("padding", 1)
    src.setdefault("scaleMode", "contain")
    return src


def raw_dir(root: Path, spec: dict[str, Any]) -> Path:
    return root / sources_cfg(spec)["dir"]


def clean_dir(root: Path, spec: dict[str, Any]) -> Path:
    return root / sources_cfg(spec)["cleanDir"]


def out_dir(root: Path, spec: dict[str, Any] | None = None) -> Path:
    name = (spec or {}).get("outDir") or "out"
    return root / name


def canvas_size(spec: dict[str, Any]) -> tuple[int, int]:
    canvas = spec.get("canvas") or {}
    w = int(canvas.get("width") or spec.get("width") or 0)
    h = int(canvas.get("height") or spec.get("height") or 0)
    if w <= 0 or h <= 0:
        raise SpecError("canvas.width and canvas.height must be positive integers")
    if w > 4096 or h > 4096:
        raise SpecError("canvas is too large (max 4096)")
    return w, h


def color_mode(spec: dict[str, Any]) -> str:
    mode = str(spec.get("colorMode") or "indexed").lower()
    if mode in {"rgb", "rgba", "truecolor"}:
        return "rgba"
    if mode in {"indexed", "index", "palette"}:
        return "indexed"
    raise SpecError(f"Unsupported colorMode {mode!r}")


def layer_names(spec: dict[str, Any]) -> list[str]:
    layers = spec.get("layers") or [{"name": "sprite"}]
    names: list[str] = []
    for layer in layers:
        if isinstance(layer, str):
            names.append(layer)
        else:
            names.append(str(layer["name"]))
    if not names:
        raise SpecError("At least one layer is required")
    return names


def format_cel_name(pattern: str, *, tag: str, frame: int, layer: str) -> str:
    return pattern.format(tag=tag, frame=frame, layer=layer)


def expand_spec(spec: dict[str, Any]) -> dict[str, Any]:
    spec = deepcopy(spec)
    validate_base(spec)
    tags = spec.get("tags") or []
    frames = spec.get("frames")
    if frames:
        _fill_tag_ranges_from_frames(spec)
        return spec

    src = sources_cfg(spec)
    pattern = src["pattern"]
    layers = layer_names(spec)
    out_frames: list[dict[str, Any]] = []
    expanded_tags: list[dict[str, Any]] = []
    cursor = 0
    for tag in tags:
        name = str(tag["name"])
        if "from" in tag and "to" in tag:
            n = int(tag["to"]) - int(tag["from"]) + 1
        else:
            n = int(tag.get("frames") or 1)
        if n <= 0:
            raise SpecError(f"Tag {name!r} has no frames")
        duration = int(tag.get("duration") or 100)
        direction = str(tag.get("direction") or "forward").lower()
        for i in range(n):
            cels = {}
            for layer in layers:
                cels[layer] = format_cel_name(pattern, tag=name, frame=i, layer=layer)
            out_frames.append(
                {
                    "duration": int(tag.get("frameDurations", [duration] * n)[i] if tag.get("frameDurations") else duration),
                    "cels": cels,
                    "tag": name,
                    "tagIndex": i,
                }
            )
        expanded_tags.append(
            {
                "name": name,
                "from": cursor,
                "to": cursor + n - 1,
                "direction": direction,
                "duration": duration,
                "repeat": int(tag.get("repeat") or 0),
            }
        )
        cursor += n
    spec["frames"] = out_frames
    spec["tags"] = expanded_tags
    spec["sources"] = src
    return spec


def _fill_tag_ranges_from_frames(spec: dict[str, Any]) -> None:
    frames = spec["frames"]
    if spec.get("tags"):
        return
    # infer a single "default" tag
    spec["tags"] = [
        {
            "name": "default",
            "from": 0,
            "to": max(0, len(frames) - 1),
            "direction": "forward",
            "repeat": 0,
        }
    ]


def validate_base(spec: dict[str, Any]) -> None:
    schema = spec.get("schema") or SCHEMA
    if schema != SCHEMA:
        raise SpecError(f"Unsupported schema {schema!r}; expected {SCHEMA}")
    name = str(spec.get("name") or "").strip()
    if not name:
        raise SpecError("spec.name is required")
    kind = str(spec.get("kind") or "character")
    if kind not in KINDS:
        raise SpecError(f"Unknown kind {kind!r}; expected one of {', '.join(KINDS)}")
    color_mode(spec)
    canvas_size(spec)
    src = spec.get("sources") or {}
    anchor = str(src.get("anchor") or "bottom-center")
    if anchor not in ANCHORS:
        raise SpecError(f"Unknown anchor {anchor!r}")
    tags = spec.get("tags") or []
    frames = spec.get("frames")
    if not tags and not frames:
        raise SpecError("spec needs tags or frames")
    resolve_palette(spec.get("palette") or "endesga-32")
    for tag in tags:
        if not tag.get("name"):
            raise SpecError("Every tag needs a name")
        direction = str(tag.get("direction") or "forward").lower()
        if direction not in DIRECTIONS:
            raise SpecError(f"Unknown tag direction {direction!r}")


def direction_code(name: str) -> int:
    key = name.lower()
    if key not in DIRECTIONS:
        raise SpecError(f"Unknown direction {name!r}")
    return DIRECTIONS[key]


def required_cel_files(spec: dict[str, Any]) -> list[dict[str, Any]]:
    expanded = expand_spec(spec)
    items: list[dict[str, Any]] = []
    for index, frame in enumerate(expanded["frames"]):
        for layer, filename in (frame.get("cels") or {}).items():
            items.append(
                {
                    "frame": index,
                    "layer": layer,
                    "tag": frame.get("tag"),
                    "tagIndex": frame.get("tagIndex"),
                    "file": filename,
                    "duration": frame.get("duration", 100),
                }
            )
    return items
