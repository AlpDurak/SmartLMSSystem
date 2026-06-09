#!/usr/bin/env python3
"""
Smart LMS — one-shot MCP installer.

Registers the smart-lms MCP server into every detected AI coding tool:
  Claude Code, Codex CLI, Gemini CLI, Cursor, Windsurf, Zed, Continue.

Usage:
  python install.py                  # auto-detect repo location
  python install.py --repo /path     # explicit repo path
  python install.py --uninstall      # remove from all tools
"""
import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

import io, sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    try: _sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

def bold(s): return f"\033[1m{s}\033[0m"
def green(s): return f"\033[32m{s}\033[0m"
def yellow(s): return f"\033[33m{s}\033[0m"
def dim(s): return f"\033[2m{s}\033[0m"

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

HOME = Path.home()


# ── MCP entry ─────────────────────────────────────────────────────────────────

def mcp_entry(repo: Path) -> dict:
    return {
        "command": sys.executable,
        "args": ["-m", "smart_lms.server"],
        "cwd": str(repo),
    }


# ── Tool registrations ────────────────────────────────────────────────────────

def install_json_mcpServers(path: Path, repo: Path, uninstall: bool) -> str:
    """Generic handler for tools that use {mcpServers: {name: entry}} JSON."""
    cfg = read_json(path)
    servers = cfg.setdefault("mcpServers", {})
    if uninstall:
        if "smart-lms" in servers:
            del servers["smart-lms"]
            write_json(path, cfg)
            return "removed"
        return "not registered"
    servers["smart-lms"] = mcp_entry(repo)
    write_json(path, cfg)
    return "registered"


def install_zed(path: Path, repo: Path, uninstall: bool) -> str:
    """Zed uses context_servers with a different shape."""
    cfg = read_json(path)
    servers = cfg.setdefault("context_servers", {})
    if uninstall:
        if "smart-lms" in servers:
            del servers["smart-lms"]
            write_json(path, cfg)
            return "removed"
        return "not registered"
    servers["smart-lms"] = {
        "command": {
            "path": sys.executable,
            "args": ["-m", "smart_lms.server"],
            "env": {"PYTHONPATH": str(repo)},
        }
    }
    write_json(path, cfg)
    return "registered"


def install_continue(path: Path, repo: Path, uninstall: bool) -> str:
    """Continue.dev uses mcpServers as a list, not a dict."""
    cfg = read_json(path)
    servers = cfg.setdefault("mcpServers", [])
    existing = next((i for i, s in enumerate(servers) if s.get("name") == "smart-lms"), None)
    if uninstall:
        if existing is not None:
            servers.pop(existing)
            write_json(path, cfg)
            return "removed"
        return "not registered"
    entry = {"name": "smart-lms", **mcp_entry(repo)}
    if existing is not None:
        servers[existing] = entry
    else:
        servers.append(entry)
    write_json(path, cfg)
    return "registered"


# ── Tool catalogue ────────────────────────────────────────────────────────────

def tools(repo: Path):
    """
    Returns list of (display_name, detect_path, config_path, handler).
    detect_path: if this exists, the tool is considered installed.
    config_path: where to write the config (created if absent).
    """
    W = os.name == "nt"
    APPDATA = Path(os.environ.get("APPDATA", HOME / "AppData" / "Roaming"))
    LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", HOME / "AppData" / "Local"))
    XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))

    return [
        (
            "Claude Code",
            HOME / ".claude",
            HOME / ".claude" / "settings.json",
            install_json_mcpServers,
        ),
        (
            "Codex CLI (OpenAI)",
            HOME / ".codex",
            HOME / ".codex" / "config.json",
            install_json_mcpServers,
        ),
        (
            "Gemini CLI",
            HOME / ".gemini",
            HOME / ".gemini" / "settings.json",
            install_json_mcpServers,
        ),
        (
            "Cursor",
            (APPDATA / "Cursor") if W else (HOME / ".config" / "Cursor"),
            (APPDATA / "Cursor" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "mcp_settings.json")
                if W else (HOME / ".cursor" / "mcp.json"),
            install_json_mcpServers,
        ),
        (
            "Windsurf (Codeium)",
            (APPDATA / "Windsurf") if W else (HOME / ".codeium" / "windsurf"),
            (APPDATA / "Windsurf" / "User" / "globalStorage" / "codeium.codeium" / "mcp_config.json")
                if W else (HOME / ".codeium" / "windsurf" / "mcp_config.json"),
            install_json_mcpServers,
        ),
        (
            "Zed",
            (APPDATA / "Zed") if W else (XDG_CONFIG / "zed"),
            (APPDATA / "Zed" / "settings.json") if W else (XDG_CONFIG / "zed" / "settings.json"),
            install_zed,
        ),
        (
            "Continue",
            HOME / ".continue",
            HOME / ".continue" / "config.json",
            install_continue,
        ),
    ]


# ── main ──────────────────────────────────────────────────────────────────────

def install_deps(repo: Path):
    req = repo / "requirements.txt"
    if not req.exists():
        return
    print(bold("  Installing Python dependencies…"))
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
        stderr=subprocess.DEVNULL,
    )
    print(green("  [ok] dependencies installed"))


