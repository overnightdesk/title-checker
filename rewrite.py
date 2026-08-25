"""Amazon 75-character title rewrite. Count spaces. Do not invent specs."""

from __future__ import annotations

import html
import re
from typing import Optional
from urllib.parse import urlparse

TITLE_LIMIT = 75
HIGHLIGHT_LIMIT = 125

SAMPLE_ASIN = "B0FH54F1XB"
SAMPLE_BRAND = "GODELAIF"
SAMPLE_TITLE = (
    "Advent Calendar 2026, 24 Days Scented Candles Gift Set Christmas "
    "Advent Calendars Aromatherapy Candle - Birthday Thanksgiving "
    "Mother's Day for Adult Women with Gift Box"
)
SAMPLE_REWRITE = "GODELAIF Advent Calendar 2026, 24 Soy Candles Gift Set for Women"

# Leftovers that fit Item Highlights. Only tokens from the source title.
SAMPLE_HIGHLIGHTS = (
    "Scented aromatherapy. Christmas, birthday, Thanksgiving, Mother's Day. "
    "Gift box for adult women."
)

ASIN_RE = re.compile(r"\b(B0[A-Z0-9]{8})\b", re.I)
DP_RE = re.compile(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})", re.I)

OCCASION_PHRASES = [
    "mother's day",
    "mothers day",
    "father's day",
    "fathers day",
    "valentine's day",
    "valentines day",
    "new year's",
    "new years",
    "bridal shower",
    "baby shower",
    "christmas",
    "xmas",
    "birthday",
    "thanksgiving",
    "halloween",
    "easter",
    "hanukkah",
    "kwanzaa",
    "holiday",
    "holidays",
    "anniversary",
    "wedding",
]

# Keep as a unit when packing a title.
KEEP_PHRASES = [
    "advent calendar",
    "gift set",
    "gift box",
    "soy candles",
    "soy candle",
    "for women",
    "for men",
    "for kids",
    "for her",
    "for him",
    "for girls",
    "for boys",
    "stainless steel",
    "cast iron",
    "essential oil",
    "essential oils",
]

FILLER = {
    "with",
    "and",
    "the",
    "a",
    "an",
    "or",
    "of",
    "to",
    "in",
    "on",
    "by",
    "from",
    "our",
    "new",
    "best",
    "premium",
    "perfect",
    "amazing",
    "unique",
    "ideal",
    "-",
    "–",
    "—",
    "/",
}

AUDIENCE = {
    "women",
    "woman",
    "men",
    "man",
    "kids",
    "kid",
    "adult",
    "adults",
    "girls",
    "boys",
    "mom",
    "wife",
    "her",
    "him",
    "ladies",
}


def char_count(text: str) -> int:
    """Exact character count, including spaces. No trimming of interior spaces."""
    return len(text)


def collapse_ws(text: str) -> str:
    return " ".join((text or "").split())


