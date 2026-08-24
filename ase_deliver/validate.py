from __future__ import annotations

from pathlib import Path
from typing import Any

from .asefile import read_ase_info
from .compile import load_prepared_cel
from .spec import canvas_size, expand_spec, load_spec, out_dir, project_dir, required_cel_files


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def validate_project(project: Path) -> dict[str, Any]:
    root = project_dir(project)
    spec = expand_spec(load_spec(root))
    w, h = canvas_size(spec)
    checks: list[dict[str, Any]] = []
    dest = out_dir(root, spec) / f"{spec['name']}.aseprite"

    required = required_cel_files(spec)
    missing: list[str] = []
    empty_frames: list[int] = []
    edge_hits: list[int] = []
    for item in required:
        filename = item["file"]
        try:
            im = load_prepared_cel(root, spec, filename)
        except Exception:
            missing.append(str(filename))
            continue
        bbox = im.getbbox()
        if bbox is None:
            empty_frames.append(item["frame"])
            continue
        if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == w or bbox[3] == h:
            # touching canvas edge can be OK for tiles, warn for characters
            if spec.get("kind") in {"character", "prop", "portrait"} and bbox[1] == 0:
                edge_hits.append(item["frame"])

    checks.append(
        _check(
            "sources-present",
            not missing,
            "all cel files present" if not missing else f"missing: {', '.join(missing[:12])}",
        )
    )
    checks.append(
        _check(
            "frames-not-empty",
            not empty_frames,
            "every frame has pixels" if not empty_frames else f"empty frames: {empty_frames[:12]}",
        )
    )

    if dest.is_file():
        info = read_ase_info(dest)
        checks.append(_check("aseprite-magic", True, f"{info.width}x{info.height} {info.frames} frames"))
        checks.append(
            _check(
                "aseprite-size",
                info.width == w and info.height == h,
                f"file {info.width}x{info.height} vs spec {w}x{h}",
            )
        )
        checks.append(
            _check(
                "aseprite-frame-count",
                info.frames == len(spec["frames"]),
                f"file {info.frames} vs spec {len(spec['frames'])}",
            )
        )
        want_tags = [t["name"] for t in spec.get("tags") or []]
        checks.append(
            _check(
                "aseprite-tags",
                info.tags == want_tags,
                f"file tags {info.tags} vs spec {want_tags}",
            )
        )
        want_layers = [layer if isinstance(layer, str) else layer["name"] for layer in spec.get("layers") or []]
        checks.append(
            _check(
                "aseprite-layers",
                info.layers == want_layers,
                f"file layers {info.layers} vs spec {want_layers}",
            )
        )
        depth_ok = (spec.get("colorMode") == "rgba" and info.depth == 32) or (
            (spec.get("colorMode") in {None, "indexed"}) and info.depth == 8
        )
        checks.append(_check("color-mode", depth_ok, f"depth={info.depth}"))
    else:
        checks.append(_check("aseprite-file", False, f"missing {dest.name}; run compile"))

    sheet = out_dir(root, spec) / f"{spec['name']}.png"
    gif = out_dir(root, spec) / f"{spec['name']}.gif"
    meta = out_dir(root, spec) / f"{spec['name']}.json"
    checks.append(_check("sprite-sheet", sheet.is_file(), str(sheet.name)))
    checks.append(_check("gif-preview", gif.is_file(), str(gif.name)))
    checks.append(_check("json-meta", meta.is_file(), str(meta.name)))

    if spec.get("kind") in {"character", "prop"}:
        checks.append(
            _check(
                "headroom",
                not edge_hits,
                "subject is not clipped at the top"
                if not edge_hits
                else f"frames touching top edge: {edge_hits[:8]} (may be clipped)",
            )
        )

    ok = all(c["ok"] for c in checks if c["name"] != "headroom")
    return {
        "ok": ok,
        "deliverable": ok,
        "checks": checks,
        "missing": missing,
        "file": str(dest) if dest.is_file() else None,
    }
