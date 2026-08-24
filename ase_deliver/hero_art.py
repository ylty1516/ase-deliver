"""Side-view hero (勇者) — 48x48 so a slash attack has room for the blade."""

from __future__ import annotations

import math

from .pixelkit import Canvas, RGB

OUT = (20, 16, 32)
WHITE = (255, 255, 255)
INK = (18, 14, 28)
SKIN = (236, 186, 148)
SKIN_D = (196, 140, 108)
HAIR = (86, 48, 32)
HAIR_H = (150, 88, 52)
TUNIC = (52, 108, 196)
TUNIC_D = (32, 68, 148)
TUNIC_H = (118, 170, 230)
CAPE = (188, 44, 58)
CAPE_D = (132, 28, 44)
PANTS = (52, 60, 92)
BOOT = (86, 46, 32)
BOOT_H = (128, 74, 46)
STEEL = (214, 226, 236)
STEEL_M = (154, 174, 196)
STEEL_D = (90, 108, 132)
GOLD = (254, 214, 72)
GOLD_M = (232, 156, 40)
GOLD_D = (196, 96, 28)
SLASH = (255, 244, 180)
SLASH_H = (255, 255, 255)

SIZE = 48
GROUND = 46


def _sword(c: Canvas, hx: float, hy: float, angle: float, length: float) -> None:
    rad = math.radians(angle)
    ux, uy = math.cos(rad), math.sin(rad)
    px, py = -uy, ux
    # blade, thicker at hilt
    steps = 16
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        r = 2.55 * (1.0 - t0) + 0.85 * t0
        x0 = hx + ux * (length * t0)
        y0 = hy + uy * (length * t0)
        x1 = hx + ux * (length * t1)
        y1 = hy + uy * (length * t1)
        col = STEEL_D if t0 > 0.82 else (STEEL if t0 > 0.2 else STEEL_M)
        c.stroke(x0, y0, x1, y1, r, col)
        c.stroke(x0 + px * 0.8, y0 + py * 0.8, x1 + px * 0.5, y1 + py * 0.5, max(0.55, r * 0.35), WHITE if t0 < 0.55 else STEEL)
    # tip
    c.disc(hx + ux * length, hy + uy * length, 0.9, WHITE)
    # guard
    c.stroke(hx - px * 3.4, hy - py * 3.4, hx + px * 3.4, hy + py * 3.4, 1.25, GOLD)
    c.disc(hx - px * 3.4, hy - py * 3.4, 1.1, GOLD_M)
    c.disc(hx + px * 3.4, hy + py * 3.4, 1.1, GOLD_M)
    # grip
    c.stroke(hx - ux * 1.2, hy - uy * 1.2, hx - ux * 4.2, hy - uy * 4.2, 1.15, BOOT)
    c.disc(hx - ux * 4.6, hy - uy * 4.6, 1.5, GOLD)


def _slash_arc(c: Canvas, hx: float, hy: float, angle: float, length: float, span: int) -> None:
    for a in range(int(angle - span), int(angle + 8), 5):
        rad = math.radians(a)
        dist = length + 2.5
        x = int(hx + math.cos(rad) * dist)
        y = int(hy + math.sin(rad) * dist)
        c.set(x, y, SLASH_H if a % 10 == 0 else SLASH)
        c.set(x + 1, y, SLASH)


