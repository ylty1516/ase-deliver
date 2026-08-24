"""Hand-authored 32x32 game sprites: a shaded slime plus props."""

from __future__ import annotations

import math

from .pixelkit import Canvas, RGB

# Dedicated indexed palette — still a tight game ramp, not truecolor.
OUT = (20, 16, 32)
DARK = (31, 74, 53)
MID = (54, 128, 67)
BODY = (92, 196, 74)
HI = (176, 232, 124)
WHITE = (255, 255, 255)
INK = (18, 14, 28)
CHEEK = (240, 118, 128)
MOUTH = (196, 48, 64)
GLASS = (176, 214, 228)
GLASS_D = (90, 122, 150)
RED = (212, 52, 64)
RED_D = (148, 32, 48)
RED_H = (246, 130, 138)
CORK = (176, 96, 64)
CORK_D = (112, 56, 40)
GOLD = (254, 214, 72)
GOLD_M = (232, 156, 40)
GOLD_D = (196, 96, 28)
WOOD = (176, 104, 64)
WOOD_D = (110, 54, 44)
WOOD_H = (220, 168, 112)
METAL = (192, 203, 220)
METAL_D = (90, 105, 136)
STEEL = (214, 226, 236)
STEEL_D = (118, 136, 160)


def _grounded(size: int, rx: float, ry: float, lift: float, lean: float) -> tuple[float, float, float, float]:
    bottom = size - 2 - lift
    cy = bottom - ry
    cx = size / 2 + lean
    return cx, cy, rx, ry


def _eyes(c: Canvas, cx: float, cy: float, ry: float, look_x: int, look_y: int, blink: bool) -> None:
    eye_y = cy - ry * 0.18
    for side, ox in ((-1, -3.6), (1, 3.6)):
        ex = cx + ox
        if blink:
            c.rect(int(ex) - 2, int(eye_y), int(ex) + 2, int(eye_y) + 1, INK)
            continue
        c.ellipse(ex, eye_y, 2.6, 3.1, WHITE)
        c.ellipse(ex + look_x * 0.7, eye_y + look_y * 0.6 + 0.4, 1.35, 1.7, INK)
        c.set(int(ex - 1), int(eye_y - 1), WHITE)
        # cheek
        c.set(int(ex + side * 2), int(eye_y + 3), CHEEK)
        c.set(int(ex + side * 3), int(eye_y + 3), CHEEK)


def _mouth(c: Canvas, cx: float, cy: float, kind: str) -> None:
    mx, my = int(cx), int(cy + 3)
    if kind == "o":
        c.ellipse(mx, my + 1, 1.6, 1.4, MOUTH)
        return
    if kind == "flat":
        c.rect(mx - 2, my, mx + 2, my, INK)
        return
    # smile
    c.set(mx - 2, my, INK)
    c.set(mx - 1, my + 1, INK)
    c.set(mx, my + 1, INK)
    c.set(mx + 1, my + 1, INK)
    c.set(mx + 2, my, INK)


def slime_frame(
    *,
    size: int = 32,
    squash_y: float = 1.0,
    lift: float = 0.0,
    lean: float = 0.0,
    look_x: int = 1,
    look_y: int = 0,
    mouth: str = "smile",
    blink: bool = False,
) -> Canvas:
    squash_x = 1.0 / max(0.78, squash_y)
    rx = min(11.4 * squash_x, size / 2 - 2.6)
    ry = min(10.2 * squash_y, size / 2 - 3.0)
    cx, cy, rx, ry = _grounded(size, rx, ry, lift, lean)
    c = Canvas.blank(size, size)
    c.ellipse(cx, cy, rx, ry, BODY)
    body_px = c.collect(BODY)
    c.shade_body(body_px, cx, cy, rx, ry, DARK, MID, BODY, HI)
    _eyes(c, cx, cy, ry, look_x, look_y, blink)
    _mouth(c, cx, cy, mouth)
    c.outline(OUT)
    return c


def slime_idle(n: int = 6) -> list[Canvas]:
    frames = []
    for i in range(n):
        t = i / n * 2 * math.pi
        squash = 1.0 + 0.11 * math.cos(t)
        look_y = -1 if math.cos(t) > 0.45 else 0
        blink = i == n - 1
        frames.append(
            slime_frame(
                squash_y=squash,
                look_x=1,
                look_y=look_y,
                mouth="smile",
                blink=blink,
            )
        )
    return frames


def slime_walk(n: int = 6) -> list[Canvas]:
    # Hop-walk, in place, facing right.
    hops = [
        (0.78, 0.0, 1.0, "flat"),
        (1.16, 3.0, 2.2, "o"),
        (1.08, 6.0, 2.0, "o"),
        (1.12, 4.0, 1.4, "smile"),
        (0.84, 1.0, 1.2, "flat"),
        (0.96, 0.0, 0.4, "smile"),
    ]
    frames = []
    for i in range(n):
        squash, lift, lean, mouth = hops[i % len(hops)]
        frames.append(
            slime_frame(
                squash_y=squash,
                lift=lift,
                lean=lean,
                look_x=2,
                look_y=0,
                mouth=mouth,
            )
        )
    return frames


def slime_jump() -> list[Canvas]:
    return [
        slime_frame(squash_y=0.78, lift=0, lean=0, look_x=1, look_y=1, mouth="flat"),
        slime_frame(squash_y=1.22, lift=5, lean=0.4, look_x=1, look_y=-1, mouth="o"),
        slime_frame(squash_y=1.04, lift=7, lean=0.2, look_x=1, look_y=-1, mouth="o"),
        slime_frame(squash_y=0.90, lift=2, lean=0, look_x=1, look_y=1, mouth="flat"),
    ]


