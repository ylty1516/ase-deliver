from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ase_deliver.asefile import read_ase_info
from ase_deliver.demo import make_demo_spec, seed_demo_project
from ase_deliver.doctor import find_aseprite
from ase_deliver.ops import build_project, paint_cel
from ase_deliver.spec import expand_spec


class RoundTripTests(unittest.TestCase):
    def test_demo_frames_are_16x16(self) -> None:
        spec = make_demo_spec()
        expanded = expand_spec(spec)
        self.assertEqual(expanded["canvas"]["width"], 16)
        self.assertEqual(len(expanded["frames"]), 8)

    def test_build_demo_and_read_aseprite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "slime"
            seed_demo_project(dest)
            result = build_project(dest)
            self.assertTrue(result.get("ok"), msg=json.dumps(result, indent=2))
            ase = dest / "out" / "slime.aseprite"
            self.assertTrue(ase.is_file())
            info = read_ase_info(ase)
            self.assertEqual(info.width, 16)
            self.assertEqual(info.height, 16)
            self.assertEqual(info.frames, 8)
            self.assertEqual(info.layers, ["sprite"])
            self.assertEqual(info.tags, ["idle", "walk"])
            self.assertEqual(info.depth, 8)
            self.assertTrue((dest / "out" / "slime.png").is_file())
            self.assertTrue((dest / "out" / "slime.gif").is_file())
            self.assertTrue((dest / "out" / "slime.json").is_file())

            aseprite = find_aseprite()
            if aseprite:
                proc = subprocess.run(
                    [str(aseprite), "-b", "--list-tags", "--list-layers", str(ase)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                out = (proc.stdout or "") + (proc.stderr or "")
                self.assertIn("idle", out)
                self.assertIn("walk", out)
                self.assertIn("sprite", out)

    def test_paint_cel_ascii(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "dot"
            seed_demo_project(dest, name="dot")
            payload = {
                "map": {".": None, "#": "#ffffff"},
                "rows": [
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                    ".......##.......",
                    ".......##.......",
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                    "................",
                ],
            }
            painted = paint_cel(dest, payload, tag="idle", frame=0)
            self.assertTrue(painted["ok"])
            self.assertTrue(Path(painted["png"]).is_file())


if __name__ == "__main__":
    unittest.main()
