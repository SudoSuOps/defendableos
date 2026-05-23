"""Tiny .env loader for the edge-agent CLI · zero dependencies.

Looks up MOONSHOT_API_KEY / OPENAI_API_KEY / etc. in:
  1. Process environment (highest priority)
  2. `.env` in the platform repo root (defendableos/.env) if discoverable
  3. `.env` in the CWD

Never logs values. Never serializes to disk. Pure read-only.
"""
from __future__ import annotations

import os
from pathlib import Path


_LOADED_FROM: list[Path] = []


def _candidate_env_paths() -> list[Path]:
    here = Path(__file__).resolve()
    candidates: list[Path] = []
    # Walk up from this file looking for `defendableos/.env`
    for parent in [here.parent] + list(here.parents):
        env = parent / ".env"
        if env.is_file():
            candidates.append(env)
        # Stop at the repo root
        if (parent / "services").is_dir() and (parent / "docs").is_dir():
            break
    # Also check CWD
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file() and cwd_env not in candidates:
        candidates.append(cwd_env)
    return candidates


def _parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    k, _, v = line.partition("=")
    k = k.strip()
    v = v.strip().strip('"').strip("'")
    if not k:
        return None
    return k, v


def get(name: str, default: str | None = None) -> str | None:
    """Return value of env var · checks os.environ first, then .env files."""
    if name in os.environ and os.environ[name]:
        return os.environ[name]
    for path in _candidate_env_paths():
        try:
            for line in path.read_text().splitlines():
                parsed = _parse_env_line(line)
                if parsed is None:
                    continue
                k, v = parsed
                if k == name and v:
                    if path not in _LOADED_FROM:
                        _LOADED_FROM.append(path)
                    return v
        except (OSError, UnicodeDecodeError):
            continue
    return default


def loaded_from() -> list[str]:
    """Return list of .env paths consulted · for transparency in receipts."""
    return [str(p) for p in _LOADED_FROM]
