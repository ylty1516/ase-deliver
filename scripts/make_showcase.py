"""Build README / GitHub Pages images from real AseDeliver output."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SLIME = ROOT / "examples" / "slime"
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = (15, 17, 21, 255)
INK = (26, 29, 36, 255)
PANEL = (32, 36, 46, 255)
LINE = (58, 68, 102, 255)
TEXT = (232, 230, 227, 255)
MUTED = (139, 155, 180, 255)
CYAN = (109, 194, 202, 255)
GREEN = (99, 199, 77, 255)
ORANGE = (247, 118, 34, 255)
PINK = (181, 80, 136, 255)
WHITE = (255, 255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["segoeuib.ttf" if bold else "segoeui.ttf", "arialbd.ttf" if bold else "arial.ttf"]
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def mono(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("consola.ttf", "cascadiamono.ttf", "cour.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return font(size)


def checker(size: tuple[int, int], cell: int = 8) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", (w, h), (38, 42, 54, 255))
    draw = ImageDraw.Draw(im)
    a, b = (48, 52, 66, 255), (32, 35, 46, 255)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=a if ((x // cell + y // cell) % 2 == 0) else b)
    return im


def load_frames(tag: str) -> list[Image.Image]:
    frames = []
    for i in range(4):
        path = SLIME / "clean" / f"{tag}_{i:02d}.png"
        frames.append(Image.open(path).convert("RGBA"))
    return frames


def scale(im: Image.Image, factor: int) -> Image.Image:
    w, h = im.size
    return im.resize((w * factor, h * factor), Image.NEAREST)


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius: int, fill) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def paste_center(dst: Image.Image, src: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    dst.alpha_composite(src, (x - src.width // 2, y - src.height // 2))


def labeled_sheet() -> Image.Image:
    idle = load_frames("idle")
    walk = load_frames("walk")
    factor = 10
    pad = 28
    gap = 14
    label_h = 36
    cell = 16 * factor
    cols = 4
    rows = 2
    width = pad * 2 + cols * cell + (cols - 1) * gap
    height = 88 + rows * (cell + label_h + 18)
    canvas = Image.new("RGBA", (width, height), NAVY)
    draw = ImageDraw.Draw(canvas)
    title = font(28, True)
    small = font(16, True)
    draw.text((pad, 22), "AseDeliver  ·  slime.aseprite", font=title, fill=TEXT)
    draw.text((width - pad - 220, 28), "idle  +  walk   16×16", font=small, fill=CYAN)

    def row(frames: list[Image.Image], y: int, tag: str, color) -> None:
        draw.rounded_rectangle([pad - 8, y - 10, width - pad + 8, y + cell + label_h + 6], radius=16, fill=INK)
        draw.ellipse([pad, y + 8, pad + 12, y + 20], fill=color)
        draw.text((pad + 20, y + 4), tag, font=small, fill=color)
        for i, fr in enumerate(frames):
            x = pad + i * (cell + gap)
            bg = checker((cell, cell), cell=10)
            sprite = scale(fr, factor)
            bg.alpha_composite(sprite)
            canvas.alpha_composite(bg, (x, y + 28))
            draw.text((x + 6, y + 28 + cell + 4), f"{tag}_{i:02d}.png", font=mono(13), fill=MUTED)

    row(idle, 86, "idle", CYAN)
    row(walk, 86 + cell + label_h + 28, "walk", ORANGE)
    return canvas


def big_gif() -> None:
    idle = load_frames("idle")
    factor = 14
    frames = []
    for fr in idle:
        bg = checker((16 * factor + 48, 16 * factor + 48), cell=14)
        sprite = scale(fr, factor)
        x = (bg.width - sprite.width) // 2
        y = (bg.height - sprite.height) // 2
        bg.alpha_composite(sprite, (x, y))
        frames.append(bg.convert("P", palette=Image.ADAPTIVE, colors=64))
    frames[0].save(
        OUT / "slime-idle.gif",
        save_all=True,
        append_images=frames[1:],
        duration=140,
        loop=0,
        optimize=False,
    )
    walk = load_frames("walk")
    wframes = []
    for fr in walk:
        bg = checker((16 * factor + 48, 16 * factor + 48), cell=14)
        sprite = scale(fr, factor)
        x = (bg.width - sprite.width) // 2
        y = (bg.height - sprite.height) // 2
        bg.alpha_composite(sprite, (x, y))
        wframes.append(bg.convert("P", palette=Image.ADAPTIVE, colors=64))
    wframes[0].save(
        OUT / "slime-walk.gif",
        save_all=True,
        append_images=wframes[1:],
        duration=90,
        loop=0,
        optimize=False,
    )


def editor_mock() -> Image.Image:
    w, h = 1280, 720
    canvas = Image.new("RGBA", (w, h), (18, 20, 26, 255))
    draw = ImageDraw.Draw(canvas)
    rounded_rect(draw, [24, 18, w - 24, h - 18], 18, (22, 25, 32, 255))
    # title bar
    rounded_rect(draw, [24, 18, w - 24, 64], 18, (28, 32, 42, 255))
    draw.rectangle([24, 46, w - 24, 64], fill=(28, 32, 42, 255))
    for i, color in enumerate(((232, 81, 81), (232, 180, 72), (99, 199, 77))):
        draw.ellipse([44 + i * 22, 32, 58 + i * 22, 46], fill=color)
    draw.text((120, 28), "slime.aseprite  —  AseDeliver", font=font(18, True), fill=TEXT)
    draw.text((w - 280, 30), "Indexed  ·  16×16  ·  8 frames", font=font(14), fill=MUTED)

    # canvas area
    view = checker((640, 480), cell=20)
    slime = scale(load_frames("idle")[1], 22)
    vx = (640 - slime.width) // 2
    vy = (480 - slime.height) // 2 + 12
    view.alpha_composite(slime, (vx, vy))
    canvas.alpha_composite(view, (56, 88))
    draw.rectangle([56, 88, 56 + 640, 88 + 480], outline=LINE, width=1)

    # right tools
    rounded_rect(draw, [720, 88, w - 48, 300], 14, PANEL)
    draw.text((744, 108), "Layers", font=font(16, True), fill=MUTED)
    rounded_rect(draw, [744, 140, w - 72, 188], 10, (45, 52, 70, 255))
    draw.rectangle([744, 140, 752, 188], fill=CYAN)
    draw.text((768, 154), "sprite", font=font(18, True), fill=TEXT)
    draw.text((w - 168, 156), "255", font=mono(14), fill=MUTED)

    draw.text((744, 214), "Palette  ·  endesga-32", font=font(16, True), fill=MUTED)
    pal = [
        (99, 199, 77),
        (62, 137, 72),
        (38, 92, 66),
        (25, 60, 62),
        (167, 240, 112),
        (24, 20, 37),
        (255, 255, 255),
        (192, 203, 220),
        (247, 118, 34),
        (254, 231, 97),
        (109, 194, 202),
        (181, 80, 136),
    ]
    for i, c in enumerate(pal):
        x = 744 + (i % 8) * 28
        y = 246 + (i // 8) * 28
        draw.rounded_rectangle([x, y, x + 22, y + 22], radius=4, fill=c)

    rounded_rect(draw, [720, 320, w - 48, 568], 14, PANEL)
    draw.text((744, 340), "Tags", font=font(16, True), fill=MUTED)
    rounded_rect(draw, [744, 376, w - 72, 430], 10, (36, 72, 78, 255))
    draw.text((760, 392), "idle    frames 0–3    140ms", font=mono(15), fill=CYAN)
    rounded_rect(draw, [744, 446, w - 72, 500], 10, (78, 46, 28, 255))
    draw.text((760, 462), "walk    frames 4–7     90ms", font=mono(15), fill=ORANGE)
    draw.text((744, 524), "Deliverable  OK  .aseprite + sheet + gif + json", font=font(14), fill=GREEN)

    # timeline
    rounded_rect(draw, [56, 588, w - 48, 686], 14, PANEL)
    draw.text((76, 604), "Timeline", font=font(14, True), fill=MUTED)
    for i in range(8):
        x = 76 + i * 88
        fill = (36, 72, 78, 255) if i < 4 else (78, 46, 28, 255)
        rounded_rect(draw, [x, 632, x + 76, 668], 8, fill)
        thumb = scale((load_frames("idle") if i < 4 else load_frames("walk"))[i % 4], 2)
        canvas.alpha_composite(thumb, (x + 6, 636))
        draw.text((x + 42, 640), str(i), font=mono(12), fill=WHITE)
    return canvas


def pipeline() -> Image.Image:
    w, h = 1280, 360
    canvas = Image.new("RGBA", (w, h), NAVY)
    draw = ImageDraw.Draw(canvas)
    steps = [
        ("01", "Spec", "JSON template\ncanvas · tags · palette", CYAN),
        ("02", "Pixels", "Any model, or ASCII\ninto raw/", GREEN),
        ("03", "Compile", "Real .aseprite\nlayers · frames · tags", ORANGE),
        ("04", "Deliver", "Sheet + GIF + JSON\nopen in Aseprite", PINK),
    ]
    card_w = 270
    gap = 28
    left = (w - (card_w * 4 + gap * 3)) // 2
    for i, (num, title, body, color) in enumerate(steps):
        x = left + i * (card_w + gap)
        rounded_rect(draw, [x, 40, x + card_w, 310], 18, INK)
        draw.rounded_rectangle([x, 40, x + 8, 310], radius=4, fill=color)
        draw.text((x + 28, 64), num, font=mono(18), fill=color)
        draw.text((x + 28, 102), title, font=font(32, True), fill=TEXT)
        draw.multiline_text((x + 28, 160), body, font=font(18), fill=MUTED, spacing=8)
        if i < 3:
            ax = x + card_w + 4
            draw.polygon([(ax, 170), (ax + 16, 180), (ax, 190)], fill=LINE)
    return canvas


def hero(bg_path: Path | None) -> Image.Image:
    w, h = 1600, 840
    canvas = Image.new("RGBA", (w, h), NAVY)
    if bg_path and bg_path.is_file():
        bg = Image.open(bg_path).convert("RGBA")
        bg = bg.resize((w, h), Image.NEAREST)
        bg = bg.filter(ImageFilter.GaussianBlur(0.2))
        # darken so type stays readable
        overlay = Image.new("RGBA", (w, h), (10, 12, 18, 150))
        canvas.alpha_composite(bg)
        canvas.alpha_composite(overlay)
    draw = ImageDraw.Draw(canvas)
    # left copy
    draw.text((80, 150), "AseDeliver", font=font(72, True), fill=WHITE)
    draw.multiline_text(
        (80, 250),
        "Any AI → production Aseprite\ngame art you can actually ship.",
        font=font(34),
        fill=TEXT,
        spacing=10,
    )
    draw.rounded_rectangle([80, 390, 430, 448], radius=12, fill=CYAN)
    draw.text((108, 404), "spec  →  .aseprite  →  engine", font=font(18, True), fill=(15, 17, 21, 255))
    draw.text((80, 480), "CLI  ·  MCP  ·  ASCII pixels  ·  Godot / Phaser / Unity", font=font(18), fill=MUTED)

    # giant slime
    slime = scale(load_frames("idle")[1], 28)
    shadow = Image.new("RGBA", (slime.width, 36), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.ellipse([20, 0, slime.width - 20, 34], fill=(0, 0, 0, 90))
    canvas.alpha_composite(shadow, (980, 620))
    canvas.alpha_composite(slime, (980, 180))
    return canvas


def og_card() -> Image.Image:
    w, h = 1280, 640
    canvas = Image.new("RGBA", (w, h), NAVY)
    draw = ImageDraw.Draw(canvas)
    # pixel grid
    for x in range(0, w, 16):
        draw.line([x, 0, x, h], fill=(32, 36, 48, 255))
    for y in range(0, h, 16):
        draw.line([0, y, w, y], fill=(32, 36, 48, 255))
    rounded_rect(draw, [48, 48, w - 48, h - 48], 28, INK)
    slime = scale(load_frames("idle")[2], 18)
    canvas.alpha_composite(slime, (70, 120))
    draw.text((420, 150), "AseDeliver", font=font(64, True), fill=WHITE)
    draw.multiline_text(
        (420, 240),
        "The missing compiler between\nany AI image and a real\n.aseprite game asset.",
        font=font(28),
        fill=MUTED,
        spacing=8,
    )
    draw.rounded_rectangle([420, 430, 820, 492], radius=12, fill=GREEN)
    draw.text((448, 446), "open in Aseprite  ·  ship to engine", font=font(18, True), fill=NAVY)
    return canvas


def gallery_strip() -> Image.Image:
    idle = load_frames("idle")
    walk = load_frames("walk")
    factor = 8
    frames = idle + walk
    cell = 16 * factor
    pad = 20
    canvas = Image.new("RGBA", (pad * 2 + len(frames) * (cell + 12) - 12, cell + pad * 2), NAVY)
    for i, fr in enumerate(frames):
        bg = checker((cell, cell), 8)
        bg.alpha_composite(scale(fr, factor))
        canvas.alpha_composite(bg, (pad + i * (cell + 12), pad))
    return canvas


def extra_items() -> Image.Image:
    from ase_deliver.images import rasterize_pixels

    potion = {
        "map": {".": None, "w": "#ffffff", "g": "#8b9bb4", "r": "#e43b44", "h": "#f6757a", "d": "#a22633", "n": "#181425"},
        "rows": [
            "................",
            "......wwww......",
            "......wggw......",
            ".......ww.......",
            "......nnnn......",
            ".....nrrrrn.....",
            "....nrrhrrrn....",
            "....nrrrrrrn....",
            "....nrrrrrrn....",
            ".....ndrrdn.....",
            "......nnnn......",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }
    coin = {
        "map": {".": None, "y": "#fee761", "o": "#feae34", "d": "#f77622", "w": "#ffffff"},
        "rows": [
            "................",
            "................",
            "......oooo......",
            "....ooyyyyoo....",
            "...oyywyyyyo....",
            "...oyyyyyyyo....",
            "...oyyyddyyo....",
            "...oyyyyyyyo....",
            "....ooyyyyoo....",
            "......oooo......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }
    chest = {
        "map": {".": None, "w": "#ead4aa", "o": "#d77643", "d": "#733e39", "y": "#fee761", "n": "#181425"},
        "rows": [
            "................",
            "................",
            "................",
            "....dddddddd....",
            "...dwwwwwwwd....",
            "...dwwwwwwwd....",
            "...doooooood....",
            "...dooynyyod....",
            "...doooooood....",
            "...dnnnnnnnd....",
            "....dddddddd....",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }
    sword = {
        "map": {".": None, "s": "#c0cbdc", "h": "#ffffff", "o": "#b86f50", "d": "#733e39", "y": "#fee761"},
        "rows": [
            "............hh..",
            "...........hss..",
            "..........hss...",
            ".........hss....",
            "........hss.....",
            ".......hss......",
            "....y.hss.......",
            "....yyoo........",
            ".....dd.........",
            ".....dd.........",
            ".....d..........",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }
    items = [("potion", potion), ("coin", coin), ("chest", chest), ("sword", sword)]
    factor = 10
    cell = 16 * factor
    pad = 24
    canvas = Image.new("RGBA", (pad * 2 + 4 * (cell + 36) - 36, cell + 90), NAVY)
    draw = ImageDraw.Draw(canvas)
    for i, (name, payload) in enumerate(items):
        im = rasterize_pixels(payload)
        bg = checker((cell, cell), 10)
        bg.alpha_composite(scale(im, factor))
        x = pad + i * (cell + 36)
        canvas.alpha_composite(bg, (x, 18))
        draw.text((x + 8, cell + 28), name, font=font(18, True), fill=TEXT)
    return canvas


def main() -> None:
    labeled_sheet().save(OUT / "slime-sheet.png")
    big_gif()
    editor_mock().save(OUT / "aseprite-mock.png")
    pipeline().save(OUT / "pipeline.png")
    gallery_strip().save(OUT / "slime-strip.png")
    extra_items().save(OUT / "props.png")
    og_card().save(OUT / "og.png")
    scale(load_frames("idle")[1], 4).save(OUT / "favicon.png")

    candidates = (
        list((ROOT / "docs" / "assets").glob("mood.*"))
        + list(Path.cwd().glob("images/*"))
    )
    hero_im = hero(candidates[0] if candidates else None)
    hero_im.save(OUT / "hero.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
