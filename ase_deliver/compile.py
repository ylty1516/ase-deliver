from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from .asefile import AseCel, AseFrame, AseLayer, AseSlice, AseSprite, AseTag, write_aseprite
from .images import fit_to_canvas, key_background, load_source, quantize_rgba, rasterize_pixels
from .palettes import resolve_palette
from .spec import (
    SpecError,
    canvas_size,
    clean_dir,
    color_mode,
    direction_code,
    expand_spec,
    load_spec,
    out_dir,
    project_dir,
    raw_dir,
    sources_cfg,
)


def _candidate_names(filename: str) -> list[str]:
    name = str(filename)
    names = [name]
    png = str(Path(name).with_suffix(".png"))
    js = str(Path(name).with_suffix(".json"))
    for extra in (png, js):
        if extra not in names:
            names.append(extra)
    return names


def _find_source(root: Path, spec: dict[str, Any], filename: str) -> Path:
    names = _candidate_names(filename)
    folders = [clean_dir(root, spec), raw_dir(root, spec), root]
    for folder in folders:
        for name in names:
            candidate = folder / name
            if candidate.is_file():
                return candidate
            abs_candidate = Path(name)
            if abs_candidate.is_file():
                return abs_candidate
    raise SpecError(f"Missing source image: {filename} (looked in clean/ and raw/)")


def _load_cel_image(root: Path, spec: dict[str, Any], filename: str) -> Image.Image:
    return load_source(_find_source(root, spec, filename))


def load_prepared_cel(root: Path, spec: dict[str, Any], source: Any) -> Image.Image:
    if isinstance(source, dict):
        return _prepare_image(rasterize_pixels(source), spec)
    path = _find_source(root, spec, str(source))
    image = load_source(path)
    # clean/ is already keyed, fitted, quantized — do not scale it again.
    try:
        path.relative_to(clean_dir(root, spec))
        return image.convert("RGBA")
    except ValueError:
        return _prepare_image(image, spec)


def _prepare_image(im: Image.Image, spec: dict[str, Any]) -> Image.Image:
    w, h = canvas_size(spec)
    src = sources_cfg(spec)
    keyed = key_background(
        im,
        key_colors=src.get("keyColors") or [],
        corner_key=bool(src.get("cornerKey", True)),
        tolerance=int(src.get("tolerance") or 28),
    )
    fitted = fit_to_canvas(
        keyed,
        w,
        h,
        anchor=str(src.get("anchor") or "bottom-center"),
        padding=int(src.get("padding") or 1),
        scale_mode=str(src.get("scaleMode") or "contain"),
    )
    if color_mode(spec) == "indexed":
        palette = resolve_palette(spec.get("palette") or "endesga-32")
        fitted = quantize_rgba(fitted, palette, transparent_index=int(spec.get("transparentIndex") or 0))
    return fitted


def ingest_project(project: Path) -> dict[str, Any]:
    root = project_dir(project)
    spec = expand_spec(load_spec(root))
    w, h = canvas_size(spec)
    raw = raw_dir(root, spec)
    clean = clean_dir(root, spec)
    clean.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    missing: list[str] = []
    sheet = spec.get("sheet")
    if sheet:
        sheet_path = root / sheet["file"] if not Path(sheet["file"]).is_file() else Path(sheet["file"])
        if not sheet_path.is_file():
            sheet_path = raw / sheet["file"]
        if not sheet_path.is_file():
            raise SpecError(f"Sprite sheet not found: {sheet.get('file')}")
        from .images import slice_sheet

        cells = slice_sheet(
            load_source(sheet_path),
            int(sheet["cellWidth"]),
            int(sheet["cellHeight"]),
            columns=sheet.get("columns"),
            rows=sheet.get("rows"),
            layout=str(sheet.get("layout") or "row"),
        )
        for index, frame in enumerate(spec["frames"]):
            if index >= len(cells):
                missing.append(f"sheet frame {index}")
                continue
            for layer, filename in (frame.get("cels") or {}).items():
                dest = clean / filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                img = _prepare_image(cells[index], spec)
                img.save(dest)
                written.append(str(dest))
        return {
            "ok": not missing,
            "written": written,
            "missing": missing,
            "canvas": [w, h],
            "frames": len(spec["frames"]),
        }

    for frame in spec["frames"]:
        for _layer, filename in (frame.get("cels") or {}).items():
            raw_file = raw / filename
            json_file = raw / Path(filename).with_suffix(".json")
            if not raw_file.is_file() and json_file.is_file():
                raw_file = json_file
            if not raw_file.is_file():
                missing.append(filename)
                continue
            dest = clean / filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            img = _prepare_image(load_source(raw_file), spec)
            dest = dest.with_suffix(".png")
            img.save(dest)
            # Keep spec filename even if source was json.
            if dest.name != Path(filename).name:
                png_dest = clean / Path(filename).with_suffix(".png")
                png_dest.parent.mkdir(parents=True, exist_ok=True)
                img.save(png_dest)
            written.append(str(dest))
    return {
        "ok": not missing,
        "written": written,
        "missing": missing,
        "canvas": [w, h],
        "frames": len(spec["frames"]),
        "rawDir": str(raw),
        "cleanDir": str(clean),
    }