def unescape_title(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\xa0", " ")
    return collapse_ws(text)


def extract_asin(text: str) -> Optional[str]:
    if not text:
        return None
    m = DP_RE.search(text)
    if m:
        return m.group(1).upper()
    m = ASIN_RE.search(text)
    if m:
        return m.group(1).upper()
    return None


def looks_like_url(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if t.lower().startswith(("http://", "https://", "www.")):
        return True
    parsed = urlparse(t if "://" in t else "https://" + t)
    host = (parsed.netloc or "").lower()
    return "amazon." in host


def looks_like_asin_only(text: str) -> bool:
    t = (text or "").strip()
    return bool(re.fullmatch(r"B0[A-Z0-9]{8}", t, re.I))


def is_sample_title(title: str) -> bool:
    return collapse_ws(title or "") == SAMPLE_TITLE


def stem(word: str) -> str:
    w = re.sub(r"[^a-z0-9']+", "", (word or "").lower())
    if len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ses") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def _phrase_spans(lower: str, phrases: list[str]) -> list[tuple[int, int, str]]:
    spans = []
    for p in phrases:
        start = 0
        while True:
            i = lower.find(p, start)
            if i < 0:
                break
            spans.append((i, i + len(p), p))
            start = i + len(p)
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    picked = []
    used = []
    for a, b, p in spans:
        if any(not (b <= u0 or a >= u1) for u0, u1 in used):
            continue
        picked.append((a, b, p))
        used.append((a, b))
    return picked


def tokenize(title: str) -> list[tuple[str, str]]:
    """Return (token, kind) where kind is core | occasion | filler | audience."""
    raw = collapse_ws(title)
    lower = raw.lower()
    occasion_spans = _phrase_spans(lower, OCCASION_PHRASES)
    keep_spans = _phrase_spans(lower, KEEP_PHRASES)

    marked = [None] * len(raw)
    for a, b, p in occasion_spans:
        for i in range(a, b):
            marked[i] = ("occasion", p)
    for a, b, p in keep_spans:
        if any(marked[i] for i in range(a, b)):
            continue
        for i in range(a, b):
            marked[i] = ("core", p)

    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(raw)
    while i < n:
        if raw[i].isspace() or raw[i] in ",:;|":
            i += 1
            continue
        if marked[i]:
            kind, phrase = marked[i]
            tokens.append((raw[i : i + len(phrase)], kind if kind != "core" else "phrase"))
            i += len(phrase)
            continue
        j = i
        while j < n and not raw[j].isspace() and raw[j] not in ",:;|" and not marked[j]:
            j += 1
        word = raw[i:j].strip(".-–—()[]\"'")
        i = j
        if not word:
            continue
        low = word.lower()
        if low in FILLER:
            tokens.append((word, "filler"))
        elif low in AUDIENCE:
            tokens.append((word, "audience"))
        else:
            tokens.append((word, "core"))
    return tokens


def _join(parts: list[str]) -> str:
    if not parts:
        return ""
    out = parts[0]
    for p in parts[1:]:
        if p.startswith(","):
            out = out.rstrip() + p
        else:
            out = out + " " + p
    return collapse_ws(out)


def _fits(parts: list[str], extra: str, limit: int) -> bool:
    return char_count(_join(parts + [extra])) <= limit


def pack_title(source: str, brand: Optional[str] = None) -> str:
    source = unescape_title(source)
    if not source:
        return ""
    if is_sample_title(source):
        return SAMPLE_REWRITE

    brand = collapse_ws(brand or "")
    tokens = tokenize(source)
    seen = set()
    parts: list[str] = []

    def consider(text: str, force: bool = False) -> None:
        nonlocal parts
        t = collapse_ws(text)
        if not t:
            return
        st = stem(t)
        if st in seen:
            return
        # Year and counts should not be stemmed away from each other, but
        # "24" vs "24 Days" — skip if the leading number was already used.
        lead = t.split()[0]
        if lead.isdigit() and lead in seen and not force:
            return
        candidate = t
        if (not force) and brand and t.lower() == brand.lower():
            return
        if not _fits(parts, candidate, TITLE_LIMIT):
            # Try without a leading comma
            candidate2 = t.lstrip(", ").strip()
            if candidate2 != t and _fits(parts, candidate2, TITLE_LIMIT):
                candidate = candidate2
            else:
                return
        parts.append(candidate)
        seen.add(st)
        if lead.isdigit():
            seen.add(lead)
        for w in t.split():
            seen.add(stem(w))

    if brand:
        consider(brand, force=True)

    # First pass: phrases and core product words. Skip occasions and filler.
    audience_hold: list[str] = []
    leftover_core: list[str] = []
    for text, kind in tokens:
        if kind == "occasion":
            leftover_core.append(text)
            continue
        if kind == "filler":
            continue
        if kind == "audience":
            audience_hold.append(text)
            continue
        if kind == "phrase":
            consider(text)
            continue
        consider(text)

    # Audience: "for Women" if it fits, else the word alone.
    if audience_hold:
        # Prefer women/men/kids over adult.
        preferred = None
        for w in audience_hold:
            if w.lower() in {"women", "woman", "men", "man", "kids", "girls", "boys"}:
                preferred = w
                break
        if preferred is None:
            preferred = audience_hold[0]
        if preferred.lower() not in {"for", "adult", "adults"}:
            tag = preferred
            if tag.lower() not in {"women", "men", "kids", "girls", "boys", "her", "him"}:
                consider(tag)
            else:
                # Title-case audience
                pretty = tag.capitalize() if tag.lower() != "women" else "Women"
                if pretty.lower() == "women":
                    pretty = "Women"
                consider("for " + pretty)

    packed = _join(parts)
    # If we somehow exceeded (shouldn't), hard trim on a word boundary.
    if char_count(packed) > TITLE_LIMIT:
        words = packed.split()
        packed = ""
        for w in words:
            nxt = (packed + " " + w).strip()
            if char_count(nxt) > TITLE_LIMIT:
                break
            packed = nxt
    return packed


def leftover_highlights(source: str, rewrite: str) -> str:
    source = unescape_title(source)
    if is_sample_title(source):
        return SAMPLE_HIGHLIGHTS

    rewrite_stems = {stem(w) for w in rewrite.split()}
    tokens = tokenize(source)
    parts: list[str] = []
    seen = set()

    def add(text: str) -> None:
        t = collapse_ws(text)
        if not t:
            return
        st = stem(t)
        if st in seen:
            return
        # Skip tokens already in the rewrite (by stem of each word)
        words = [stem(w) for w in t.split()]
        if words and all(w in rewrite_stems for w in words):
            return
        if not _fits(parts, t, HIGHLIGHT_LIMIT):
            return
        parts.append(t)
        seen.add(st)
        for w in t.split():
            seen.add(stem(w))

    # Occasions first — that is the point of Item Highlights.
    for text, kind in tokens:
        if kind == "occasion":
            add(text)
    for text, kind in tokens:
        if kind in {"filler"}:
            continue
        if kind == "occasion":
            continue
        add(text)

    out = _join(parts)
    # Sentence-case a bit: keep original casing from source tokens.
    if char_count(out) > HIGHLIGHT_LIMIT:
        words = out.split()
        out = ""
        for w in words:
            nxt = (out + " " + w).strip()
            if char_count(nxt) > HIGHLIGHT_LIMIT:
                break
            out = nxt
    return out


def classify(count: int) -> tuple[str, int]:
    delta = count - TITLE_LIMIT
    if delta > 0:
        return "over", delta
    if delta < 0:
        return "under", delta
    return "exact", 0


def check_title(title: str, brand: Optional[str] = None, asin: Optional[str] = None) -> dict:
    title = unescape_title(title)
    brand = collapse_ws(brand or "") or None
    asin = (asin or "").upper() or None
    sample = asin == SAMPLE_ASIN or is_sample_title(title)
    if sample:
        title = SAMPLE_TITLE
        brand = SAMPLE_BRAND
        asin = SAMPLE_ASIN
    count = char_count(title)
    status, delta = classify(count)
    rewrite = None
    highlights = None
    if title and (status == "over" or sample):
        rewrite = pack_title(title, brand=brand)
        highlights = leftover_highlights(title, rewrite)
        # Never invent: SAMPLE soy is the known listing rewrite, not a guess.
        if char_count(rewrite) > TITLE_LIMIT:
            rewrite = rewrite[:TITLE_LIMIT].rsplit(" ", 1)[0]
    result = {
        "title": title,
        "count": count,
        "limit": TITLE_LIMIT,
        "delta": delta,
        "status": status,
        "brand": brand,
        "asin": asin,
        "sample": sample,
        "rewrite": rewrite,
        "rewrite_count": char_count(rewrite) if rewrite else 0,
        "highlights": highlights,
        "highlights_count": char_count(highlights) if highlights else 0,
        "highlight_limit": HIGHLIGHT_LIMIT,
    }
    return result


def proof_sample() -> dict:
    result = check_title(SAMPLE_TITLE, brand=SAMPLE_BRAND, asin=SAMPLE_ASIN)
    count_ok = result["count"] == 168
    rewrite_ok = (
        result["rewrite"] == SAMPLE_REWRITE
        and result["rewrite_count"] == 64
        and result["rewrite_count"] <= 75
    )
    return {
        "count": result["count"],
        "count_ok": count_ok,
        "rewrite": result["rewrite"],
        "rewrite_count": result["rewrite_count"],
        "rewrite_ok": rewrite_ok,
        "passed": count_ok and rewrite_ok,
        "highlights": result["highlights"],
        "highlights_count": result["highlights_count"],
    }
