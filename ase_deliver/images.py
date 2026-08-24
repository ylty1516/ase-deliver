from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw

from .palettes import nearest_index
from .util import color_dist2, parse_hex


def open_rgba(path: Path) -> Image.Image:
    im = Image.open(path)
    if getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1:
        im.seek(0)
    return im.convert("RGBA")


def rasterize_pixels(payload: dict[str, Any]) -> Image.Image:
    """Draw from an ASCII map or index grid. Any text-only AI can emit this."""
    if "rows" in payload:
        mapping = payload.get("map") or payload.get("palette") or {}
        rows = [str(r) for r in payload["rows"]]
        if not rows:
            raise ValueError("pixels.rows is empty")
        width = max(len(r) for r in rows)
        height = len(rows)
        im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pix = im.load()
        decoded: dict[str, tuple[int, int, int, int] | None] = {}
        for key, val in mapping.items():
            if val in (None, "", "transparent"):
                decoded[str(key)] = None
            else:
                decoded[str(key)] = parse_hex(str(val))
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                color = decoded.get(ch)
                if color is None and ch not in decoded:
                    raise ValueError(f"Character {ch!r} at {x},{y} is not in the pixel map")
                if color is not None:
                    pix[x, y] = color
        return im
    if "indices" in payload:
        width = int(payload["width"])
        height = int(payload["height"])
        palette = [parse_hex(c) for c in payload["palette"]]
        data = payload["indices"]
        im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        pix = im.load()
        i = 0
        for y in range(height):
            for x in range(width):
                idx = int(data[i])
                i += 1
                if 0 <= idx < len(palette):
                    pix[x, y] = palette[idx]
        return im
    raise ValueError("Pixel payload needs rows+map or indices+palette")


def load_source(path: Path) -> Image.Image:
    if path.suffix.lower() == ".json":
        from .util import load_json

        return rasterize_pixels(load_json(path))
    return open_rgba(path)


def _flood_transparent(im: Image.Image, seeds: list[tuple[int, int]], target: tuple[int, int, int], tolerance: int) -> Image.Image:
    im = im.copy()
    w, h = im.size
    pix = im.load()
    seen = [[False] * w for _ in range(h)]
    q = deque()
    for x, y in seeds:
        if 0 <= x < w and 0 <= y < h:
            q.append((x, y))
    limit = tolerance * tolerance * 3
    while q:
        x, y = q.popleft()
        if seen[y][x]:
            continue
        seen[y][x] = True
        r, g, b, a = pix[x, y]
        if a == 0:
            continue
        if color_dist2((r, g, b), target) > limit:
            continue
        pix[x, y] = (r, g, b, 0)
        if x > 0:
            q.append((x - 1, y))
        if x + 1 < w:
            q.append((x + 1, y))
        if y > 0:
            q.append((x, y - 1))
        if y + 1 < h:
            q.append((x, y + 1))
    return im


def key_background(
    im: Image.Image,
    *,
    key_colors: Sequence[str] | None = None,
    corner_key: bool = True,
    tolerance: int = 28,
) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    pix = im.load()
    keys = [parse_hex(c)[:3] for c in (key_colors or [])]
    limit = tolerance * tolerance * 3

    if keys:
        for y in range(h):
            for x in range(w):
                r, g, b, a = pix[x, y]
                if a == 0:
                    continue
                for kc in keys:
                    if color_dist2((r, g, b), kc) <= limit:
                        pix[x, y] = (r, g, b, 0)
                        break

    if corner_key and w > 0 and h > 0:
        corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        samples = []
        for x, y in corners:
            r, g, b, a = pix[x, y]
            if a > 0:
                samples.append((r, g, b))
        if samples:
            # Use the most common-ish corner (first if they agree closely).
            target = samples[0]
            if sum(1 for s in samples if color_dist2(s, target) <= limit) >= max(1, len(samples) - 1):
                im = _flood_transparent(im, corners, target, tolerance)
    return im


def content_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    return im.convert("RGBA").getbbox()


