from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .ops import (
    build_project,
    compile_project,
    demo_project,
    doctor,
    export_project,
    generation_brief,
    ingest_project,
    init_project,
    list_templates,
    open_in_aseprite,
    paint_cel,
    project_status,
    validate_project,
)
from .spec import SpecError
from .util import load_json


def _print(data: Any, as_json: bool) -> None:
    if as_json:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return
    if isinstance(data, dict) and "markdown" in data and "prompt" in data:
        sys.stdout.write(data["markdown"])
        return
    if isinstance(data, dict):
        ok = data.get("ok")
        if ok is False:
            err = data.get("error") or data.get("missing") or "failed"
            sys.stderr.write(f"ERROR: {err}\n")
        for key, value in data.items():
            if key in {"markdown"}:
                continue
            if isinstance(value, (dict, list)):
                pretty = json.dumps(value, ensure_ascii=False, indent=2)
                sys.stdout.write(f"{key}:\n{pretty}\n")
            else:
                sys.stdout.write(f"{key}: {value}\n")
        return
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _project_arg(ns: argparse.Namespace) -> Path:
    return Path(getattr(ns, "project", None) or ".").expanduser().resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ase-deliver",
        description="Compile production-ready Aseprite game art from a spec any AI can write.",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--version", action="version", version=f"ase-deliver {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Check Python, Pillow, Aseprite")
    t = sub.add_parser("templates", help="List starter templates")
    t.add_argument("--json", action="store_true")

    p = sub.add_parser("init", help="Create a new asset project")
    p.add_argument("name")
    p.add_argument("--template", default="character-platformer")
    p.add_argument("--out", default=None, help="Directory (default: ./<name>)")
    p.add_argument("--desc", default="", help="Subject description used in image prompts")

    for name, help_text in [
        ("brief", "Write BRIEF.md and print prompts for any image model"),
        ("status", "Which source files are present / missing"),
        ("ingest", "Key background, fit to canvas, quantize into clean/"),
        ("compile", "Write out/<name>.aseprite"),
        ("export", "Write sprite sheet, GIF, JSON"),
        ("validate", "Deliverable checklist"),
        ("build", "ingest + compile + export + validate"),
        ("open", "Open the .aseprite file in Aseprite"),
    ]:
        sp = sub.add_parser(name, help=help_text)
        sp.add_argument("project", nargs="?", default=".")

    d = sub.add_parser("demo", help="Build a built-in slime and optionally open Aseprite")
    d.add_argument("--out", default="examples/slime")
    d.add_argument("--open", action="store_true")

    paint = sub.add_parser("paint", help="Write a cel from ASCII/JSON pixel payload")
    paint.add_argument("project")
    paint.add_argument("--tag", required=True)
    paint.add_argument("--frame", type=int, default=0)
    paint.add_argument("--layer", default=None)
    paint.add_argument("--file", default=None, help="JSON file; default stdin")

    mcp = sub.add_parser("mcp", help="Run the MCP server on stdio (for any MCP-capable AI)")
    mcp.add_argument("--debug", action="store_true")

    args = parser.parse_args(argv)
    as_json = bool(getattr(args, "json", False))

    try:
        if args.cmd == "mcp":
            from .mcp_server import run_mcp

            run_mcp()
            return 0
        if args.cmd == "doctor":
            data = doctor()
            _print(data, as_json)
            return 0 if data.get("ok") else 1
        if args.cmd == "templates":
            data = {"ok": True, "templates": list_templates()}
            if as_json:
                _print(data, True)
            else:
                for item in data["templates"]:
                    canvas = item["canvas"]
                    tags = ", ".join(item["tags"])
                    print(f"{item['id']:24} {canvas['width']}x{canvas['height']}  {item['kind']:10}  {tags}")
            return 0
        if args.cmd == "init":
            dest = Path(args.out) if args.out else Path.cwd() / args.name
            data = init_project(dest, args.template, name=args.name, description=args.desc)
            _print(data, as_json)
            return 0
        if args.cmd == "demo":
            data = demo_project(args.out, open_file=args.open)
            _print(data, as_json)
            return 0 if data.get("ok") else 1
        if args.cmd == "paint":
            payload = load_json(Path(args.file)) if args.file else json.load(sys.stdin)
            data = paint_cel(_project_arg(args), payload, tag=args.tag, frame=args.frame, layer=args.layer)
            _print(data, as_json)
            return 0

        project = _project_arg(args)
        if args.cmd == "brief":
            data = generation_brief(project)
        elif args.cmd == "status":
            data = project_status(project)
        elif args.cmd == "ingest":
            data = ingest_project(project)
        elif args.cmd == "compile":
            data = compile_project(project)
        elif args.cmd == "export":
            data = export_project(project)
        elif args.cmd == "validate":
            data = validate_project(project)
        elif args.cmd == "build":
            data = build_project(project)
        elif args.cmd == "open":
            data = open_in_aseprite(project)
        else:
            parser.error(f"unknown command {args.cmd}")
            return 2
        _print(data, as_json)
        return 0 if data.get("ok", True) else 1
    except (SpecError, KeyError, FileNotFoundError, ValueError) as exc:
        payload = {"ok": False, "error": str(exc)}
        _print(payload, as_json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
