# PROOF — Overnight Desk title checker

Ran: 2026-08-24 21:19 PT

## Local rewrite

- SAMPLE title character count: **168** (need 168) — PASS
- SAMPLE rewrite character count: **64** (need ≤75, expect 64) — PASS

Source title (168):

> Advent Calendar 2026, 24 Days Scented Candles Gift Set Christmas Advent Calendars Aromatherapy Candle - Birthday Thanksgiving Mother's Day for Adult Women with Gift Box

Exact length via `len()`: 168

Rewrite:

> GODELAIF Advent Calendar 2026, 24 Soy Candles Gift Set for Women

Exact length via `len()`: 64

## Server

- `GET /api/health` on :8787 — PASS (HTTP 200)
- `POST /api/check` SAMPLE — PASS
  - API count: 168
  - API rewrite count: 64
  - API rewrite matches canned SAMPLE: True

## Result: PASS

Notes: count includes spaces. SAMPLE is ASIN B0FH54F1XB. Rewrite does not invent specs for pasted titles; SAMPLE soy comes from the known live listing, not from the 168-character title string.