def hero_pose(
    *,
    lean: float = 0.0,
    front_foot: float = 2.0,
    back_foot: float = -2.0,
    hand_x: float = 6.0,
    hand_y: float = -2.0,
    sword_ang: float = -40.0,
    sword_len: float = 16.0,
    slash: int = 0,
    bob: float = 0.0,
    squash: float = 1.0,
    sword_behind: bool = False,
) -> Canvas:
    c = Canvas.blank(SIZE, SIZE)
    cx = 22.0 + lean
    gy = GROUND
    head_y = 15.0 + bob
    hip_y = 31.0 + bob + (1.0 - squash) * 2.0
    hx = cx + hand_x
    hy = head_y + 11 + hand_y

    # cape (behind)
    c.ellipse(cx - 3, hip_y - 4, 5.5, 9.0, CAPE)
    for y in range(int(hip_y - 2), int(gy - 4)):
        c.set(int(cx - 7), y, CAPE_D)

    if sword_behind:
        _sword(c, hx, hy, sword_ang, sword_len)

    # back leg
    bx = cx - 2 + back_foot
    c.rect(int(bx - 2), int(hip_y), int(bx + 2), int(gy - 5), PANTS)
    c.rect(int(bx - 3), int(gy - 5), int(bx + 3), int(gy - 1), BOOT)
    c.rect(int(bx - 2), int(gy - 5), int(bx + 3), int(gy - 4), BOOT_H)

    # torso
    c.rect(int(cx - 5), int(head_y + 7), int(cx + 5), int(hip_y + 1), TUNIC)
    c.rect(int(cx - 5), int(head_y + 7), int(cx - 4), int(hip_y + 1), TUNIC_D)
    c.rect(int(cx + 3), int(head_y + 7), int(cx + 5), int(head_y + 14), TUNIC_H)
    c.rect(int(cx - 4), int(hip_y), int(cx + 4), int(hip_y), GOLD)

    # front leg
    fx = cx + 2 + front_foot
    c.rect(int(fx - 2), int(hip_y), int(fx + 2), int(gy - 5), PANTS)
    c.rect(int(fx - 3), int(gy - 5), int(fx + 3), int(gy - 1), BOOT)
    c.rect(int(fx - 2), int(gy - 5), int(fx + 3), int(gy - 4), BOOT_H)

    # head + hair
    c.ellipse(cx + 0.5, head_y, 7.2, 7.4, SKIN)
    c.ellipse(cx - 0.5, head_y - 2.2, 7.8, 5.6, HAIR)
    c.ellipse(cx + 3.5, head_y - 4.2, 3.2, 2.4, HAIR_H)
    c.rect(int(cx - 7), int(head_y - 1), int(cx - 4), int(head_y + 5), HAIR)
    # face
    c.set(int(cx + 3), int(head_y), SKIN_D)
    c.ellipse(cx + 3.2, head_y + 0.4, 2.3, 2.5, WHITE)
    c.ellipse(cx + 3.8, head_y + 0.6, 1.15, 1.35, INK)
    c.set(int(cx + 3), int(head_y - 0.5), WHITE)
    c.set(int(cx + 4), int(head_y + 3), SKIN_D)

    # back arm
    c.stroke(cx - 3, head_y + 10, cx - 7, hip_y - 4, 1.45, SKIN)
    c.disc(cx - 7, hip_y - 4, 1.5, SKIN_D)

    # front arm + hand
    c.stroke(cx + 4, head_y + 10, hx, hy, 1.5, SKIN)
    c.disc(hx, hy, 1.8, SKIN)

    if not sword_behind:
        _sword(c, hx, hy, sword_ang, sword_len)
    if slash:
        _slash_arc(c, hx, hy, sword_ang, sword_len, 34 if slash == 1 else 50)

    c.outline(OUT)
    return c


def hero_idle() -> list[Canvas]:
    frames = []
    for i in range(4):
        t = i / 4 * 2 * math.pi
        frames.append(
            hero_pose(
                bob=math.sin(t) * 0.8,
                squash=1.0 + 0.03 * math.cos(t),
                hand_x=6.0,
                hand_y=-1.0 + math.sin(t) * 0.6,
                sword_ang=-48 + math.sin(t) * 4,
                sword_len=15.0,
                front_foot=2.0,
                back_foot=-2.0,
            )
        )
    return frames


def hero_attack() -> list[Canvas]:
    # Anticipation → raise → contact → follow-through → recover.
    keys = [
        dict(lean=-2.5, front_foot=0.0, back_foot=-1.5, hand_x=-3.0, hand_y=-9.0, sword_ang=-150, sword_len=15.0, slash=0, squash=0.92, sword_behind=True),
        dict(lean=-1.0, front_foot=1.5, back_foot=-2.0, hand_x=1.0, hand_y=-11.0, sword_ang=-105, sword_len=16.5, slash=0, squash=0.96, sword_behind=True),
        dict(lean=2.5, front_foot=5.0, back_foot=-3.0, hand_x=9.0, hand_y=-3.0, sword_ang=-18, sword_len=18.0, slash=1, squash=1.02),
        dict(lean=3.5, front_foot=6.0, back_foot=-2.0, hand_x=11.0, hand_y=3.0, sword_ang=22, sword_len=17.5, slash=2, squash=1.04),
        dict(lean=1.5, front_foot=3.5, back_foot=-1.0, hand_x=7.0, hand_y=6.0, sword_ang=58, sword_len=15.5, slash=0, squash=0.98),
        dict(lean=0.2, front_foot=2.0, back_foot=-2.0, hand_x=6.0, hand_y=0.0, sword_ang=-20, sword_len=15.0, slash=0, squash=1.0),
    ]
    return [hero_pose(**k) for k in keys]


HERO_PALETTE = [
    f"#{r:02x}{g:02x}{b:02x}"
    for r, g, b in (
        OUT, WHITE, INK, SKIN, SKIN_D, HAIR, HAIR_H,
        TUNIC, TUNIC_D, TUNIC_H, CAPE, CAPE_D, PANTS,
        BOOT, BOOT_H, STEEL, STEEL_M, STEEL_D, GOLD, GOLD_M, GOLD_D,
        SLASH, SLASH_H,
    )
]
