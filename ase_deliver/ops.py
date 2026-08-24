from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .brief import generation_brief
from .compile import compile_project, ingest_project
from .demo import seed_demo_project, seed_props_project
from .doctor import doctor, find_aseprite
from .export import export_project
from .images import rasterize_pixels
from .spec import (
    SpecError,
    expand_spec,
    format_cel_name,
    load_spec,
    out_dir,
    project_dir,
    raw_dir,
    save_spec,
    sources_cfg,
)
from .templates import get_template, list_templates
from .util import dump_json, ensure_dir
from .validate import validate_project


def init_project(
    dest: str | Path,
    template: str,
    name: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    dest = Path(dest)
    spec = get_template(template)
    spec["name"] = name or spec["name"]
    if description:
        spec["description"] = description
    if dest.exists() and any(dest.iterdir()):
        raise SpecError(f"{dest} already exists and is not empty")
    ensure_dir(dest)
    save_spec(dest, spec)
    ensure_dir(raw_dir(dest, spec))
    ensure_dir(dest / sources_cfg(spec)["cleanDir"])
    ensure_dir(out_dir(dest, spec))
    brief = generation_brief(dest)
    return {
        "ok": True,
        "project": str(dest.resolve()),
        "spec": str((dest / "spec.json").resolve()),
        "template": template,
        "rawDir": str(raw_dir(dest, spec).resolve()),
        "requiredFiles": brief["files"],
        "brief": brief["brief"],
        "prompt": brief["prompt"],
    }


def paint_cel(
    project: str | Path,
    payload: dict[str, Any],
    tag: str,
    frame: int = 0,
    layer: str | None = None,
) -> dict[str, Any]:
    root = project_dir(Path(project))
    spec = expand_spec(load_spec(root))
    layer = layer or (spec.get("layers") or [{"name": "sprite"}])[0]
    layer_name = layer if isinstance(layer, str) else layer["name"]
    pattern = sources_cfg(spec)["pattern"]
    filename = format_cel_name(pattern, tag=tag, frame=frame, layer=layer_name)
    raw = ensure_dir(raw_dir(root, spec))
    png_path = raw / filename
    json_path = png_path.with_suffix(".json")
    dump_json(json_path, payload)
    im = rasterize_pixels(payload)
    im.save(png_path)
    return {
        "ok": True,
        "png": str(png_path),
        "json": str(json_path),
        "size": list(im.size),
        "tag": tag,
        "frame": frame,
        "layer": layer_name,
    }


def build_project(project: str | Path) -> dict[str, Any]:
    root = project_dir(Path(project))
    compiled = compile_project(root, ingest_first=True)
    if not compiled.get("ok"):
        return compiled
    exported = export_project(root)
    validated = validate_project(root)
    return {
        "ok": bool(compiled.get("ok") and exported.get("ok") and validated.get("ok")),
        "compile": compiled,
        "export": exported,
        "validate": validated,
        "deliverable": validated.get("file"),
    }


def open_in_aseprite(project: str | Path) -> dict[str, Any]:
    root = Path(project)
    ase = find_aseprite()
    if not ase:
        return {"ok": False, "error": "Aseprite executable not found. Set ASEPRITE."}
    if root.is_file() and root.suffix.lower() in {".ase", ".aseprite"}:
        target = root
    else:
        spec = load_spec(project_dir(root))
        target = out_dir(project_dir(root), spec) / f"{spec['name']}.aseprite"
    if not target.is_file():
        return {"ok": False, "error": f"Nothing to open: {target}"}
    subprocess.Popen([str(ase), str(target)])
    return {"ok": True, "file": str(target), "aseprite": str(ase)}


def demo_project(dest: str | Path, open_file: bool = False) -> dict[str, Any]:
    dest = Path(dest)
    seeded = seed_demo_project(dest, name="slime")
    built = build_project(dest)
    props_dir = dest.parent / "props"
    props = seed_props_project(props_dir)
    props_built = build_project(props_dir)
    opened = None
    if open_file:
        opened = open_in_aseprite(dest)
    return {
        "ok": bool(built.get("ok") and props_built.get("ok")),
        "project": str(dest.resolve()),
        "propsProject": str(props_dir.resolve()),
        "seededFiles": seeded["files"],
        "propsFiles": props["files"],
        "build": built,
        "propsBuild": props_built,
        "opened": opened,
    }


def project_status(project: str | Path) -> dict[str, Any]:
    root = project_dir(Path(project))
    spec = expand_spec(load_spec(root))
    from .spec import required_cel_files

    required = required_cel_files(spec)
    raw = raw_dir(root, spec)
    present = []
    missing = []
    for item in required:
        name = str(item["file"])
        png = raw / name
        js = png.with_suffix(".json")
        if png.is_file() or js.is_file():
            present.append(name)
        else:
            missing.append(name)
    dest = out_dir(root, spec) / f"{spec['name']}.aseprite"
    return {
        "ok": True,
        "project": str(root.resolve()),
        "name": spec["name"],
        "kind": spec.get("kind"),
        "canvas": spec.get("canvas"),
        "tags": [t["name"] for t in spec.get("tags") or []],
        "required": len(required),
        "present": present,
        "missing": missing,
        "aseprite": str(dest) if dest.is_file() else None,
    }


__all__ = [
    "init_project",
    "paint_cel",
    "build_project",
    "open_in_aseprite",
    "demo_project",
    "project_status",
    "ingest_project",
    "compile_project",
    "export_project",
    "validate_project",
    "generation_brief",
    "list_templates",
    "get_template",
    "doctor",
]
