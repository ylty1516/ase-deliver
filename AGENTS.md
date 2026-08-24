# AseDeliver — contract for any AI

You are producing **shippable Aseprite game art**, not a pretty PNG.

Source of truth is always `out/<name>.aseprite`.
A PNG/GIF without that file is not done.

## What this tool is

`ase-deliver` turns a JSON spec + frame images (or ASCII pixels) into:

- `.aseprite` with layers, frames, tags, palette, pivot/slices
- sprite sheet PNG
- GIF preview
- engine JSON (`frames` + `meta.frameTags`)

It does **not** replace your image model. You generate pixels however you can. This compiler makes them deliverable in Aseprite.

## Do this, in order

1. `doctor` — confirm Pillow; Aseprite is optional for compile, required to open the file.
2. `init` a project from a template. Fill `description` with the subject.
3. `brief` — follow the returned prompt and **exact filenames**.
4. Put one image per required name in `raw/`. Magenta `#FF00FF` background. Isolated subject. Integer scale of the canvas is OK.
5. `build` (ingest + compile + export + validate).
6. Only report done if `validate.deliverable` is true.
7. `open` in Aseprite if the user wants to see it.

CLI (Windows):

```
C:\Users\yyx\ase-deliver\ase-deliver.bat doctor
C:\Users\yyx\ase-deliver\ase-deliver.bat templates
C:\Users\yyx\ase-deliver\ase-deliver.bat init hero --template character-platformer --out D:\game\art\hero --desc "orange fox knight, facing right"
C:\Users\yyx\ase-deliver\ase-deliver.bat brief D:\game\art\hero
C:\Users\yyx\ase-deliver\ase-deliver.bat build D:\game\art\hero
C:\Users\yyx\ase-deliver\ase-deliver.bat open D:\game\art\hero
```

Python module:

```
python -m ase_deliver <command>
```

Set `PYTHONPATH=C:\Users\yyx\ase-deliver` if you are not cwd'd there.

## Templates

| id | canvas | tags |
|---|---|---|
| character-platformer | 32x32 | idle, walk, jump |
| character-topdown | 16x16 | idle-down, walk-down/left/right/up |
| character-turnaround | 64x64 | front, three-quarter, side, back |
| portrait | 80x80 | bust |
| prop | 32x32 | idle |
| tileset-16 | 16x16 | grass, dirt, stone, water |
| ui-button | 48x16 | normal, hover, pressed |
| fx | 32x32 | burst |

Pick the template that matches the asset **shape**. Do not dump a walk cycle into `portrait`.

## Hard visual rules

- Isolated subject, no ground, no baked drop shadow, no scenery, no watermark, no text.
- Background exactly `#FF00FF` (or already transparent).
- Same character in every frame: proportions, colors, pivot. Standing poses: feet on the bottom pixel row.
- Crisp pixels, no anti-aliasing.
- Indexed palette from the spec (default `endesga-32`).
- Animation tags must loop when they are cycles (`idle`, `walk`).
- Never invent filenames. Use the brief list.

## If you cannot generate images

Use `paint` / `paint_cel` with an ASCII map:

```json
{
  "map": { ".": null, "#": "#63c74d", "e": "#181425" },
  "rows": ["....", ".##.", ".ee.", "...."]
}
```

That is a valid source. Text-only models can still deliver tiny sprites.

## Do not

- Deliver only a midjourney/chatgpt PNG.
- Use Photoshop-style layers as the ship format.
- Change canvas size silently.
- Put multiple poses in one file unless the spec is a sprite sheet (`sheet` field).
- Claim success when `validate` reports missing files or a missing `.aseprite`.

## MCP

If the host has the `ase-deliver` MCP server, call those tools instead of shelling out. Same order: `init_project` → `generation_brief` → (write `raw/`) → `build` → `validate_sprite` → `open_in_aseprite`.
