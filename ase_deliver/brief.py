from __future__ import annotations

from pathlib import Path
from typing import Any

from .palettes import palette_hexes, resolve_palette
from .spec import canvas_size, expand_spec, load_spec, project_dir, raw_dir, required_cel_files, sources_cfg
from .util import write_text

TAG_HINTS = {
    "idle": "Subtle idle / breathing. Same pose, tiny squash-and-stretch. Must loop: last frame flows into first.",
    "walk": "In-place walk cycle, side view facing right, locked camera. Contact / passing / opposite contact. Feet on the bottom pixel. Must loop.",
    "run": "In-place run cycle, side view facing right, more stretch than walk. Must loop.",
    "jump": "Anticipation crouch, then airborne, then peak. Keep the same silhouette family. No ground.",
    "fall": "Airborne falling pose, limbs consistent with jump.",
    "attack": "Anticipation, contact, follow-through. Same weapon/hands every frame.",
    "hurt": "Hit reaction, same character, no extra blood scenery.",
    "die": "Death pose sequence, still isolated on magenta.",
    "front": "Full-body turnaround, facing camera, A-pose or rest pose, feet planted.",
    "side": "Full-body turnaround, strict side view facing right.",
    "back": "Full-body turnaround, facing away from camera.",
    "three-quarter": "Full-body 3/4 view facing right.",
    "normal": "Default UI/state. No text on the asset.",
    "hover": "Hover state. Geometry identical to normal, only color/light changes.",
    "pressed": "Pressed state. Geometry identical to normal, maybe 1px down-shift.",
    "disabled": "Disabled state. Same geometry, desaturated.",
}


def _pose_hint(tag: str, kind: str) -> str:
    if tag in TAG_HINTS:
        return TAG_HINTS[tag]
    if kind == "tileset":
        return "Seamless tile, no unique landmark, lighting from top-left, matches neighbors."
    if kind == "fx":
        return "Transparent background (magenta), centered origin, reads at 32px, loop or one-shot as tagged."
    return f"Animation tag {tag!r}. Same character/object as the rest of the set. Isolated subject."


def generation_brief(project: Path | None = None, spec: dict[str, Any] | None = None) -> dict[str, Any]:
    if spec is None:
        if project is None:
            raise ValueError("project or spec is required")
        root = project_dir(project)
        spec = load_spec(root)
    else:
        root = project_dir(project) if project else Path(".")
    expanded = expand_spec(spec)
    w, h = canvas_size(expanded)
    palette = palette_hexes(resolve_palette(expanded.get("palette") or "endesga-32"))
    src = sources_cfg(expanded)
    required = required_cel_files(expanded)
    by_tag: dict[str, list[str]] = {}
    for item in required:
        by_tag.setdefault(str(item.get("tag") or "default"), []).append(str(item["file"]))

    description = str(expanded.get("description") or expanded.get("subject") or "").strip()
    view = str(expanded.get("view") or "side")
    kind = str(expanded.get("kind") or "character")
    subject_line = description or f"a {kind} game sprite named {expanded['name']}"

    global_rules = [
        f"Production pixel-art game sprite, {w}x{h} pixels (integer scale {w*4}x{h*4} is OK; no other sizes).",
        f"View: {view}. Kind: {kind}.",
        "Isolated subject on a FLAT background of exactly #FF00FF. No ground, no drop shadow, no scenery, no watermark, no text.",
        "Crisp pixels, no anti-aliasing, no blur, no JPEG artifacts, no photographic texture.",
        "Readable silhouette. 1px dark outline if the subject would otherwise melt into the background.",
        "Same character/object in every frame: identical proportions, colors, pivot. Feet sit on the bottom pixel row for standing poses.",
        "Use only this palette: " + ", ".join(palette) + ".",
        f"Save each required filename into {src['dir']}/ exactly as listed. One pose per file.",
    ]
    prompt = (
        f"{w}x{h} pixel art {kind} sprite of {subject_line}, {view} view, "
        "Aseprite 16-bit game asset, crisp pixels, 1px outline, limited palette, "
        "isolated on flat magenta background #FF00FF, no drop shadow, no ground, no scenery."
    )

    tags = []
    for tag in expanded.get("tags") or []:
        name = tag["name"]
        files = by_tag.get(name, [])
        tag_prompt = (
            f"{prompt} Animation: {name}. {_pose_hint(name, kind)} "
            f"{len(files)} frames, keep the subject in the same canvas position."
        )
        tags.append(
            {
                "name": name,
                "from": tag.get("from"),
                "to": tag.get("to"),
                "files": files,
                "hint": _pose_hint(name, kind),
                "prompt": tag_prompt,
            }
        )

    markdown_lines = [
        f"# Generation brief — {expanded['name']}",
        "",
        f"- Canvas: **{w}x{h}**",
        f"- Mode: **{expanded.get('colorMode') or 'indexed'}**",
        f"- Palette: `{expanded.get('palette') or 'endesga-32'}`",
        f"- Drop files into: `{src['dir']}/`",
        f"- Background: `#FF00FF`",
        "",
        "## Subject",
        "",
        subject_line,
        "",
        "## Prompt for any image model",
        "",
        prompt,
        "",
        "## Hard rules",
        "",
    ]
    markdown_lines.extend(f"- {rule}" for rule in global_rules)
    markdown_lines += ["", "## Files"]
    for tag in tags:
        markdown_lines += ["", f"### {tag['name']}", "", tag["hint"], ""]
        markdown_lines.extend(f"- `{name}`" for name in tag["files"])

    text = "\n".join(markdown_lines) + "\n"
    brief_path = None
    if project is not None:
        brief_path = project_dir(project) / "BRIEF.md"
        write_text(brief_path, text)

    return {
        "ok": True,
        "name": expanded["name"],
        "canvas": [w, h],
        "palette": palette,
        "prompt": prompt,
        "rules": global_rules,
        "tags": tags,
        "files": [item["file"] for item in required],
        "rawDir": str(raw_dir(root, expanded)),
        "brief": str(brief_path) if brief_path else None,
        "markdown": text,
    }