def _anchor_offset(anchor: str, box_w: int, box_h: int, canvas_w: int, canvas_h: int) -> tuple[int, int]:
    ax, ay = "center", "center"
    if "-" in anchor:
        parts = anchor.split("-")
        if parts[0] in {"top", "bottom", "center"}:
            ay, ax = parts[0], parts[1]
        else:
            ax, ay = parts[0], parts[1]
    else:
        if anchor in {"top", "bottom"}:
            ay = anchor
        elif anchor in {"left", "right"}:
            ax = anchor
    x = {"left": 0, "center": (canvas_w - box_w) // 2, "right": canvas_w - box_w}[ax]
    y = {"top": 0, "center": (canvas_h - box_h) // 2, "bottom": canvas_h - box_h}[ay]
    return x, y


def fit_to_canvas(
    im: Image.Image,
    width: int,
    height: int,
    *,
    anchor: str = "bottom-center",
    padding: int = 1,
    scale_mode: str = "contain",
) -> Image.Image:
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    bw, bh = im.size
    pad = max(0, int(padding))
    inner_w = max(1, width - pad * 2)
    inner_h = max(1, height - pad * 2)

    if scale_mode == "none":
        scaled = im
    else:
        if bw <= inner_w and bh <= inner_h and scale_mode in {"fit-down", "contain"}:
            # Prefer integer upscale when it fits exactly-ish.
            sx = inner_w // max(1, bw)
            sy = inner_h // max(1, bh)
            factor = max(1, min(sx, sy))
            if scale_mode == "contain" and factor > 1:
                scaled = im.resize((bw * factor, bh * factor), Image.NEAREST)
            else:
                scaled = im
        else:
            scale = min(inner_w / max(1, bw), inner_h / max(1, bh))
            nw = max(1, int(round(bw * scale)))
            nh = max(1, int(round(bh * scale)))
            resample = Image.NEAREST
            if scale < 0.5:
                # Area filter first, then snap, keeps clusters from photo/AI sources.
                im_box = im.resize((nw, nh), Image.BOX)
                scaled = im_box.resize((nw, nh), Image.NEAREST)
            else:
                scaled = im.resize((nw, nh), resample)

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sw, sh = scaled.size
    if sw > width or sh > height:
        scaled = scaled.resize((min(sw, width), min(sh, height)), Image.NEAREST)
        sw, sh = scaled.size
    x, y = _anchor_offset(anchor, sw, sh, width, height)
    canvas.alpha_composite(scaled, (max(0, x), max(0, y)))
    return canvas


def quantize_rgba(im: Image.Image, palette: Sequence[tuple[int, int, int]], transparent_index: int = 0) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    pix = im.load()
    skip = {transparent_index} if 0 <= transparent_index < len(palette) else set()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opix = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a < 16:
                continue
            idx = nearest_index((r, g, b), palette, skip=skip)
            pr, pg, pb = palette[idx]
            opix[x, y] = (pr, pg, pb, 255)
    return out


def slice_sheet(
    im: Image.Image,
    cell_w: int,
    cell_h: int,
    *,
    columns: int | None = None,
    rows: int | None = None,
    layout: str = "row",
) -> list[Image.Image]:
    im = im.convert("RGBA")
    w, h = im.size
    cols = columns or max(1, w // cell_w)
    rws = rows or max(1, h // cell_h)
    frames: list[Image.Image] = []
    if layout in {"row", "rows", "horizontal"}:
        for y in range(rws):
            for x in range(cols):
                frames.append(im.crop((x * cell_w, y * cell_h, (x + 1) * cell_w, (y + 1) * cell_h)))
    else:
        for x in range(cols):
            for y in range(rws):
                frames.append(im.crop((x * cell_w, y * cell_h, (x + 1) * cell_w, (y + 1) * cell_h)))
    return frames


def unique_colors(im: Image.Image, limit: int = 300) -> int:
    im = im.convert("RGBA")
    colors = set()
    for r, g, b, a in im.getdata():
        if a < 16:
            continue
        colors.add((r, g, b))
        if len(colors) >= limit:
            return limit
    return len(colors)


def composite(layers: Sequence[Image.Image]) -> Image.Image:
    if not layers:
        raise ValueError("No layers to composite")
    base = Image.new("RGBA", layers[0].size, (0, 0, 0, 0))
    for layer in layers:
        base.alpha_composite(layer.convert("RGBA"))
    return base


def checker_preview(im: Image.Image, cell: int = 8) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    draw = ImageDraw.Draw(bg)
    c1, c2 = (40, 40, 48, 255), (28, 28, 34, 255)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=c1 if (x // cell + y // cell) % 2 == 0 else c2)
    bg.alpha_composite(im)
    return bg
