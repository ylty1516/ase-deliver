"""Tiny pixel-art helpers: ellipses, outlines, vertical shade, palette export."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PIL import Image

RGB = tuple[int, int, int]
Pixel = RGB | None


@dataclass
class Canvas:
    width: int
    height: int
    px: list[list[Pixel]]

    @classmethod
    def blank(cls, width: int, height: int) -> "Canvas":
        return cls(width, height, [[None] * width for _ in range(height)])

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set(self, x: int, y: int, color: Pixel) -> None:
        if self.in_bounds(x, y):
            self.px[y][x] = color

    def get(self, x: int, y: int) -> Pixel:
        if not self.in_bounds(x, y):
            return None
        return self.px[y][x]

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, color: RGB, fill: bool = True) -> None:
        if rx <= 0 or ry <= 0:
            return
        min_x = max(0, int(cx - rx - 1))
        max_x = min(self.width - 1, int(cx + rx + 1))
        min_y = max(0, int(cy - ry - 1))
        max_y = min(self.height - 1, int(cy + ry + 1))
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                nx = (x + 0.5 - cx) / rx
                ny = (y + 0.5 - cy) / ry
                if nx * nx + ny * ny <= 1.0:
                    if fill:
                        self.set(x, y, color)
                    else:
                        if abs(nx * nx + ny * ny - 1.0) < 0.18:
                            self.set(x, y, color)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: RGB) -> None:
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.set(x, y, color)

    def disc(self, cx: float, cy: float, r: float, color: RGB) -> None:
        self.ellipse(cx, cy, r, r, color)

    def shade_body(self, mask: Iterable[tuple[int, int]], cx: float, cy: float, rx: float, ry: float, dark: RGB, mid: RGB, body: RGB, hi: RGB) -> None:
        for x, y in mask:
            nx = (x + 0.5 - cx) / max(rx, 0.01)
            ny = (y + 0.5 - cy) / max(ry, 0.01)
            # lighting from top-left
            light = -0.55 * nx - 0.85 * ny
            if light > 0.72 and ny < -0.15:
                self.set(x, y, hi)
            elif ny > 0.42 or light < -0.35:
                self.set(x, y, dark)
            elif ny > 0.12 or light < -0.05:
                self.set(x, y, mid)
            else:
                self.set(x, y, body)
            # cheap dither on the mid/dark seam
            if 0.08 < ny < 0.22 and (x + y) % 2 == 0 and light < 0.2:
                self.set(x, y, dark if self.get(x, y) == mid else self.get(x, y))

    def collect(self, color: RGB | None = None) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                p = self.px[y][x]
                if p is None:
                    continue
                if color is None or p == color:
                    out.append((x, y))
        return out

    def outline(self, color: RGB) -> None:
        solid = [(x, y) for y in range(self.height) for x in range(self.width) if self.px[y][x] is not None]
        border: list[tuple[int, int]] = []
        for x, y in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not self.in_bounds(nx, ny) or self.px[ny][nx] is None:
                    border.append((x, y))
                    break
        for x, y in border:
            self.set(x, y, color)

    def to_image(self) -> Image.Image:
        im = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        pix = im.load()
        for y in range(self.height):
            for x in range(self.width):
                c = self.px[y][x]
                if c is not None:
                    pix[x, y] = (c[0], c[1], c[2], 255)
        return im

    def to_payload(self) -> dict:
        palette: dict[str, str | None] = {".": None}
        rows: list[str] = []
        chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        color_to_ch: dict[RGB, str] = {}
        next_i = 0
        for y in range(self.height):
            row = []
            for x in range(self.width):
                c = self.px[y][x]
                if c is None:
                    row.append(".")
                    continue
                if c not in color_to_ch:
                    color_to_ch[c] = chars[next_i]
                    palette[chars[next_i]] = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
                    next_i += 1
                row.append(color_to_ch[c])
            rows.append("".join(row))
        return {"map": palette, "rows": rows}
