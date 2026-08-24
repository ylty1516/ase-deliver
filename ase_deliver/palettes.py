from __future__ import annotations

from typing import Sequence

from .util import parse_hex, to_hex

RGB = tuple[int, int, int]


def _hex_list(colors: Sequence[str]) -> list[RGB]:
    out: list[RGB] = []
    for c in colors:
        r, g, b, _a = parse_hex(c)
        out.append((r, g, b))
    return out


PALETTES: dict[str, list[RGB]] = {
    "pico-8": _hex_list(
        [
            "#000000",
            "#1d2b53",
            "#7e2553",
            "#008751",
            "#ab5236",
            "#5f574f",
            "#c2c3c7",
            "#fff1e8",
            "#ff004d",
            "#ffa300",
            "#ffec27",
            "#00e436",
            "#29adff",
            "#83769c",
            "#ff77a8",
            "#ffccaa",
        ]
    ),
    "sweetie-16": _hex_list(
        [
            "#1a1c2c",
            "#5d275d",
            "#b13e53",
            "#ef7d57",
            "#ffcd75",
            "#a7f070",
            "#38b764",
            "#257179",
            "#29366f",
            "#3b5dc9",
            "#41a6f6",
            "#73eff7",
            "#f4f4f4",
            "#94b0c2",
            "#566c86",
            "#333c57",
        ]
    ),
    "db16": _hex_list(
        [
            "#140c1c",
            "#442434",
            "#30346d",
            "#4e4a4e",
            "#854c30",
            "#346524",
            "#d04648",
            "#757161",
            "#597dce",
            "#d27d2c",
            "#8595a1",
            "#6daa2c",
            "#d2aa99",
            "#6dc2ca",
            "#dad45e",
            "#deeed6",
        ]
    ),
    "arne-16": _hex_list(
        [
            "#000000",
            "#9d9d9d",
            "#ffffff",
            "#be2633",
            "#e06f8b",
            "#493c2b",
            "#a46422",
            "#eb8931",
            "#f7e26b",
            "#2f484e",
            "#44891a",
            "#a3ce27",
            "#1b2632",
            "#005784",
            "#31a2f2",
            "#b2dcef",
        ]
    ),
    "gameboy": _hex_list(["#0f380f", "#306230", "#8bac0f", "#9bbc0f"]),
    "endesga-32": _hex_list(
        [
            "#be4a2f",
            "#d77643",
            "#ead4aa",
            "#e4a672",
            "#b86f50",
            "#733e39",
            "#3e2731",
            "#a22633",
            "#e43b44",
            "#f77622",
            "#feae34",
            "#fee761",
            "#63c74d",
            "#3e8948",
            "#265c42",
            "#193c3e",
            "#124e89",
            "#0099db",
            "#2ce8f5",
            "#ffffff",
            "#c0cbdc",
            "#8b9bb4",
            "#5a6988",
            "#3a4466",
            "#262b44",
            "#181425",
            "#ff0044",
            "#68386c",
            "#b55088",
            "#f6757a",
            "#e8b796",
            "#c28569",
        ]
    ),
}


def list_palettes() -> list[str]:
    return sorted(PALETTES)


def resolve_palette(value: str | Sequence[str] | None) -> list[RGB]:
    if value is None:
        return list(PALETTES["endesga-32"])
    if isinstance(value, str):
        key = value.strip().lower()
        if key not in PALETTES:
            known = ", ".join(list_palettes())
            raise ValueError(f"Unknown palette {value!r}. Built-ins: {known}")
        return list(PALETTES[key])
    colors: list[RGB] = []
    for item in value:
        r, g, b, _a = parse_hex(str(item))
        colors.append((r, g, b))
    if not colors:
        raise ValueError("Palette list is empty")
    return colors


def palette_hexes(palette: Sequence[RGB]) -> list[str]:
    return [to_hex(c) for c in palette]


def nearest_index(rgb: Sequence[int], palette: Sequence[RGB], skip: set[int] | None = None) -> int:
    best_i = 0
    best_d = 10**18
    skip = skip or set()
    for i, swatch in enumerate(palette):
        if i in skip:
            continue
        d = (int(rgb[0]) - swatch[0]) ** 2 + (int(rgb[1]) - swatch[1]) ** 2 + (int(rgb[2]) - swatch[2]) ** 2
        if d < best_d:
            best_d = d
            best_i = i
    return best_i