SKILL_MD = """\
---
name: smart-lms
description: Launch a browser-based LMS study assistant. The agent teaches,
  quizzes, and examines using the student's Moodle course materials, Google
  Drive, and NotebookLM as sources. Output is rendered as flashcards, quiz
  cards, summaries, and mock exams.
trigger: /smart-lms
---

# Smart LMS Skill

You are a student study assistant. When this skill is invoked, follow the
boot sequence and then run the study loop.

## MCP Server

This skill requires the smart-lms MCP server. It must be registered in
your tool's MCP settings pointing to:
  python -m smart_lms.server
from the SmartLMSSystem repo directory.

## Boot Sequence

1. Call `start_ui()` — launches the browser UI and returns
   `{session_id, url, port}`. Save `session_id` for the rest of the session.
2. Call `list_courses()` to confirm LMS credentials are working.
   If the result is empty, tell the user: "Your LMS credentials are not set.
   Call setup_lms_credentials(username, password) to configure them."
3. Call `create_session(title="New session", course="")` to start
   persisting this conversation.

## Study Loop (repeat until user closes the browser or says goodbye)

### Step 1 — Wait for user input
Call `wait_for_prompt(session_id)`.
Returns: `{text, course_ids, doc_ids, drive_files}`

### Step 2 — Gather sources
For each selected course_id, call `get_material_text(course_id, doc_ids)`
to get `[{title, text}]`. Concatenate all text as `<SOURCE_TEXT>`.

### Step 3 — Interpret intent and generate card blocks

Use `<SOURCE_TEXT>` as the knowledge base. Do NOT make up facts.

- "teach me X" / "explain X": 4-8 flashcards + 1 summary block
- "quiz me" / "test me" / "examine me": 1 quiz block + 1 exam block
- "summarize X": 1 summary block only
- Other: reply in prose

### Step 4 — Render and persist

Call `render(session_id, blocks)` to push card blocks to the browser.
Call `save_turn(session_id, "user", <user text>, <source list>, null)`
Call `save_turn(session_id, "assistant", <prose reply>, [], blocks)`

Go back to Step 1.
"""


def install_skill(repo: Path, uninstall: bool):
    """Copy SKILL.md to Claude Code, Codex, and Gemini skill directories."""
    skill_file = repo / "smart_lms" / "skill" / "SKILL.md"
    # Use bundled skill content (no file dependency)
    content = SKILL_MD

    targets = [
        ("Claude Code skill", HOME / ".claude" / "skills" / "smart-lms" / "SKILL.md"),
        ("Codex CLI skill",   HOME / ".codex"  / "skills" / "smart-lms" / "SKILL.md"),
    ]

    for label, dest in targets:
        if uninstall:
            if dest.exists():
                dest.unlink()
                print(f"  {green('ok')} {label} removed")
            else:
                print(f"  {dim('--')} {label} (not installed)")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"  {green('ok')} {label}")
            print(dim(f"    {dest}"))

    # Gemini CLI — append/remove skill block in ~/.gemini/GEMINI.md
    gemini_md = HOME / ".gemini" / "GEMINI.md"
    marker_start = "# [smart-lms skill]"
    marker_end   = "# [/smart-lms skill]"

    if (HOME / ".gemini").exists():
        existing = gemini_md.read_text(encoding="utf-8") if gemini_md.exists() else ""
        if uninstall:
            if marker_start in existing:
                start = existing.index(marker_start)
                end   = existing.index(marker_end) + len(marker_end)
                gemini_md.write_text(
                    (existing[:start] + existing[end:]).strip() + "\n",
                    encoding="utf-8",
                )
                print(f"  {green('ok')} Gemini CLI skill removed")
            else:
                print(f"  {dim('--')} Gemini CLI skill (not installed)")
        else:
            block = f"\n{marker_start}\n{content}\n{marker_end}\n"
            if marker_start in existing:
                start = existing.index(marker_start)
                end   = existing.index(marker_end) + len(marker_end)
                new = existing[:start] + block.strip() + existing[end:]
            else:
                new = existing + block
            gemini_md.parent.mkdir(parents=True, exist_ok=True)
            gemini_md.write_text(new, encoding="utf-8")
            print(f"  {green('ok')} Gemini CLI skill")
            print(dim(f"    {gemini_md}"))


def main():
    parser = argparse.ArgumentParser(description="Smart LMS MCP installer")
    parser.add_argument("--repo", type=Path,
                        default=Path(__file__).parent.resolve(),
                        help="Path to the SmartLMSSystem repo")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove smart-lms from all tools")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Skip pip install")
    args = parser.parse_args()

    repo = args.repo.resolve()
    action = "Uninstalling" if args.uninstall else "Installing"

    print()
    print(bold(f"  Smart LMS MCP — {action}"))
    print(dim(f"  repo: {repo}"))
    print()

    if not args.uninstall and not args.skip_deps:
        install_deps(repo)
        print()

    registered = []
    skipped = []

    for name, detect, cfg_path, handler in tools(repo):
        if not detect.exists():
            skipped.append(name)
            continue
        result = handler(cfg_path, repo, args.uninstall)
        verb = {"registered": "ok", "removed": "ok", "not registered": "--"}[result]
        color = green if result in ("registered", "removed") else dim
        print(f"  {color(verb)} {name} MCP")
        print(dim(f"    {cfg_path}"))
        registered.append(name)

    print()
    print(bold("  Skills:"))
    install_skill(repo, args.uninstall)

    print()
    if registered:
        print(bold(f"  {action} complete for: {', '.join(registered)}"))
    if skipped:
        print(dim(f"  Skipped (not installed): {', '.join(skipped)}"))

    if not args.uninstall:
        print()
        print(bold("  Next steps:"))
        print("  1. Reload / restart your AI coding tool")
        print("  2. Set your Moodle credentials once:")
        print(dim('     call setup_lms_credentials("your@email.com", "password")'))
        print("  3. Type  /smart-lms  to launch the study UI")
        print()


if __name__ == "__main__":
    main()
