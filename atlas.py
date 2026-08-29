#!/usr/bin/env python3
"""Validate, run, and publish the Fleet Failure Atlas.

The tool deliberately uses only the Python standard library so a clean clone can
exercise every public pattern without installing a package or starting a service.
"""

from __future__ import annotations

import argparse
import contextlib
import html
import json
import os
import re
import signal
import subprocess  # nosec B404
import sys
import tempfile
import threading
import time
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO, TypedDict

ROOT = Path(__file__).resolve().parent
PATTERNS_DIR = ROOT / "patterns"
SITE_DIR = ROOT / "docs"
TIMEOUT_SECONDS = 5
MAX_OUTPUT_BYTES = 64 * 1024

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
PRIVATE_MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("corp.", "internal"),
        (".private.", "example"),
        ("/srv/private-", "agent"),
        ("internal-release-", "only"),
    )
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


class AtlasError(RuntimeError):
    """A release-blocking validation error."""


class Pattern(TypedDict):
    path: Path
    metadata: dict[str, str]
    body: str
    headings: list[str]


class FixtureResult(TypedDict):
    pattern_id: str
    mode: str
    status: str
    evidence: dict[str, object]


class SiteEntry(TypedDict):
    id: str
    slug: str
    title: str
    lifecycle: list[str]
    symptoms: list[str]
    architectures: list[str]
    provenance: str
    status: str


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_pattern(path: Path) -> Pattern:
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


def load_patterns() -> list[Pattern]:
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
    try:
        patterns = load_patterns()
    except (AtlasError, OSError, UnicodeError) as exc:
        return [str(exc)]
    executable_count = sum(
        pattern["metadata"].get("status") == "executable" for pattern in patterns
    )
    if executable_count < 3:
        errors.append("the collection requires at least three executable patterns")
    ids: set[str] = set()
    slugs: set[str] = set()

    for pattern in patterns:
        path = pattern["path"]
        metadata = pattern["metadata"]
        headings = pattern["headings"]

        unexpected = sorted(set(metadata) - set(REQUIRED_METADATA))
        if unexpected:
            errors.append(f"{path.relative_to(ROOT)}: unexpected metadata: {', '.join(unexpected)}")

        for key in REQUIRED_METADATA:
            if not metadata.get(key):
                errors.append(f"{path.relative_to(ROOT)}: missing metadata {key}")
        pattern_id = metadata.get("id", "")
        slug = metadata.get("slug", "")
        if not re.fullmatch(r"FFA-\d{3}", pattern_id):
            errors.append(f"{path.relative_to(ROOT)}: id must match FFA-NNN")
        filename_match = re.match(r"(\d{3})[-_]", path.name)
        if not filename_match or pattern_id.removeprefix("FFA-") != filename_match.group(1):
            errors.append(f"{path.relative_to(ROOT)}: filename prefix must match id")
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
            if headings.count(section) != 1:
                errors.append(f"{path.relative_to(ROOT)}: missing section {section!r}")
            else:
                section_match = re.search(
                    rf"^## {re.escape(section)}\s*$\n(.*?)(?=^## |\Z)",
                    pattern["body"],
                    flags=re.MULTILINE | re.DOTALL,
                )
                if not section_match or not section_match.group(1).strip():
                    errors.append(f"{path.relative_to(ROOT)}: empty section {section!r}")

        title_headings = re.findall(r"^# (.+?)\s*$", pattern["body"], flags=re.MULTILINE)
        if title_headings != [metadata.get("title", "")]:
            errors.append(f"{path.relative_to(ROOT)}: level-one heading must equal title")

        fixture_value = metadata.get("fixture", "")
        if metadata.get("status") == "documented":
            if fixture_value != "none":
                errors.append(f"{path.relative_to(ROOT)}: documented entries require fixture: none")
        else:
            fixture = (ROOT / fixture_value).resolve()
            if ROOT not in fixture.parents or fixture.parent != (ROOT / "fixtures"):
                errors.append(f"{path.relative_to(ROOT)}: fixture must be directly under fixtures/")
            elif fixture.suffix != ".py" or not fixture.is_file():
                errors.append(f"{path.relative_to(ROOT)}: fixture must be an existing Python file")

    markdown_files = [path for path in ROOT.rglob("*.md") if ".git" not in path.parts]
    for path in markdown_files:
        if path.exists():
            errors.extend(_check_local_links(path, path.read_text(encoding="utf-8")))
    errors.extend(_check_skill_alignment())
    return errors


def safety_scan() -> list[str]:
    errors: list[str] = []
    checked = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    ]
    for path in sorted(checked):
        raw = path.read_bytes()
        if b"\0" in raw[:8192]:
            continue
        text = raw.decode("utf-8", errors="replace")
        lowered = text.lower()
        for marker in PRIVATE_MARKERS:
            if marker in lowered:
                errors.append(f"{path.relative_to(ROOT)}: private-topology marker {marker!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"{path.relative_to(ROOT)}: possible secret matching {pattern.pattern!r}"
                )
        if re.search(r"/(?:Users|home)/[A-Za-z0-9._-]+/", text):
            errors.append(f"{path.relative_to(ROOT)}: absolute user path")
        if re.search(r"\b[A-Za-z]:\\(?:Users|Documents and Settings)\\[^\\]+\\", text):
            errors.append(f"{path.relative_to(ROOT)}: absolute Windows user path")
    return errors


