#!/usr/bin/env python3
"""Validate, run, and publish the Fleet Failure Atlas.

The tool deliberately uses only the Python standard library so a clean clone can
exercise every public pattern without installing a package or starting a service.
"""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Iterable


ROOT = Path(__file__).resolve().parent
PATTERNS_DIR = ROOT / "patterns"
SITE_DIR = ROOT / "docs"
TIMEOUT_SECONDS = 5

REQUIRED_METADATA = (
    "id",
    "slug",
    "title",
    "lifecycle",
    "symptoms",
    "architectures",
    "provenance",
    "status",
    "fixture",
)
REQUIRED_SECTIONS = (
    "Scope and affected architecture",
    "Symptom and observable signature",
    "Root mechanism",
    "Minimal safe fixture",
    "Deterministic detector",
    "Repair invariant",
    "Regression check",
    "False positives and non-applicable cases",
    "Provenance",
)
ALLOWED_PROVENANCE = {"observed", "externally-reported", "hypothetical"}
ALLOWED_STATUS = {"executable", "documented"}
PRIVATE_MARKERS = (
    "corp.internal",
    ".private.example",
    "/srv/private-agent",
    "internal-release-only",
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


class AtlasError(RuntimeError):
    """A release-blocking validation error."""


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_pattern(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AtlasError(f"{path.relative_to(ROOT)}: missing front matter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AtlasError(f"{path.relative_to(ROOT)}: unclosed front matter") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise AtlasError(f"{path.relative_to(ROOT)}: invalid metadata line {line!r}")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key or not value or key in metadata:
            raise AtlasError(f"{path.relative_to(ROOT)}: invalid or duplicate metadata key {key!r}")
        metadata[key] = value

    body = "\n".join(lines[end + 1 :]).strip() + "\n"
    headings = re.findall(r"^## (.+?)\s*$", body, flags=re.MULTILINE)
    return {"path": path, "metadata": metadata, "body": body, "headings": headings}


def load_patterns() -> list[dict[str, object]]:
    return [parse_pattern(path) for path in sorted(PATTERNS_DIR.glob("*.md"))]


def _check_local_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        clean = target.split("#", 1)[0]
        if not clean or clean.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / clean).resolve()
        if ROOT not in resolved.parents and resolved != ROOT:
            errors.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
        elif not resolved.exists():
            errors.append(f"{path.relative_to(ROOT)}: broken local link: {target}")
    return errors


def _check_skill_alignment() -> list[str]:
    def checklist_block(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        match = re.search(
            r"<!-- checklist:start -->\s*(.*?)\s*<!-- checklist:end -->",
            text,
            flags=re.DOTALL,
        )
        if not match:
            raise AtlasError(f"{path.relative_to(ROOT)}: missing checklist markers")
        return re.sub(r"\s+", " ", match.group(1)).strip()

    try:
        plain = checklist_block(ROOT / "regression-review-checklist.md")
        skill = checklist_block(ROOT / "skills/regression-review/SKILL.md")
    except AtlasError as exc:
        return [str(exc)]
    return [] if plain == skill else ["regression checklist and SKILL.md have drifted"]


def validate() -> list[str]:
    errors: list[str] = []
    patterns = load_patterns()
    if len(patterns) < 3:
        errors.append("the first release requires at least three patterns")
    ids: set[str] = set()
    slugs: set[str] = set()

    for pattern in patterns:
        path = pattern["path"]
        assert isinstance(path, Path)
        metadata = pattern["metadata"]
        assert isinstance(metadata, dict)
        headings = pattern["headings"]
        assert isinstance(headings, list)

        for key in REQUIRED_METADATA:
            if not metadata.get(key):
                errors.append(f"{path.relative_to(ROOT)}: missing metadata {key}")
        pattern_id = metadata.get("id", "")
        slug = metadata.get("slug", "")
        if not re.fullmatch(r"FFA-\d{3}", pattern_id):
            errors.append(f"{path.relative_to(ROOT)}: id must match FFA-NNN")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            errors.append(f"{path.relative_to(ROOT)}: slug is not URL-safe")
        if pattern_id in ids:
            errors.append(f"{path.relative_to(ROOT)}: duplicate id {pattern_id}")
        if slug in slugs:
            errors.append(f"{path.relative_to(ROOT)}: duplicate slug {slug}")
        ids.add(pattern_id)
        slugs.add(slug)
        if metadata.get("provenance") not in ALLOWED_PROVENANCE:
            errors.append(f"{path.relative_to(ROOT)}: invalid provenance")
        if metadata.get("status") not in ALLOWED_STATUS:
            errors.append(f"{path.relative_to(ROOT)}: invalid status")
        for key in ("lifecycle", "symptoms", "architectures"):
            if not _split_csv(metadata.get(key, "")):
                errors.append(f"{path.relative_to(ROOT)}: {key} must contain a value")
        for section in REQUIRED_SECTIONS:
            if section not in headings:
                errors.append(f"{path.relative_to(ROOT)}: missing section {section!r}")

        fixture_value = metadata.get("fixture", "")
        fixture = (ROOT / fixture_value).resolve()
        if ROOT not in fixture.parents or fixture.parent != (ROOT / "fixtures"):
            errors.append(f"{path.relative_to(ROOT)}: fixture must be directly under fixtures/")
        elif not fixture.is_file():
            errors.append(f"{path.relative_to(ROOT)}: fixture does not exist: {fixture_value}")

    markdown_files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"] + list(ROOT.glob("docs/*.md")) + list(PATTERNS_DIR.glob("*.md"))
    for path in markdown_files:
        if path.exists():
            errors.extend(_check_local_links(path, path.read_text(encoding="utf-8")))
    errors.extend(_check_skill_alignment())
    return errors


def safety_scan() -> list[str]:
    errors: list[str] = []
    text_suffixes = {"", ".cff", ".html", ".json", ".md", ".py", ".svg", ".txt", ".yaml", ".yml"}
    checked = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix in text_suffixes
        and path.name != "atlas.py"  # contains the scanner's own deny-list literals
    ]
    for path in sorted(checked):
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for marker in PRIVATE_MARKERS:
            if marker in lowered:
                errors.append(f"{path.relative_to(ROOT)}: private-topology marker {marker!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: possible secret matching {pattern.pattern!r}")
        if re.search(r"/(?:Users|home)/[A-Za-z0-9._-]+/", text):
            errors.append(f"{path.relative_to(ROOT)}: absolute user path")
    return errors


def run_fixture(pattern: dict[str, object], mode: str) -> dict[str, object]:
    metadata = pattern["metadata"]
    assert isinstance(metadata, dict)
    fixture = ROOT / metadata["fixture"]
    with tempfile.TemporaryDirectory(prefix="ffa-") as temp_dir:
        env = {
            "ATLAS_FIXTURE_ROOT": temp_dir,
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
        }
        try:
            completed = subprocess.run(
                [sys.executable, str(fixture), mode],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AtlasError(f"{metadata['id']} {mode}: exceeded {TIMEOUT_SECONDS}s") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise AtlasError(f"{metadata['id']} {mode}: fixture failed: {detail}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AtlasError(f"{metadata['id']} {mode}: fixture did not return JSON") from exc
    if result.get("pattern_id") != metadata["id"] or result.get("mode") != mode or result.get("status") != "pass":
        raise AtlasError(f"{metadata['id']} {mode}: malformed or unsuccessful result: {result}")
    if not isinstance(result.get("evidence"), dict) or not result["evidence"]:
        raise AtlasError(f"{metadata['id']} {mode}: evidence must be a non-empty object")
    return result


def run(pattern_id: str | None = None, mode: str = "all") -> list[dict[str, object]]:
    patterns = load_patterns()
    if pattern_id:
        patterns = [item for item in patterns if item["metadata"]["id"] == pattern_id]
        if not patterns:
            raise AtlasError(f"unknown pattern: {pattern_id}")
    modes = ("reproduce", "detect", "regress") if mode == "all" else (mode,)
    return [run_fixture(pattern, selected) for pattern in patterns for selected in modes]


def _inline_markdown(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def _render_markdown(body: str) -> str:
    chunks: list[str] = []
    in_list = False
    in_code = False
    code_lines: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            chunks.append(f"<p>{_inline_markdown(' '.join(paragraph_lines))}</p>")
            paragraph_lines.clear()

    for line in body.splitlines():
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                chunks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                if in_list:
                    chunks.append("</ul>")
                    in_list = False
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("# "):
            flush_paragraph()
            chunks.append(f"<h1>{_inline_markdown(line[2:])}</h1>")
        elif line.startswith("## "):
            flush_paragraph()
            if in_list:
                chunks.append("</ul>")
                in_list = False
            heading = line[3:]
            anchor = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
            chunks.append(f'<h2 id="{anchor}">{_inline_markdown(heading)}</h2>')
        elif line.startswith("- "):
            flush_paragraph()
            if not in_list:
                chunks.append("<ul>")
                in_list = True
            chunks.append(f"<li>{_inline_markdown(line[2:])}</li>")
        elif not line.strip():
            flush_paragraph()
            if in_list:
                chunks.append("</ul>")
                in_list = False
        else:
            if in_list:
                chunks.append("</ul>")
                in_list = False
            paragraph_lines.append(line.strip())
    flush_paragraph()
    if in_list:
        chunks.append("</ul>")
    if in_code:
        chunks.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(chunks)


STYLE = """
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a30;--ink:#ecf2ff;--muted:#a9b7d0;--accent:#7dd3fc;--line:#263653}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 75% 0,#182849 0,var(--bg) 42%);color:var(--ink);font:16px/1.65 system-ui,sans-serif}
main{max-width:980px;margin:auto;padding:64px 24px}a{color:var(--accent)}.eyebrow{text-transform:uppercase;letter-spacing:.16em;color:var(--accent);font-size:.75rem}
h1{font-size:clamp(2.4rem,7vw,5.5rem);line-height:.98;max-width:850px;margin:.2em 0}.lede{font-size:1.2rem;color:var(--muted);max-width:720px}
.controls{display:flex;gap:12px;flex-wrap:wrap;margin:32px 0}.controls input,.controls select{background:var(--panel);border:1px solid var(--line);color:var(--ink);padding:12px 14px;border-radius:10px;font:inherit}
.controls input{flex:1;min-width:240px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.card{background:color-mix(in srgb,var(--panel) 90%,transparent);border:1px solid var(--line);border-radius:16px;padding:20px;text-decoration:none;color:var(--ink)}
.card:hover{border-color:var(--accent);transform:translateY(-2px)}.tag{display:inline-block;margin:3px 4px 3px 0;padding:2px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:.75rem}
.meta{color:var(--muted);font-size:.9rem}.pattern{max-width:780px}.pattern h2{margin-top:2.2em}.pattern pre{overflow:auto;background:#070b15;border:1px solid var(--line);padding:16px;border-radius:12px}.pattern code{background:#070b15;padding:.15em .35em;border-radius:4px}
footer{margin-top:48px;padding-top:24px;border-top:1px solid var(--line);color:var(--muted)}@media(prefers-reduced-motion:no-preference){.card{transition:.15s ease}}
""".strip()


def _page(title: str, content: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Executable failure patterns for autonomous coding-agent systems."><meta name="theme-color" content="#0b1020">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="Reproduce, detect, and prevent autonomous coding-agent failures.">
<meta property="og:image" content="https://korovin-aa97.github.io/fleet-failure-atlas/assets/social-preview.png"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body><main>{content}<footer><a href="{prefix}index.html">Fleet Failure Atlas</a> · <a href="https://github.com/korovin-aa97/fleet-failure-atlas">GitHub</a> · MIT licensed</footer></main></body></html>
"""


def site_files() -> dict[Path, str]:
    entries: list[dict[str, object]] = []
    files: dict[Path, str] = {}
    for pattern in load_patterns():
        metadata = pattern["metadata"]
        assert isinstance(metadata, dict)
        entry = {
            "id": metadata["id"],
            "slug": metadata["slug"],
            "title": metadata["title"],
            "lifecycle": _split_csv(metadata["lifecycle"]),
            "symptoms": _split_csv(metadata["symptoms"]),
            "architectures": _split_csv(metadata["architectures"]),
            "provenance": metadata["provenance"],
            "status": metadata["status"],
        }
        entries.append(entry)
        meta = f'<p class="meta">{metadata["id"]} · {metadata["provenance"]} · {metadata["status"]}</p>'
        body = f'<a href="../index.html">← All patterns</a><article class="pattern">{meta}{_render_markdown(pattern["body"])}</article>'
        files=files | {Path("patterns") / f'{metadata["slug"]}.html': _page(str(metadata["title"]), body, "../")}

    data = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    card_items: list[str] = []
    for entry in entries:
        search_value = " ".join(
            [
                str(entry["title"]),
                *entry["symptoms"],
                *entry["lifecycle"],
                *entry["architectures"],
            ]
        ).lower()
        stage = entry["lifecycle"][0]
        tags = "".join(
            f'<span class="tag">{html.escape(tag)}</span>'
            for tag in entry["symptoms"]
        )
        card_items.append(
            f'<a class="card" data-search="{html.escape(search_value)}" '
            f'data-stage="{html.escape(stage)}" href="patterns/{entry["slug"]}.html">'
            f'<span class="eyebrow">{entry["id"]} · {html.escape(stage)}</span>'
            f'<h2>{html.escape(entry["title"])}</h2>'
            f'<p class="meta">{html.escape(entry["provenance"])} provenance</p>'
            f'{tags}</a>'
        )
    cards = "\n".join(card_items)
    stages = sorted({stage for entry in entries for stage in entry["lifecycle"]})
    options = "".join(f'<option value="{html.escape(stage)}">{html.escape(stage)}</option>' for stage in stages)
    script = """<script>const q=document.querySelector('#q'),stage=document.querySelector('#stage'),cards=[...document.querySelectorAll('.card')];function filter(){const term=q.value.toLowerCase();cards.forEach(c=>c.hidden=!(c.dataset.search.includes(term)&&(!stage.value||c.dataset.stage===stage.value)))}q.addEventListener('input',filter);stage.addEventListener('change',filter);</script>"""
    content = f'''<p class="eyebrow">Reproduce · detect · prevent</p><h1>Failures become useful when they become executable.</h1><p class="lede">A clean-room field guide to autonomous coding-agent failures. Every entry includes a bounded fixture, deterministic detector, repair invariant, and regression proof.</p><div class="controls"><input id="q" type="search" aria-label="Search patterns" placeholder="Search symptoms, systems, or titles…"><select id="stage" aria-label="Filter by lifecycle"><option value="">All lifecycle stages</option>{options}</select></div><section class="grid">{cards}</section>{script}'''
    files[Path("index.html")] = _page("Fleet Failure Atlas", content)
    files[Path("atlas.json")] = data
    return files


def build_site(check: bool = False) -> list[str]:
    drift: list[str] = []
    expected = site_files()
    for relative, content in expected.items():
        path = SITE_DIR / relative
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    generated = {SITE_DIR / relative for relative in expected}
    for path in (SITE_DIR / "patterns").glob("*.html"):
        if path not in generated:
            if check:
                drift.append(str(path.relative_to(ROOT)))
            else:
                path.unlink()
    return drift


def _fail_if(errors: Iterable[str], title: str) -> None:
    errors = list(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(f"{title} failed with {len(errors)} error(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate pattern schema and local links")
    subparsers.add_parser("safety", help="scan publishable content for secrets and private markers")
    run_parser = subparsers.add_parser("run", help="run one or all executable patterns")
    run_parser.add_argument("pattern_id", nargs="?", help="stable ID such as FFA-001")
    run_parser.add_argument("--mode", choices=("reproduce", "detect", "regress", "all"), default="all")
    site_parser = subparsers.add_parser("build-site", help="generate the static atlas")
    site_parser.add_argument("--check", action="store_true", help="fail when checked-in output has drifted")
    subparsers.add_parser("check", help="run every release gate")
    args = parser.parse_args()

    if args.command == "validate":
        _fail_if(validate(), "validation")
        print(f"Validated {len(load_patterns())} patterns.")
    elif args.command == "safety":
        _fail_if(safety_scan(), "safety scan")
        print("Safety scan passed.")
    elif args.command == "run":
        results = run(args.pattern_id, args.mode)
        print(json.dumps(results, indent=2, sort_keys=True))
    elif args.command == "build-site":
        drift = build_site(args.check)
        _fail_if((f"generated site drift: {path}" for path in drift), "site check")
        print("Static site is current." if args.check else "Static site generated.")
    elif args.command == "check":
        _fail_if(validate(), "validation")
        _fail_if(safety_scan(), "safety scan")
        results = run()
        _fail_if((f"generated site drift: {path}" for path in build_site(check=True)), "site check")
        print(f"Release gates passed: {len(load_patterns())} patterns, {len(results)} fixture checks.")


if __name__ == "__main__":
    main()