def compile_project(project: Path, ingest_first: bool = True) -> dict[str, Any]:
    root = project_dir(project)
    spec = expand_spec(load_spec(root))
    if ingest_first:
        ingested = ingest_project(root)
        if ingested.get("missing"):
            return {
                "ok": False,
                "error": "Missing source files",
                "missing": ingested["missing"],
                "hint": "Put the listed files in raw/, then run ingest/build again.",
            }
    else:
        ingested = None

    w, h = canvas_size(spec)
    mode = color_mode(spec)
    palette = resolve_palette(spec.get("palette") or "endesga-32")
    layers = []
    for entry in spec.get("layers") or [{"name": "sprite"}]:
        if isinstance(entry, str):
            layers.append(AseLayer(name=entry))
        else:
            layers.append(
                AseLayer(
                    name=str(entry["name"]),
                    opacity=int(entry.get("opacity") or 255),
                    visible=bool(entry.get("visible", True)),
                )
            )
    name_to_index = {layer.name: i for i, layer in enumerate(layers)}

    frames: list[AseFrame] = []
    for frame in spec["frames"]:
        cels: list[AseCel] = []
        for layer_name, filename in (frame.get("cels") or {}).items():
            if layer_name not in name_to_index:
                raise SpecError(f"Cel references unknown layer {layer_name!r}")
            im = load_prepared_cel(root, spec, filename)
            cels.append(AseCel(layer=name_to_index[layer_name], image=im))
        frames.append(AseFrame(duration=int(frame.get("duration") or 100), cels=cels))

    tags = [
        AseTag(
            name=str(tag["name"]),
            from_frame=int(tag["from"]),
            to_frame=int(tag["to"]),
            direction=direction_code(str(tag.get("direction") or "forward")),
            repeat=int(tag.get("repeat") or 0),
        )
        for tag in spec.get("tags") or []
    ]
    slices: list[AseSlice] = []
    for sl in spec.get("slices") or []:
        pivot = sl.get("pivot")
        nine = sl.get("ninePatch") or sl.get("nine_patch")
        slices.append(
            AseSlice(
                name=str(sl["name"]),
                x=int(sl.get("x") or 0),
                y=int(sl.get("y") or 0),
                width=int(sl.get("w") or sl.get("width") or w),
                height=int(sl.get("h") or sl.get("height") or h),
                pivot=tuple(pivot) if pivot else (spec.get("pivot") and (int(spec["pivot"]["x"]), int(spec["pivot"]["y"]))) or None,
                nine_patch=tuple(nine) if nine else None,
            )
        )
    if spec.get("pivot") and not slices:
        slices.append(
            AseSlice(
                name="pivot",
                x=0,
                y=0,
                width=w,
                height=h,
                pivot=(int(spec["pivot"]["x"]), int(spec["pivot"]["y"])),
            )
        )
    grid = spec.get("grid") or {}
    sprite = AseSprite(
        width=w,
        height=h,
        color_mode=mode,
        layers=layers,
        frames=frames,
        palette=palette,
        tags=tags,
        slices=slices,
        grid=(int(grid.get("x") or 0), int(grid.get("y") or 0), int(grid.get("width") or 16), int(grid.get("height") or 16)),
        transparent_index=int(spec.get("transparentIndex") or 0),
    )
    dest = out_dir(root, spec) / f"{spec['name']}.aseprite"
    write_aseprite(dest, sprite)
    return {
        "ok": True,
        "file": str(dest),
        "frames": len(frames),
        "layers": [layer.name for layer in layers],
        "tags": [tag.name for tag in tags],
        "canvas": [w, h],
        "colorMode": mode,
        "ingest": ingested,
    }
