from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from PIL import Image

from .palettes import nearest_index

ASE_MAGIC = 0xA5E0
FRAME_MAGIC = 0xF1FA
CHUNK_OLD_PALETTE = 0x0004
CHUNK_LAYER = 0x2004
CHUNK_CEL = 0x2005
CHUNK_COLOR_PROFILE = 0x2007
CHUNK_TAGS = 0x2018
CHUNK_PALETTE = 0x2019
CHUNK_SLICE = 0x2022


class AseError(ValueError):
    pass


def _u8(buf: bytearray, v: int) -> None:
    buf.append(v & 0xFF)


def _u16(buf: bytearray, v: int) -> None:
    buf.extend(struct.pack("<H", v & 0xFFFF))


def _i16(buf: bytearray, v: int) -> None:
    buf.extend(struct.pack("<h", v))


def _u32(buf: bytearray, v: int) -> None:
    buf.extend(struct.pack("<I", v & 0xFFFFFFFF))


def _i32(buf: bytearray, v: int) -> None:
    buf.extend(struct.pack("<i", v))


def _str(buf: bytearray, text: str) -> None:
    encoded = text.encode("utf-8")
    _u16(buf, len(encoded))
    buf.extend(encoded)


def _chunk(chunk_type: int, payload: bytes) -> bytes:
    return struct.pack("<IH", 6 + len(payload), chunk_type) + payload


@dataclass
class AseLayer:
    name: str
    opacity: int = 255
    blend: int = 0
    visible: bool = True
    editable: bool = True


@dataclass
class AseTag:
    name: str
    from_frame: int
    to_frame: int
    direction: int = 0
    repeat: int = 0
    color: tuple[int, int, int] = (0x6D, 0xC2, 0xCA)


@dataclass
class AseSlice:
    name: str
    x: int
    y: int
    width: int
    height: int
    pivot: tuple[int, int] | None = None
    nine_patch: tuple[int, int, int, int] | None = None


@dataclass
class AseCel:
    layer: int
    image: Image.Image
    x: int = 0
    y: int = 0
    opacity: int = 255


@dataclass
class AseFrame:
    duration: int = 100
    cels: list[AseCel] = field(default_factory=list)


@dataclass
class AseSprite:
    width: int
    height: int
    color_mode: str
    layers: list[AseLayer]
    frames: list[AseFrame]
    palette: list[tuple[int, int, int]] = field(default_factory=list)
    tags: list[AseTag] = field(default_factory=list)
    slices: list[AseSlice] = field(default_factory=list)
    grid: tuple[int, int, int, int] = (0, 0, 16, 16)
    transparent_index: int = 0


def _trim_rgba(im: Image.Image) -> tuple[Image.Image, int, int]:
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 0, 0
    cropped = im.crop(bbox)
    return cropped, bbox[0], bbox[1]


def _rgba_bytes(im: Image.Image) -> bytes:
    return im.convert("RGBA").tobytes()


def _indexed_bytes(im: Image.Image, palette: Sequence[tuple[int, int, int]], transparent_index: int) -> bytes:
    im = im.convert("RGBA")
    w, h = im.size
    pix = im.load()
    skip = {transparent_index} if 0 <= transparent_index < len(palette) else set()
    out = bytearray(w * h)
    i = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a < 16:
                out[i] = transparent_index
            else:
                out[i] = nearest_index((r, g, b), palette, skip=skip)
            i += 1
    return bytes(out)


def _layer_chunk(layer: AseLayer) -> bytes:
    payload = bytearray()
    flags = 0
    if layer.visible:
        flags |= 1
    if layer.editable:
        flags |= 2
    _u16(payload, flags)
    _u16(payload, 0)  # image layer
    _u16(payload, 0)  # child level
    _u16(payload, 0)
    _u16(payload, 0)
    _u16(payload, layer.blend)
    _u8(payload, layer.opacity)
    payload.extend(b"\x00\x00\x00")
    _str(payload, layer.name)
    return _chunk(CHUNK_LAYER, bytes(payload))


def _color_profile_chunk() -> bytes:
    payload = bytearray()
    _u16(payload, 1)  # sRGB
    _u16(payload, 0)
    _u32(payload, 0)  # fixed gamma
    payload.extend(b"\x00" * 8)
    return _chunk(CHUNK_COLOR_PROFILE, bytes(payload))


