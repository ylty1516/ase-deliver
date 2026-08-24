from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

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

PROTOCOL = "2024-11-05"


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": True,
        },
    }


TOOLS = [
    _tool("doctor", "Check that AseDeliver, Pillow, and Aseprite are available.", {}),
    _tool("list_templates", "List asset templates (platformer, turnaround, tileset, UI, FX, portrait).", {}),
    _tool(
        "init_project",
        "Create a new Aseprite asset project from a template. Returns required filenames and the image-model prompt.",
        {
            "dest": {"type": "string", "description": "Output directory"},
            "template": {"type": "string", "description": "Template id from list_templates"},
            "name": {"type": "string"},
            "description": {"type": "string", "description": "What the sprite is, used in generation prompts"},
        },
        ["dest", "template"],
    ),
    _tool(
        "generation_brief",
        "Return the exact prompt, palette, and filenames any image model must produce for this project.",
        {"project": {"type": "string", "description": "Project directory"}},
        ["project"],
    ),
    _tool(
        "project_status",
        "List which source frames are present or still missing.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "paint_cel",
        "Write one cel from an ASCII pixel map (text-only AIs). Payload: {map:{char:hex|null}, rows:[strings]}.",
        {
            "project": {"type": "string"},
            "tag": {"type": "string"},
            "frame": {"type": "integer"},
            "layer": {"type": "string"},
            "payload": {"type": "object"},
        },
        ["project", "tag", "payload"],
    ),
    _tool(
        "ingest_images",
        "Chroma-key, fit to canvas, quantize. Reads raw/, writes clean/.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "compile_sprite",
        "Write a real .aseprite file (layers, frames, tags, palette).",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "export_sprite",
        "Export sprite sheet PNG, GIF preview, and engine JSON.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "validate_sprite",
        "Run the deliverable checklist. Do not tell the user it is done unless deliverable=true.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "build",
        "ingest + compile + export + validate. Preferred one-shot after sources are in raw/.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "open_in_aseprite",
        "Launch Aseprite on the compiled file.",
        {"project": {"type": "string"}},
        ["project"],
    ),
    _tool(
        "demo",
        "Build the built-in slime example to verify the pipeline.",
        {
            "dest": {"type": "string"},
            "open": {"type": "boolean"},
        },
        ["dest"],
    ),
]


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "doctor": lambda a: doctor(),
    "list_templates": lambda a: {"ok": True, "templates": list_templates()},
    "init_project": lambda a: init_project(
        a["dest"],
        a.get("template") or "character-platformer",
        name=a.get("name"),
        description=a.get("description") or "",
    ),
    "generation_brief": lambda a: generation_brief(a["project"]),
    "project_status": lambda a: project_status(a["project"]),
    "paint_cel": lambda a: paint_cel(
        a["project"],
        a["payload"],
        tag=a["tag"],
        frame=int(a.get("frame") or 0),
        layer=a.get("layer"),
    ),
    "ingest_images": lambda a: ingest_project(a["project"]),
    "compile_sprite": lambda a: compile_project(a["project"]),
    "export_sprite": lambda a: export_project(a["project"]),
    "validate_sprite": lambda a: validate_project(a["project"]),
    "build": lambda a: build_project(a["project"]),
    "open_in_aseprite": lambda a: open_in_aseprite(a["project"]),
    "demo": lambda a: demo_project(a["dest"], open_file=bool(a.get("open"))),
}


def _write_ndjson(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _write_lsp(msg: dict[str, Any]) -> None:
    payload = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + payload)
    sys.stdout.buffer.flush()


def _read_messages():
    """Accept both MCP newline-delimited JSON and LSP Content-Length framing."""
    buf = sys.stdin.buffer
    pending = b""
    mode = None  # 'ndjson' | 'lsp'
    while True:
        chunk = buf.readline()
        if not chunk:
            return
        if mode is None:
            if chunk.lower().startswith(b"content-length:"):
                mode = "lsp"
            else:
                mode = "ndjson"
        if mode == "ndjson":
            line = (pending + chunk).decode("utf-8").strip()
            pending = b""
            if not line:
                continue
            yield json.loads(line)
            continue
        # LSP
        headers = chunk
        while True:
            line = buf.readline()
            if not line:
                return
            headers += line
            if line in (b"\r\n", b"\n"):
                break
        length = 0
        for raw in headers.split(b"\n"):
            if raw.lower().startswith(b"content-length:"):
                length = int(raw.split(b":", 1)[1].strip())
        body = buf.read(length)
        yield json.loads(body.decode("utf-8"))


def _result_text(data: Any) -> dict[str, Any]:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    is_error = isinstance(data, dict) and data.get("ok") is False
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _handle(msg: dict[str, Any], writer) -> None:
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        writer(
            {
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "protocolVersion": params.get("protocolVersion") or PROTOCOL,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "ase-deliver", "version": __version__},
                },
            }
        )
        return
    if method == "notifications/initialized" or method == "initialized":
        return
    if method == "tools/list":
        writer({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        return
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if not handler:
            writer(
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "content": [{"type": "text", "text": f"Unknown tool {name}"}],
                        "isError": True,
                    },
                }
            )
            return
        try:
            data = handler(args)
            writer({"jsonrpc": "2.0", "id": mid, "result": _result_text(data)})
        except Exception as exc:
            writer(
                {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "result": {
                        "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                        "isError": True,
                    },
                }
            )
        return
    if method == "ping":
        writer({"jsonrpc": "2.0", "id": mid, "result": {}})
        return
    if mid is not None:
        writer(
            {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"Unknown method {method}"},
            }
        )


def run_mcp() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stdin.reconfigure(encoding="utf-8")
        except Exception:
            pass
    # Detect framing from the first message; default NDJSON (MCP spec).
    first = True
    writer = _write_ndjson
    stdin = sys.stdin
    while True:
        if first:
            # Peek first bytes to choose framing.
            peek = sys.stdin.buffer.peek(16) if hasattr(sys.stdin.buffer, "peek") else b""
            if peek.lower().startswith(b"content-length:"):
                writer = _write_lsp
                for msg in _read_messages():
                    _handle(msg, writer)
                return
            first = False
        line = stdin.readline()
        if not line:
            return
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        _handle(msg, writer)
