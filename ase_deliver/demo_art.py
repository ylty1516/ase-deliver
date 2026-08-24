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
STEEL_D = (90, 108, 132)
STEEL_M = (154, 174, 196)
LEATHER = (148, 78, 48)
LEATHER_D = (96, 46, 32)
RUBY = (220, 40, 58)


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
    # cork + lip
    c.rect(13, 2, 18, 6, CORK)
    c.rect(13, 2, 18, 3, CORK_D)
    c.rect(12, 6, 19, 7, LEATHER)
    # neck
    c.rect(14, 8, 17, 12, GLASS)
    c.rect(14, 8, 14, 12, GLASS_D)
    c.rect(17, 8, 17, 12, WHITE)
    # shoulder
    c.ellipse(16, 14.5, 4.2, 2.4, GLASS)
    # round flask
    c.ellipse(16, 21.5, 9.2, 8.6, GLASS)
    liquid = RED_H if glow > 0.5 else RED
    for y in range(14, 31):
        for x in range(6, 27):
            if c.get(x, y) != GLASS:
                continue
            if y < 17:
                continue
            if y == 17:
                c.set(x, y, RED_H)
            elif y >= 26 or x >= 22:
                c.set(x, y, RED_D)
            elif x <= 11:
                c.set(x, y, RED_H)
            else:
                c.set(x, y, liquid)
    # glass rim above liquid
    for x in range(12, 21):
        if c.get(x, 16) is not None:
            c.set(x, 16, GLASS)
    # shine + bubble
    c.set(11, 15, WHITE)
    c.set(11, 16, WHITE)
    c.set(10, 17, WHITE)
    c.set(12, 18, GLASS)
    c.set(14, 22, WHITE if glow > 0.5 else RED_H)
    c.set(15, 23, RED_H)
    c.outline(OUT)
    return c


def coin_frame(phase: float) -> Canvas:
    c = Canvas.blank(32, 32)
    squash = 0.38 + 0.62 * abs(math.cos(phase))
    rx, ry = 9.2 * squash, 9.2
    c.ellipse(16, 16, rx, ry, GOLD)
    face = c.collect(GOLD)
    for x, y in face:
        nx = (x + 0.5 - 16) / max(rx, 0.35)
        ny = (y + 0.5 - 16) / ry
        r2 = nx * nx + ny * ny
        if r2 > 0.72:
            c.set(x, y, GOLD_D if ny > 0.15 else GOLD_M)
        elif ny > 0.38:
            c.set(x, y, GOLD_D)
        elif nx < -0.28 and ny < -0.18:
            c.set(x, y, GOLD)
        else:
            c.set(x, y, GOLD_M if r2 > 0.28 else GOLD)
    # stamped star, only when the face is wide enough
    if squash > 0.72:
        # clean 4-point diamond stamp
        c.set(16, 13, GOLD_D)
        c.set(15, 14, GOLD_D)
        c.set(16, 14, WHITE)
        c.set(17, 14, GOLD_D)
        c.set(14, 15, GOLD_D)
        c.set(15, 15, GOLD_D)
        c.set(16, 15, GOLD_D)
        c.set(17, 15, GOLD_D)
        c.set(18, 15, GOLD_D)
        c.set(15, 16, GOLD_D)
        c.set(16, 16, GOLD_D)
        c.set(17, 16, GOLD_D)
        c.set(16, 17, GOLD_D)
        c.set(12, 11, WHITE)
        c.set(13, 10, WHITE)
    c.outline(OUT)
    return c