def _palette_chunk(palette: Sequence[tuple[int, int, int]]) -> bytes:
    payload = bytearray()
    n = len(palette)
    _u32(payload, n)
    _u32(payload, 0)
    _u32(payload, n - 1 if n else 0)
    payload.extend(b"\x00" * 8)
    for r, g, b in palette:
        _u16(payload, 0)
        _u8(payload, r)
        _u8(payload, g)
        _u8(payload, b)
        _u8(payload, 255)
    return _chunk(CHUNK_PALETTE, bytes(payload))


def _old_palette_chunk(palette: Sequence[tuple[int, int, int]]) -> bytes:
    n = min(len(palette), 256)
    payload = bytearray()
    _u16(payload, 1)
    _u8(payload, 0)
    _u8(payload, 0 if n == 256 else n)
    for i in range(n):
        r, g, b = palette[i]
        _u8(payload, r)
        _u8(payload, g)
        _u8(payload, b)
    return _chunk(CHUNK_OLD_PALETTE, bytes(payload))


def _cel_chunk(cel: AseCel, color_mode: str, palette: Sequence[tuple[int, int, int]], transparent_index: int) -> bytes:
    trimmed, ox, oy = _trim_rgba(cel.image)
    w, h = trimmed.size
    if color_mode == "indexed":
        raw = _indexed_bytes(trimmed, palette, transparent_index)
    else:
        raw = _rgba_bytes(trimmed)
    compressed = zlib.compress(raw, 9)
    payload = bytearray()
    _u16(payload, cel.layer)
    _i16(payload, cel.x + ox)
    _i16(payload, cel.y + oy)
    _u8(payload, cel.opacity)
    _u16(payload, 2)  # compressed image
    _i16(payload, 0)
    payload.extend(b"\x00" * 5)
    _u16(payload, w)
    _u16(payload, h)
    payload.extend(compressed)
    return _chunk(CHUNK_CEL, bytes(payload))


def _tags_chunk(tags: Sequence[AseTag]) -> bytes:
    payload = bytearray()
    _u16(payload, len(tags))
    payload.extend(b"\x00" * 8)
    for tag in tags:
        _u16(payload, tag.from_frame)
        _u16(payload, tag.to_frame)
        _u8(payload, tag.direction)
        _u16(payload, tag.repeat)
        payload.extend(b"\x00" * 6)
        _u8(payload, tag.color[0])
        _u8(payload, tag.color[1])
        _u8(payload, tag.color[2])
        _u8(payload, 0)
        _str(payload, tag.name)
    return _chunk(CHUNK_TAGS, bytes(payload))


def _slice_chunk(sl: AseSlice) -> bytes:
    flags = 0
    if sl.nine_patch:
        flags |= 1
    if sl.pivot:
        flags |= 2
    payload = bytearray()
    _u32(payload, 1)
    _u32(payload, flags)
    _u32(payload, 0)
    _str(payload, sl.name)
    _u32(payload, 0)
    _i32(payload, sl.x)
    _i32(payload, sl.y)
    _u32(payload, sl.width)
    _u32(payload, sl.height)
    if sl.nine_patch:
        cx, cy, cw, ch = sl.nine_patch
        _i32(payload, cx)
        _i32(payload, cy)
        _u32(payload, cw)
        _u32(payload, ch)
    if sl.pivot:
        _i32(payload, sl.pivot[0])
        _i32(payload, sl.pivot[1])
    return _chunk(CHUNK_SLICE, bytes(payload))