def potion_frame(glow: float = 0.0) -> Canvas:
    c = Canvas.blank(32, 32)
    # cork
    c.rect(14, 4, 17, 7, CORK)
    c.rect(14, 4, 17, 5, CORK_D)
    # neck
    c.rect(14, 8, 17, 11, GLASS)
    c.rect(14, 8, 14, 11, GLASS_D)
    # bottle body
    c.ellipse(16, 20, 7.4, 8.4, GLASS)
    # liquid
    liquid = RED_H if glow > 0.5 else RED
    for y in range(16, 28):
        for x in range(9, 24):
            if c.get(x, y) == GLASS and y >= 17:
                nx = (x - 16) / 7.0
                ny = (y - 22) / 7.5
                if nx * nx + ny * ny <= 0.82:
                    if y >= 24:
                        c.set(x, y, RED_D)
                    elif x <= 12:
                        c.set(x, y, RED_H)
                    else:
                        c.set(x, y, liquid)
    # glass shine
    c.set(12, 16, WHITE)
    c.set(12, 17, WHITE)
    c.set(11, 18, GLASS)
    c.outline(OUT)
    return c


def coin_frame(phase: float) -> Canvas:
    c = Canvas.blank(32, 32)
    squash = 0.55 + 0.45 * abs(math.cos(phase))
    c.ellipse(16, 17, 8.5 * squash, 8.5, GOLD)
    inner = c.collect(GOLD)
    for x, y in inner:
        ny = (y - 17) / 8.5
        nx = (x - 16) / max(8.5 * squash, 0.4)
        if nx * nx + ny * ny > 0.55:
            c.set(x, y, GOLD_M)
        if ny > 0.35:
            c.set(x, y, GOLD_D)
        if nx < -0.25 and ny < -0.2:
            c.set(x, y, GOLD)
    c.ellipse(16, 17, 3.2 * squash, 3.2, GOLD_D)
    if squash > 0.75:
        c.set(13, 13, WHITE)
        c.set(14, 12, WHITE)
    c.outline(OUT)
    return c


def chest_frame() -> Canvas:
    c = Canvas.blank(32, 32)
    c.rect(6, 26, 25, 28, WOOD_D)
    c.rect(7, 16, 24, 26, WOOD)
    for y in (18, 21, 24):
        c.rect(8, y, 23, y, WOOD_D)
    c.rect(7, 16, 24, 17, WOOD_H)
    c.ellipse(16, 14, 9.0, 5.2, WOOD_H)
    c.rect(7, 13, 24, 16, WOOD_H)
    c.rect(7, 12, 24, 13, WOOD)
    c.rect(7, 15, 24, 16, WOOD_D)
    c.rect(7, 15, 24, 17, METAL_D)
    c.rect(11, 12, 13, 27, METAL)
    c.rect(18, 12, 20, 27, METAL)
    c.rect(11, 12, 13, 12, WHITE)
    c.ellipse(16, 18, 2.4, 2.4, GOLD)
    c.set(16, 18, GOLD_D)
    c.set(16, 17, GOLD_M)
    c.outline(OUT)
    return c


def sword_frame() -> Canvas:
    c = Canvas.blank(32, 32)
    for i in range(16):
        x = 9 + i
        y = 23 - i
        c.set(x, y, STEEL)
        c.set(x + 1, y, STEEL)
        c.set(x, y - 1, WHITE if i > 7 else STEEL)
        c.set(x + 1, y - 1, STEEL)
        c.set(x - 1, y, STEEL_D)
        c.set(x, y + 1, STEEL_D)
    c.set(25, 7, WHITE)
    c.set(26, 6, STEEL)
    c.set(24, 6, WHITE)
    c.rect(6, 20, 15, 23, GOLD)
    c.rect(6, 20, 15, 20, GOLD_M)
    c.rect(6, 23, 15, 23, GOLD_D)
    c.rect(8, 24, 12, 28, CORK)
    c.rect(8, 24, 8, 28, CORK_D)
    c.rect(12, 24, 12, 28, WOOD)
    c.ellipse(10, 29.4, 2.3, 1.7, GOLD)
    c.outline(OUT)
    return c


def spark_frames() -> list[Canvas]:
    frames = []
    for i, r in enumerate((2.0, 4.2, 6.5, 8.0, 6.0, 3.0)):
        c = Canvas.blank(32, 32)
        c.disc(16, 16, r, GOLD if i % 2 == 0 else GOLD_M)
        c.disc(16, 16, max(0.8, r * 0.45), WHITE if i < 3 else GOLD)
        if r > 5:
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                x = int(16 + math.cos(rad) * (r + 2))
                y = int(16 + math.sin(rad) * (r + 2))
                c.set(x, y, GOLD)
        c.outline(OUT)
        frames.append(c)
    return frames


SLIME_PALETTE = [
    f"#{r:02x}{g:02x}{b:02x}"
    for r, g, b in (OUT, DARK, MID, BODY, HI, WHITE, INK, CHEEK, MOUTH, GLASS, GLASS_D, RED, RED_D, RED_H, CORK, CORK_D, GOLD, GOLD_M, GOLD_D, WOOD, WOOD_D, WOOD_H, METAL, METAL_D, STEEL, STEEL_D)
]