def chest_frame() -> Canvas:
    c = Canvas.blank(32, 32)
    # lid (overhangs body by 1px)
    c.rect(5, 8, 26, 15, WOOD_H)
    c.rect(5, 8, 26, 9, WOOD)
    c.rect(5, 14, 26, 15, WOOD_D)
    # body
    c.rect(6, 16, 25, 27, WOOD)
    for y in (19, 22, 25):
        c.rect(7, y, 24, y, WOOD_D)
    c.rect(6, 16, 25, 16, WOOD_H)
    c.rect(6, 26, 25, 27, WOOD_D)
    # seam band + mid band
    c.rect(5, 15, 26, 17, METAL)
    c.rect(5, 15, 26, 15, WHITE)
    c.rect(5, 17, 26, 17, METAL_D)
    c.rect(6, 22, 25, 23, METAL_D)
    # vertical straps
    c.rect(10, 8, 12, 27, METAL)
    c.rect(19, 8, 21, 27, METAL)
    c.rect(10, 8, 12, 8, WHITE)
    c.rect(19, 8, 21, 8, WHITE)
    # rivets
    for x, y in ((6, 15), (25, 15), (6, 22), (25, 22), (10, 15), (21, 15)):
        c.set(x, y, STEEL)
    # padlock on the seam
    c.rect(14, 13, 18, 15, GOLD_M)
    c.rect(13, 16, 19, 21, GOLD)
    c.rect(13, 16, 19, 16, GOLD_M)
    c.set(16, 18, GOLD_D)
    c.set(16, 19, INK)
    c.outline(OUT)
    return c


def sword_frame() -> Canvas:
    """Vertical inventory-icon longsword — thick blade, guard, wrapped grip."""
    c = Canvas.blank(32, 32)
    # blade: taper 1px tip -> 7px near guard
    for y in range(2, 20):
        t = (y - 2) / 17.0
        half = 0.7 + t * 3.0
        for dx in range(-5, 6):
            if abs(dx) > half:
                continue
            x = 16 + dx
            if dx <= -half + 0.9:
                col = STEEL_D
            elif dx >= half - 1.1:
                col = WHITE if y < 12 else STEEL
            elif abs(dx) <= 0.8 and 6 <= y <= 17:
                col = STEEL_D  # fuller
            else:
                col = STEEL_M if dx < 0 else STEEL
            c.set(x, y, col)
    # point
    c.set(16, 1, WHITE)
    c.set(15, 2, STEEL)
    c.set(16, 2, WHITE)
    c.set(17, 2, STEEL)
    # ricasso
    c.rect(13, 19, 19, 20, STEEL_M)
    # crossguard
    c.rect(8, 20, 23, 22, GOLD)
    c.rect(8, 20, 23, 20, GOLD_M)
    c.rect(8, 22, 23, 22, GOLD_D)
    c.disc(8, 21, 1.6, GOLD)
    c.disc(23, 21, 1.6, GOLD)
    c.set(8, 21, GOLD_M)
    c.set(23, 21, GOLD_M)
    # ruby in the guard
    c.set(16, 21, RUBY)
    c.set(16, 20, RED_H)
    # wrapped grip
    for y in range(23, 29):
        wrap = LEATHER if y % 2 == 0 else LEATHER_D
        c.rect(13, y, 19, y, wrap)
        c.set(13, y, LEATHER_D)
        c.set(19, y, CORK)
    # pommel
    c.ellipse(16, 29.6, 3.2, 2.2, GOLD)
    c.set(16, 29, GOLD_M)
    c.set(15, 30, GOLD_D)
    c.set(17, 30, GOLD_D)
    c.set(16, 30, GOLD_D)
    c.outline(OUT)
    return c


def spark_frames() -> list[Canvas]:
    frames = []
    sizes = (2.0, 3.5, 5.5, 7.5, 5.0, 2.5)
    for i, r in enumerate(sizes):
        c = Canvas.blank(32, 32)
        c.disc(16, 16, max(1.2, r * 0.45), WHITE)
        c.disc(16, 16, max(1.8, r * 0.7), GOLD)
        for ang in range(0, 360, 45 if i < 3 else 90):
            rad = math.radians(ang)
            length = r + (2 if i % 2 == 0 else 0)
            c.stroke(16, 16, 16 + math.cos(rad) * length, 16 + math.sin(rad) * length, 0.9 if i < 4 else 0.7, GOLD if ang % 90 else WHITE)
        c.outline(OUT)
        frames.append(c)
    return frames


SLIME_PALETTE = [
    f"#{r:02x}{g:02x}{b:02x}"
    for r, g, b in (
        OUT, DARK, MID, BODY, HI, WHITE, INK, CHEEK, MOUTH,
        GLASS, GLASS_D, RED, RED_D, RED_H, CORK, CORK_D,
        GOLD, GOLD_M, GOLD_D, WOOD, WOOD_D, WOOD_H, METAL, METAL_D,
        STEEL, STEEL_D, STEEL_M, LEATHER, LEATHER_D, RUBY,
    )
]