def write_aseprite(path: Path, sprite: AseSprite) -> Path:
    if sprite.color_mode not in {"rgba", "indexed"}:
        raise AseError(f"Unsupported color mode {sprite.color_mode}")
    if sprite.color_mode == "indexed" and not sprite.palette:
        raise AseError("Indexed sprites need a palette")
    depth = 32 if sprite.color_mode == "rgba" else 8
    ncolors = len(sprite.palette) if sprite.palette else 0

    first_chunks: list[bytes] = [_color_profile_chunk()]
    if sprite.palette:
        first_chunks.append(_palette_chunk(sprite.palette))
        if len(sprite.palette) <= 256:
            first_chunks.append(_old_palette_chunk(sprite.palette))
    for layer in sprite.layers:
        first_chunks.append(_layer_chunk(layer))
    if sprite.tags:
        first_chunks.append(_tags_chunk(sprite.tags))
    for sl in sprite.slices:
        first_chunks.append(_slice_chunk(sl))

    frame_blobs: list[bytes] = []
    for index, frame in enumerate(sprite.frames):
        chunks = list(first_chunks) if index == 0 else []
        for cel in frame.cels:
            chunks.append(_cel_chunk(cel, sprite.color_mode, sprite.palette, sprite.transparent_index))
        body = b"".join(chunks)
        n = len(chunks)
        old = n if n < 0xFFFF else 0xFFFF
        header = struct.pack("<IHHH", 16 + len(body), FRAME_MAGIC, old, int(frame.duration))
        header += b"\x00\x00"
        header += struct.pack("<I", n)
        frame_blobs.append(header + body)

    file_size = 128 + sum(len(b) for b in frame_blobs)
    header = bytearray(128)
    struct.pack_into("<I", header, 0, file_size)
    struct.pack_into("<H", header, 4, ASE_MAGIC)
    struct.pack_into("<H", header, 6, len(sprite.frames))
    struct.pack_into("<H", header, 8, sprite.width)
    struct.pack_into("<H", header, 10, sprite.height)
    struct.pack_into("<H", header, 12, depth)
    struct.pack_into("<I", header, 14, 1)  # layer opacity valid
    struct.pack_into("<H", header, 18, sprite.frames[0].duration if sprite.frames else 100)
    header[28] = sprite.transparent_index
    struct.pack_into("<H", header, 32, ncolors)
    header[34] = 1
    header[35] = 1
    gx, gy, gw, gh = sprite.grid
    struct.pack_into("<h", header, 36, gx)
    struct.pack_into("<h", header, 38, gy)
    struct.pack_into("<H", header, 40, gw)
    struct.pack_into("<H", header, 42, gh)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(header)
        for blob in frame_blobs:
            fh.write(blob)
    return path


@dataclass
class AseInfo:
    path: Path
    file_size: int
    frames: int
    width: int
    height: int
    depth: int
    ncolors: int
    tags: list[str]
    layers: list[str]


def read_ase_info(path: Path) -> AseInfo:
    data = Path(path).read_bytes()
    if len(data) < 128:
        raise AseError(f"{path} is too small to be an Aseprite file")
    magic = struct.unpack_from("<H", data, 4)[0]
    if magic != ASE_MAGIC:
        raise AseError(f"{path} is not an Aseprite file (magic={magic:#x})")
    frames, width, height, depth = struct.unpack_from("<HHHH", data, 6)
    ncolors = struct.unpack_from("<H", data, 32)[0]
    tags: list[str] = []
    layers: list[str] = []
    offset = 128
    for _ in range(frames):
        if offset + 16 > len(data):
            break
        frame_size, frame_magic, old_n, _dur = struct.unpack_from("<IHHH", data, offset)
        new_n = struct.unpack_from("<I", data, offset + 12)[0]
        nchunks = new_n or old_n
        pos = offset + 16
        for _c in range(nchunks):
            if pos + 6 > len(data):
                break
            csize, ctype = struct.unpack_from("<IH", data, pos)
            payload = data[pos + 6 : pos + csize]
            if ctype == CHUNK_LAYER:
                name_len = struct.unpack_from("<H", payload, 16)[0]
                name = payload[18 : 18 + name_len].decode("utf-8", errors="replace")
                layers.append(name)
            elif ctype == CHUNK_TAGS:
                ntags = struct.unpack_from("<H", payload, 0)[0]
                p = 10
                for _t in range(ntags):
                    p += 2 + 2 + 1 + 2 + 6 + 3 + 1
                    nlen = struct.unpack_from("<H", payload, p)[0]
                    p += 2
                    tags.append(payload[p : p + nlen].decode("utf-8", errors="replace"))
                    p += nlen
            pos += csize
        offset += frame_size
    return AseInfo(
        path=Path(path),
        file_size=len(data),
        frames=frames,
        width=width,
        height=height,
        depth=depth,
        ncolors=ncolors,
        tags=tags,
        layers=layers,
    )
