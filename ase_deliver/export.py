from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

from .asefile import read_ase_info
from .compile import load_prepared_cel
from .doctor import find_aseprite
from .images import composite
from .spec import canvas_size, expand_spec, load_spec, out_dir, project_dir
from .util import dump_json


def _frame_images(root: Path, spec: dict[str, Any]) -> list[Image.Image]:
    frames: list[Image.Image] = []
    for frame in spec["frames"]:
        layers = []
        for _layer, filename in (frame.get("cels") or {}).items():
            layers.append(load_prepared_cel(root, spec, filename))
        if not layers:
            w, h = canvas_size(spec)
            frames.append(Image.new("RGBA", (w, h), (0, 0, 0, 0)))
        elif len(layers) == 1:
            frames.append(layers[0])
        else:
            frames.append(composite(layers))
    return frames


def _sheet(frames: list[Image.Image], columns: int | None = None) -> Image.Image:
    n = len(frames)
    w, h = frames[0].size
    cols = columns or n
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        x = (i % cols) * w
        y = (i // cols) * h
        sheet.alpha_composite(frame, (x, y))
    return sheet


def export_project(project: Path) -> dict[str, Any]:
    root = project_dir(project)
    spec = expand_spec(load_spec(root))
    dest_dir = out_dir(root, spec)
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = spec["name"]
    frames = _frame_images(root, spec)
    if not frames:
        return {"ok": False, "error": "No frames to export"}
    w, h = frames[0].size
    sheet = _sheet(frames)
    sheet_path = dest_dir / f"{name}.png"
    sheet.save(sheet_path)

    durations = [int(f.get("duration") or 100) for f in spec["frames"]]
    gif_path = dest_dir / f"{name}.gif"
    # GIF needs at least 2 frames for a useful preview; duplicate if needed.
    gif_frames = frames
    gif_durations = durations
    if len(gif_frames) == 1:
        gif_frames = [frames[0], frames[0]]
        gif_durations = [durations[0], durations[0]]
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=gif_durations,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )

    ase_json = {
        "frames": [],
        "meta": {
            "app": "ase-deliver",
            "version": "1.0.0",
            "image": sheet_path.name,
            "format": "RGBA8888",
            "size": {"w": sheet.size[0], "h": sheet.size[1]},
            "scale": "1",
            "frameTags": [
                {
                    "name": tag["name"],
                    "from": tag["from"],
                    "to": tag["to"],
                    "direction": tag.get("direction") or "forward",
                }
                for tag in spec.get("tags") or []
            ],
            "layers": [{"name": layer if isinstance(layer, str) else layer["name"]} for layer in spec.get("layers") or []],
            "size": {"w": w, "h": h},
        },
    }
    for i, frame in enumerate(frames):
        col = i
        row = 0
        ase_json["frames"].append(
            {
                "filename": f"{name} {i}.aseprite",
                "frame": {"x": col * w, "y": row * h, "w": w, "h": h},
                "rotated": False,
                "trimmed": False,
                "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
                "sourceSize": {"w": w, "h": h},
                "duration": durations[i],
            }
        )
    json_path = dest_dir / f"{name}.json"
    dump_json(json_path, ase_json)

    ase_path = dest_dir / f"{name}.aseprite"
    verified = None
    aseprite = find_aseprite()
    if aseprite and ase_path.is_file():
        verify_png = dest_dir / f"{name}.aseprite-cli.png"
        cmd = [
            str(aseprite),
            "-b",
            "--all-layers",
            "--list-tags",
            "--list-layers",
            "--sheet-type",
            "horizontal",
            "--sheet",
            str(verify_png),
            str(ase_path),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            verified = {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "").strip(),
                "stderr": (proc.stderr or "").strip(),
                "sheet": str(verify_png) if verify_png.is_file() else None,
            }
        except Exception as exc:
            verified = {"ok": False, "error": str(exc)}

    info = None
    if ase_path.is_file():
        info = read_ase_info(ase_path)
        info = {
            "frames": info.frames,
            "width": info.width,
            "height": info.height,
            "depth": info.depth,
            "tags": info.tags,
            "layers": info.layers,
        }

    return {
        "ok": True,
        "sheet": str(sheet_path),
        "gif": str(gif_path),
        "json": str(json_path),
        "aseprite": str(ase_path) if ase_path.is_file() else None,
        "frameCount": len(frames),
        "info": info,
        "asepriteCli": verified,
    }
