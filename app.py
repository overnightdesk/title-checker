#!/usr/bin/env python3
"""Overnight Desk — Amazon 75-character title checker. Bind 0.0.0.0:8787."""

from __future__ import annotations

import html as htmlmod
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, make_response, render_template, request, send_from_directory

from rewrite import (
    SAMPLE_ASIN,
    SAMPLE_BRAND,
    SAMPLE_REWRITE,
    SAMPLE_TITLE,
    TITLE_LIMIT,
    check_title,
    extract_asin,
    looks_like_asin_only,
    looks_like_url,
    proof_sample,
    unescape_title,
)

ROOT = Path(__file__).resolve().parent
FIVERR_URL = (
    "https://www.fiverr.com/overnight_desk/"
    "rewrite-amazon-75-char-titles-or-etsy-holiday-listing-copy"
)

app = Flask(
    __name__,
    static_folder=str(ROOT / "static"),
    template_folder=str(ROOT / "templates"),
)
app.secret_key = "overnight-desk-title-app-local"
app.config["JSON_SORT_KEYS"] = False

FETCH_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
TITLE_SPAN_RE = re.compile(
    r'id=["\']productTitle["\'][^>]*>(.*?)</span>', re.I | re.S
)
OG_TITLE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
BRAND_RE = re.compile(
    r'id=["\']bylineInfo["\'][^>]*>\s*(.*?)</a>', re.I | re.S
)
VISIT_STORE_RE = re.compile(r"^\s*(?:visit the\s+(.+?)\s+store|brand:\s*(.+))\s*$", re.I)


def _paywall_from_cookie() -> tuple[int, bool]:
    try:
        n = int(request.cookies.get("od_rewrites", "0"))
    except ValueError:
        n = 0
    return n, n >= 1


def fetch_amazon(asin: str) -> dict:
    """Best-effort public page fetch. Amazon often blocks datacenter IPs."""
    url = f"https://www.amazon.com/dp/{asin}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": FETCH_UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read(2_000_000)
            page = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        return {"error": f"Amazon fetch failed ({type(exc).__name__}). Paste the title."}

    low = page.lower()
    if "captcha" in low and "producttitle" not in low:
        return {"error": "Amazon served a captcha. Paste the title."}

    title = None
    m = TITLE_SPAN_RE.search(page)
    if m:
        title = unescape_title(re.sub(r"<[^>]+>", "", m.group(1)))
    if not title:
        m = OG_TITLE_RE.search(page)
        if m:
            title = unescape_title(htmlmod.unescape(m.group(1)))
            # og:title often appends ": Amazon.com"
            title = re.sub(r"\s*[:\-–]\s*Amazon\.com.*$", "", title, flags=re.I)

    if not title:
        return {"error": "Could not read the title from Amazon HTML. Paste the title."}

    brand = None
    bm = BRAND_RE.search(page)
    if bm:
        blob = unescape_title(re.sub(r"<[^>]+>", " ", bm.group(1)))
        vm = VISIT_STORE_RE.match(blob)
        if vm:
            brand = (vm.group(1) or vm.group(2) or "").strip()
        elif blob.lower().startswith("brand:"):
            brand = blob.split(":", 1)[1].strip()
        else:
            brand = blob.strip() or None
        if brand:
            brand = re.sub(r"\s+Store$", "", brand, flags=re.I).strip()

    return {"title": title, "brand": brand, "url": url}


@app.get("/")
def index():
    return render_template(
        "index.html",
        fiverr_url=FIVERR_URL,
        sample_asin=SAMPLE_ASIN,
        sample_title=SAMPLE_TITLE,
        sample_rewrite=SAMPLE_REWRITE,
        title_limit=TITLE_LIMIT,
    )


@app.get("/health")
@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "overnight-desk-title", "port": 8787})


@app.get("/api/proof")
def api_proof():
    p = proof_sample()
    p["ok"] = p["passed"]
    return jsonify(p), (200 if p["passed"] else 500)


@app.post("/api/check")
def api_check():
    body = request.get_json(silent=True) or {}
    q = (body.get("q") or request.form.get("q") or "").strip()
    pasted = (body.get("title") or request.form.get("title") or "").strip()
    sample_flag = bool(body.get("sample"))

    asin = extract_asin(q) or extract_asin(pasted)
    if sample_flag:
        asin = SAMPLE_ASIN

    used, show_paywall = _paywall_from_cookie()
    source = "paste"
    fetch_error = None
    brand = None
    title = unescape_title(pasted) if pasted else ""

    if asin == SAMPLE_ASIN and not title:
        title = SAMPLE_TITLE
        brand = SAMPLE_BRAND
        source = "sample"
    elif title:
        source = "paste"
    elif asin and (looks_like_url(q) or looks_like_asin_only(q) or looks_like_url(q) or asin):
        fetched = fetch_amazon(asin)
        if fetched.get("title"):
            title = fetched["title"]
            brand = fetched.get("brand")
            source = "fetch"
        else:
            fetch_error = fetched.get("error") or "Amazon fetch failed. Paste the title."
            source = "blocked"
    elif q and not looks_like_url(q) and not looks_like_asin_only(q):
        title = unescape_title(q)
        source = "paste"
    elif q:
        asin = extract_asin(q)
        if asin:
            fetched = fetch_amazon(asin)
            if fetched.get("title"):
                title = fetched["title"]
                brand = fetched.get("brand")
                source = "fetch"
            else:
                fetch_error = fetched.get("error") or "Amazon fetch failed. Paste the title."
                source = "blocked"

    if not title:
        resp = jsonify(
            {
                "ok": False,
                "error": fetch_error
                or "Paste an Amazon URL, an ASIN, or the title itself.",
                "asin": asin,
                "source": source,
                "need_title": True,
                "paywall": show_paywall,
            }
        )
        return resp, 200

    result = check_title(title, brand=brand, asin=asin)
    if result["sample"]:
        source = "sample"

    gave_rewrite = bool(result.get("rewrite"))
    if gave_rewrite:
        show_paywall = True
        used = max(used, 1)

    payload = {
        "ok": True,
        "source": source,
        "fetch_error": fetch_error,
        "need_title": False,
        "paywall": show_paywall,
        "fiverr": FIVERR_URL,
        "prices": {
            "one": 100,
            "amazon5": 150,
            "etsy10": 200,
        },
        **result,
    }
    resp = make_response(jsonify(payload), 200)
    if gave_rewrite:
        resp.set_cookie("od_rewrites", str(used), max_age=60 * 60 * 24 * 30, samesite="Lax")
    return resp


@app.get("/static/<path:name>")
def static_files(name: str):
    return send_from_directory(app.static_folder, name)


def main() -> None:
    print(
        f"Overnight Desk title checker  http://0.0.0.0:8787  "
        f"{datetime.now(timezone.utc).isoformat()}",
        flush=True,
    )
    app.run(host="0.0.0.0", port=8787, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