def _kill_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    else:
        process.kill()


def _read_bounded(stream: BinaryIO, sink: bytearray, overflow: threading.Event) -> None:
    while True:
        chunk = stream.read(4096)
        if not chunk:
            return
        if len(sink) + len(chunk) > MAX_OUTPUT_BYTES:
            overflow.set()
            return
        sink.extend(chunk)


def _execute_fixture(fixture: Path, mode: str, temp_dir: str) -> tuple[int, bytes, bytes]:
    env = {
        "ATLAS_FIXTURE_ROOT": temp_dir,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }
    if os.name == "nt" and (system_root := os.environ.get("SYSTEMROOT")):
        env["SYSTEMROOT"] = system_root
    process = subprocess.Popen(  # nosec B603
        [sys.executable, str(fixture), mode],
        cwd=temp_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name == "posix",
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    if process.stdout is None or process.stderr is None:
        _kill_process(process)
        raise AtlasError("fixture runner could not capture output")

    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()
    readers = [
        threading.Thread(target=_read_bounded, args=(process.stdout, stdout, overflow)),
        threading.Thread(target=_read_bounded, args=(process.stderr, stderr, overflow)),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + TIMEOUT_SECONDS
    reason: str | None = None
    while process.poll() is None:
        if overflow.is_set():
            reason = f"exceeded {MAX_OUTPUT_BYTES} output bytes"
            break
        if time.monotonic() >= deadline:
            reason = f"exceeded {TIMEOUT_SECONDS}s"
            break
        time.sleep(0.01)
    if reason:
        _kill_process(process)
    return_code = process.wait()
    for reader in readers:
        reader.join(timeout=1)
    process.stdout.close()
    process.stderr.close()
    if overflow.is_set() and reason is None:
        reason = f"exceeded {MAX_OUTPUT_BYTES} output bytes"
    if reason:
        raise AtlasError(reason)
    return return_code, bytes(stdout), bytes(stderr)


def run_fixture(pattern: Pattern, mode: str) -> FixtureResult:
    metadata = pattern["metadata"]
    fixture = (ROOT / metadata["fixture"]).resolve()
    if fixture.parent != (ROOT / "fixtures").resolve() or not fixture.is_file():
        raise AtlasError(f"{metadata['id']} {mode}: unsafe or missing fixture path")
    with tempfile.TemporaryDirectory(prefix="ffa-") as temp_dir:
        try:
            return_code, stdout_bytes, stderr_bytes = _execute_fixture(fixture, mode, temp_dir)
        except (AtlasError, OSError) as exc:
            raise AtlasError(f"{metadata['id']} {mode}: {exc}") from exc
    try:
        stdout = stdout_bytes.decode("utf-8")
        stderr = stderr_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AtlasError(f"{metadata['id']} {mode}: fixture output is not UTF-8") from exc
    if return_code != 0:
        detail = (stderr.strip() or stdout.strip())[:1000]
        raise AtlasError(f"{metadata['id']} {mode}: fixture failed: {detail}")
    try:
        decoded = json.loads(
            stdout,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise AtlasError(f"{metadata['id']} {mode}: fixture did not return JSON") from exc
    if not isinstance(decoded, dict):
        raise AtlasError(f"{metadata['id']} {mode}: fixture result must be an object")
    if (
        decoded.get("pattern_id") != metadata["id"]
        or decoded.get("mode") != mode
        or decoded.get("status") != "pass"
    ):
        raise AtlasError(f"{metadata['id']} {mode}: malformed or unsuccessful result")
    evidence = decoded.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise AtlasError(f"{metadata['id']} {mode}: evidence must be a non-empty object")
    return {
        "pattern_id": metadata["id"],
        "mode": mode,
        "status": "pass",
        "evidence": evidence,
    }


def run(
    pattern_id: str | None = None,
    mode: str = "all",
    *,
    validate_collection: bool = True,
) -> list[FixtureResult]:
    if validate_collection:
        errors = validate()
        if errors:
            raise AtlasError("collection validation failed:\n- " + "\n- ".join(errors))
    patterns = load_patterns()
    if pattern_id:
        patterns = [item for item in patterns if item["metadata"]["id"] == pattern_id]
        if not patterns:
            raise AtlasError(f"unknown pattern: {pattern_id}")
        if patterns[0]["metadata"]["status"] != "executable":
            raise AtlasError(f"pattern is documented but not executable: {pattern_id}")
    else:
        patterns = [item for item in patterns if item["metadata"]["status"] == "executable"]
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
.result-count,.empty-state{color:var(--muted)}.empty-state{padding:24px 0}.skip-link{position:absolute;left:12px;top:-60px;background:var(--ink);color:var(--bg);padding:10px 14px;border-radius:8px;z-index:2}.skip-link:focus{top:12px}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px}footer{margin-top:48px;padding-top:24px;border-top:1px solid var(--line);color:var(--muted)}@media(prefers-reduced-motion:no-preference){.card{transition:.15s ease}}@media(max-width:400px){main{padding:42px 16px}h1{font-size:2.35rem}.controls input,.controls select{min-width:0;width:100%}.grid{grid-template-columns:minmax(0,1fr)}}
""".strip()


def _page(title: str, content: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Executable failure patterns for autonomous coding-agent systems."><meta name="theme-color" content="#0b1020">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="Reproduce, detect, and prevent autonomous coding-agent failures.">
<meta property="og:image" content="https://korovin-aa97.github.io/fleet-failure-atlas/assets/social-preview.png"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><title>{html.escape(title)}</title>
<style>{STYLE}</style></head><body><a class="skip-link" href="#main">Skip to content</a><main id="main">{content}<footer><a href="{prefix}index.html">Fleet Failure Atlas</a> · <a href="https://github.com/korovin-aa97/fleet-failure-atlas">GitHub</a> · MIT licensed</footer></main></body></html>
"""


def site_files() -> dict[Path, str]:
    entries: list[SiteEntry] = []
    files: dict[Path, str] = {}
    for pattern in load_patterns():
        metadata = pattern["metadata"]
        entry: SiteEntry = {
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
        files[Path("patterns") / f"{metadata['slug']}.html"] = _page(metadata["title"], body, "../")

    data = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    card_items: list[str] = []
    for entry in entries:
        search_value = " ".join(
            [
                str(entry["title"]),
                entry["id"],
                entry["provenance"],
                entry["status"],
                *entry["symptoms"],
                *entry["lifecycle"],
                *entry["architectures"],
            ]
        ).lower()
        primary_stage = entry["lifecycle"][0]
        stage_value = "|".join(entry["lifecycle"])
        tags = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in entry["symptoms"])
        card_items.append(
            f'<a class="card" data-search="{html.escape(search_value)}" '
            f'data-stages="{html.escape(stage_value)}" href="patterns/{entry["slug"]}.html">'
            f'<span class="eyebrow">{entry["id"]} · {html.escape(primary_stage)}</span>'
            f"<h2>{html.escape(entry['title'])}</h2>"
            f'<p class="meta">{html.escape(entry["provenance"])} provenance</p>'
            f"{tags}</a>"
        )
    cards = "\n".join(card_items)
    stages = sorted({stage for entry in entries for stage in entry["lifecycle"]})
    options = "".join(
        f'<option value="{html.escape(stage)}">{html.escape(stage)}</option>' for stage in stages
    )
    script = """<script>const q=document.querySelector('#q'),stage=document.querySelector('#stage'),cards=[...document.querySelectorAll('.card')],count=document.querySelector('#result-count'),empty=document.querySelector('#empty-state');function filter(){const term=q.value.trim().toLowerCase();let visible=0;cards.forEach(c=>{const match=c.dataset.search.includes(term)&&(!stage.value||c.dataset.stages.split('|').includes(stage.value));c.hidden=!match;if(match)visible++});count.textContent=`${visible} pattern${visible===1?'':'s'}`;empty.hidden=visible!==0}q.addEventListener('input',filter);stage.addEventListener('change',filter);</script>"""
    content = f"""<p class="eyebrow">Reproduce · detect · prevent</p><h1>Failures become useful when they become executable.</h1><p class="lede">A clean-room field guide to autonomous coding-agent failures. Every entry includes a bounded fixture, deterministic detector, repair invariant, and regression proof.</p><div class="controls"><input id="q" type="search" aria-label="Search patterns" placeholder="Search symptoms, systems, IDs, or titles…"><select id="stage" aria-label="Filter by lifecycle"><option value="">All lifecycle stages</option>{options}</select></div><p id="result-count" class="result-count" role="status" aria-live="polite">{len(entries)} patterns</p><p id="empty-state" class="empty-state" hidden>No patterns match these filters.</p><section class="grid" aria-label="Failure patterns">{cards}</section>{script}"""
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate pattern schema and local links")
    subparsers.add_parser("safety", help="scan publishable content for secrets and private markers")
    run_parser = subparsers.add_parser("run", help="run one or all executable patterns")
    run_parser.add_argument("pattern_id", nargs="?", help="stable ID such as FFA-001")
    run_parser.add_argument(
        "--mode", choices=("reproduce", "detect", "regress", "all"), default="all"
    )
    site_parser = subparsers.add_parser("build-site", help="generate the static atlas")
    site_parser.add_argument(
        "--check", action="store_true", help="fail when checked-in output has drifted"
    )
    subparsers.add_parser("check", help="run every release gate")
    args = parser.parse_args()

    try:
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
            results = run(validate_collection=False)
            _fail_if(
                (f"generated site drift: {path}" for path in build_site(check=True)),
                "site check",
            )
            print(
                f"Release gates passed: {len(load_patterns())} patterns, "
                f"{len(results)} fixture checks."
            )
    except AtlasError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
