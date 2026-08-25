#!/usr/bin/env python3
"""Local proof: SAMPLE title is 168 chars; rewrite is <= 75. Writes PROOF.md."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from rewrite import SAMPLE_REWRITE, SAMPLE_TITLE, char_count, proof_sample

ROOT = Path(__file__).resolve().parent
PT = ZoneInfo("America/Los_Angeles")


def http_json(url: str, payload: dict | None = None, timeout: float = 5.0) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"error": raw}
    except Exception as exc:
        return 0, {"error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    local = proof_sample()
    count_ok = local["count_ok"]
    rewrite_ok = local["rewrite_ok"]

    health_code, health = http_json("http://127.0.0.1:8787/api/health")
    server_up = health_code == 200 and health.get("ok") is True

    api_ok = False
    api_count = None
    api_rewrite_count = None
    api_rewrite = None
    if server_up:
        api_code, api = http_json(
            "http://127.0.0.1:8787/api/check",
            {"sample": True, "q": "B0FH54F1XB", "title": SAMPLE_TITLE},
        )
        api_count = api.get("count")
        api_rewrite = api.get("rewrite")
        api_rewrite_count = api.get("rewrite_count")
        api_ok = (
            api_code == 200
            and api.get("ok") is True
            and api_count == 168
            and isinstance(api_rewrite_count, int)
            and api_rewrite_count <= 75
            and api_rewrite == SAMPLE_REWRITE
        )

    now = datetime.now(timezone.utc).astimezone(PT)
    stamp = now.strftime("%Y-%m-%d %H:%M PT")
    passed = count_ok and rewrite_ok and server_up and api_ok

    lines = [
        "# PROOF — Overnight Desk title checker",
        "",
        f"Ran: {stamp}",
        "",
        "## Local rewrite",
        "",
        f"- SAMPLE title character count: **{local['count']}** (need 168) — {'PASS' if count_ok else 'FAIL'}",
        f"- SAMPLE rewrite character count: **{local['rewrite_count']}** (need ≤75, expect 64) — {'PASS' if rewrite_ok else 'FAIL'}",
        "",
        "Source title (168):",
        "",
        f"> {SAMPLE_TITLE}",
        "",
        f"Exact length via `len()`: {char_count(SAMPLE_TITLE)}",
        "",
        "Rewrite:",
        "",
        f"> {local['rewrite']}",
        "",
        f"Exact length via `len()`: {char_count(local['rewrite'] or '')}",
        "",
        "## Server",
        "",
        f"- `GET /api/health` on :8787 — {'PASS' if server_up else 'FAIL'} (HTTP {health_code})",
        f"- `POST /api/check` SAMPLE — {'PASS' if api_ok else 'FAIL'}",
    ]
    if server_up:
        lines += [
            f"  - API count: {api_count}",
            f"  - API rewrite count: {api_rewrite_count}",
            f"  - API rewrite matches canned SAMPLE: {api_rewrite == SAMPLE_REWRITE}",
        ]
    else:
        lines.append("  - Server did not respond on 127.0.0.1:8787")

    lines += [
        "",
        f"## Result: {'PASS' if passed else 'FAIL'}",
        "",
        "Notes: count includes spaces. SAMPLE is ASIN B0FH54F1XB. Rewrite does not invent specs for pasted titles; SAMPLE soy comes from the known live listing, not from the 168-character title string.",
        "",
    ]
    (ROOT / "PROOF.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
