#!/usr/bin/env python3
"""Build the deterministic Week 1 launch assets.

The terminal cast runs the real FFA-001 reproduce, detect, and regress commands.
PNG and GIF rendering uses local authoring tools only; it does not change the
project's dependency-free runtime or test contract.
"""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess  # nosec B404 -- fixed local authoring commands
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
CAST_PATH = ASSETS / "ffa-001-terminal.cast"
GIF_PATH = ASSETS / "ffa-001-terminal.gif"
CARDS = (
    (ASSETS / "launch-card-1200x630.svg", ASSETS / "launch-card-1200x630.png", 1200, 630),
    (ASSETS / "launch-card-1080x1080.svg", ASSETS / "launch-card-1080x1080.png", 1080, 1080),
)


def _run_fixture(mode: str) -> tuple[str, dict[str, object]]:
    env = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }
    if os.name == "nt" and (system_root := os.environ.get("SYSTEMROOT")):
        env["SYSTEMROOT"] = system_root
    result = subprocess.run(  # nosec B603
        [sys.executable, str(ROOT / "atlas.py"), "run", "FFA-001", "--mode", mode],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    decoded = json.loads(result.stdout)
    if not isinstance(decoded, list) or len(decoded) != 1 or decoded[0].get("status") != "pass":
        raise RuntimeError(f"FFA-001 {mode} did not return one passing result")
    evidence = decoded[0].get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise RuntimeError(f"FFA-001 {mode} returned no evidence")
    return result.stdout, evidence


def _terminal_text(value: str) -> str:
    return value.replace("\n", "\r\n")


def _write_cast() -> None:
    outputs: dict[str, str] = {}
    evidence: dict[str, dict[str, object]] = {}
    for mode in ("reproduce", "detect", "regress"):
        outputs[mode], evidence[mode] = _run_fixture(mode)

    if evidence["reproduce"].get("vulnerable_gate_accepts") is not True:
        raise RuntimeError("reproduce evidence changed")
    if evidence["detect"].get("detector_findings") != [
        "head_sha_mismatch",
        "coverage_not_bound_to_head",
    ]:
        raise RuntimeError("detector evidence changed")
    if (
        evidence["regress"].get("repaired_gate_accepts") is not False
        or evidence["regress"].get("fresh_receipt_accepts") is not True
    ):
        raise RuntimeError("regression evidence changed")

    clear = "\x1b[2J\x1b[H"
    prompt = "\x1b[38;2;192;132;252m$\x1b[0m"
    heading = "\x1b[1;38;2;248;247;255m"
    success = "\x1b[1;38;2;167;139;250m"
    dim = "\x1b[38;2;169;183;208m"
    reset = "\x1b[0m"
    events: list[list[object]] = [
        [0.0, "o", clear],
        [
            0.2,
            "o",
            f"{heading}Fleet Failure Atlas · FFA-001{reset}\r\n{dim}real fixture output · synthetic evidence · offline{reset}\r\n\r\n",
        ],
        [0.9, "o", f"{prompt} python3 atlas.py run FFA-001 --mode reproduce\r\n"],
        [1.6, "o", _terminal_text(outputs["reproduce"])],
        [5.0, "o", f"{success}✓ failure reproduced: stale green receipt accepted{reset}\r\n"],
        [6.2, "o", clear],
        [
            6.4,
            "o",
            f"{heading}Fleet Failure Atlas · FFA-001{reset}\r\n{dim}bind evidence to the exact revision and changed surface{reset}\r\n\r\n",
        ],
        [7.0, "o", f"{prompt} python3 atlas.py run FFA-001 --mode detect\r\n"],
        [7.7, "o", _terminal_text(outputs["detect"])],
        [11.0, "o", f"{success}✓ detected: SHA mismatch + coverage gap{reset}\r\n"],
        [12.0, "o", clear],
        [
            12.2,
            "o",
            f"{heading}Fleet Failure Atlas · FFA-001{reset}\r\n{dim}prove both stale rejection and fresh acceptance{reset}\r\n\r\n",
        ],
        [12.8, "o", f"{prompt} python3 atlas.py run FFA-001 --mode regress\r\n"],
        [13.5, "o", _terminal_text(outputs["regress"])],
        [17.3, "o", f"{success}✓ regression proof: stale rejected · fresh accepted{reset}\r\n"],
        [19.0, "o", f"{dim}github.com/korovin-aa97/fleet-failure-atlas{reset}\r\n"],
    ]
    header = {
        "version": 2,
        "width": 110,
        "height": 28,
        "timestamp": 0,
        "env": {"SHELL": "sh", "TERM": "xterm-256color"},
    }
    lines = [json.dumps(header, separators=(",", ":"))]
    lines.extend(json.dumps(event, ensure_ascii=False, separators=(",", ":")) for event in events)
    CAST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_gif() -> None:
    agg = shutil.which("agg")
    if not agg:
        raise RuntimeError("agg is required to render docs/assets/ffa-001-terminal.gif")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to assemble docs/assets/ffa-001-terminal.gif")

    # Render full terminal states before assembling the animation. This avoids
    # transparent delta-frame artifacts after ANSI clear-screen events.
    frames = (
        (1, 0.7),
        (2, 0.8),
        (3, 3.3),
        (4, 1.2),
        (6, 0.5),
        (7, 0.8),
        (8, 3.3),
        (9, 1.0),
        (11, 0.5),
        (12, 0.8),
        (13, 3.8),
        (14, 1.7),
        (15, 1.6),
    )
    with tempfile.TemporaryDirectory(prefix="ffa-launch-") as temp_dir:
        temp = Path(temp_dir)
        rendered: list[tuple[Path, float]] = []
        for position, (event, duration) in enumerate(frames):
            single_gif = temp / f"frame-{position:02d}.gif"
            png = temp / f"frame-{position:02d}.png"
            subprocess.run(  # nosec B603
                [
                    agg,
                    "--quiet",
                    "--font-family",
                    "Menlo,DejaVu Sans Mono",
                    "--font-size",
                    "17",
                    "--line-height",
                    "1.3",
                    "--theme",
                    "dracula",
                    "--cols",
                    "110",
                    "--rows",
                    "28",
                    "--renderer",
                    "resvg",
                    "--select",
                    f"event:{event}",
                    "--no-loop",
                    str(CAST_PATH),
                    str(single_gif),
                ],
                cwd=ROOT,
                check=True,
                timeout=30,
            )
            subprocess.run(  # nosec B603
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(single_gif),
                    "-frames:v",
                    "1",
                    "-y",
                    str(png),
                ],
                cwd=ROOT,
                check=True,
                timeout=30,
            )
            rendered.append((png, duration))

        concat = temp / "frames.txt"
        concat_lines: list[str] = []
        for png, duration in rendered:
            concat_lines.extend((f"file '{png}'", f"duration {duration:.1f}"))
        concat_lines.append(f"file '{rendered[-1][0]}'")
        concat.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        subprocess.run(  # nosec B603
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-filter_complex",
                "split[a][b];[a]palettegen=max_colors=128:reserve_transparent=0[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:alpha_threshold=0",
                "-fps_mode",
                "vfr",
                "-gifflags",
                "0",
                "-loop",
                "0",
                "-y",
                str(GIF_PATH),
            ],
            cwd=ROOT,
            check=True,
            timeout=120,
        )


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError(f"{path.relative_to(ROOT)} is not a PNG")
    return struct.unpack(">II", data[16:24])


def _render_cards() -> None:
    sips = shutil.which("sips")
    if not sips:
        raise RuntimeError("sips is required to render launch-card PNGs on macOS")
    for source, target, width, height in CARDS:
        subprocess.run(  # nosec B603
            [sips, "-s", "format", "png", str(source), "--out", str(target)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if _png_size(target) != (width, height):
            raise RuntimeError(f"unexpected PNG dimensions for {target.relative_to(ROOT)}")


def main() -> int:
    _write_cast()
    _render_gif()
    _render_cards()
    print("Built Week 1 assets: deterministic FFA-001 cast/GIF and two SVG/PNG cards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
