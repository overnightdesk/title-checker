# Amazon 75-character title checker

Overnight Desk tool. Count an Amazon title, including spaces. 75 is the cap. If it is over, get one brand-first rewrite and leftover keywords for the 125-character Item Highlights field.

We never log into seller accounts. No ranking promises.

## Run

From this directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

The server binds `0.0.0.0:8787`. Open http://127.0.0.1:8787

If the venv already exists, skip the first two lines.

## Use

Paste an Amazon URL, an ASIN, or the title itself. Check.

Amazon often blocks HTML fetch from a server. If fetch fails, paste the title. Count and rewrite still work.

First check is free. After one rewrite, the page shows a Fiverr order link.

- $100 — one listing
- $150 — 5 Amazon ASINs
- $200 — 10 Etsy listings

Gig: https://www.fiverr.com/overnight_desk/rewrite-amazon-75-char-titles-or-etsy-holiday-listing-copy

## SAMPLE

ASIN `B0FH54F1XB`. Load SAMPLE on the page.

- Source title: 168 characters (over)
- Rewrite: `GODELAIF Advent Calendar 2026, 24 Soy Candles Gift Set for Women` (64/75)

Marked SAMPLE. Public listing. Not applied to any seller account.

Soy is on the live listing; leftover Item Highlights use only words from the source title. The rewriter does not invent specs.

## Proof

```bash
.venv/bin/python proof.py
```

Writes `PROOF.md`. SAMPLE count must be 168. Rewrite must be ≤75.

## API

`POST /api/check` JSON `{ "q": "...", "title": "...", "sample": true }`
`GET /api/health`
`GET /api/proof`
