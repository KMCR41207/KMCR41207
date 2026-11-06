#!/usr/bin/env python3
"""
Finviz-style stock market heatmap for GitHub profile.

Visual goal: DENSE grid of small square/rectangular tiles like Finviz S&P 500,
NOT 19 big horizontal bars. To achieve this with only 19 repos, we split each
repo into multiple tiles by: file count, stars, forks, languages, size buckets.

This creates 80-120 tiles from 19 repos → proper Finviz mosaic appearance.
"""

import html
import json
import math
import os
import random
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ── Config ────────────────────────────────────────────────────────────────────
USER   = "KMCR41207"
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "market-heatmap.svg"

W, H = 1060, 520
SIDEBAR_W = 210
PAD = 6
TICK_H = 22
HEADER_H = 38

HM_X = PAD
HM_Y = HEADER_H + PAD
HM_W = W - SIDEBAR_W - PAD * 2 - 4
HM_H = H - HEADER_H - TICK_H - PAD * 2

# ── Palette ───────────────────────────────────────────────────────────────────
BG = "#0d1117"
HEADER_BG = "#010409"
SIDEBAR_BG = "#010409"
BORDER = "#21262d"

# Bright Finviz greens/reds
GREENS = ["#0a4d0a", "#0f6b0f", "#14891e", "#1aa62e", "#22cc3d", "#2ef04d"]
REDS   = ["#4d0a0a", "#6b0f0f", "#891e1e", "#a62e2e", "#cc3d3d", "#f04d4d"]
NEUTRAL = "#1c2128"

FONT = "ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace"
WHITE = "#e6edf3"
DIM = "#8b949e"
BLUE = "#58a6ff"
YELL = "#e3b341"
GRTXT = "#3fb950"
RDTXT = "#f85149"

# ── GitHub API ────────────────────────────────────────────────────────────────
def _hdr():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "KMCR-heatmap"}
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h

def _get(url):
    try:
        with urlopen(Request(url, headers=_hdr()), timeout=15) as r:
            return json.load(r)
    except Exception as e:
        print(f"  api warn {url}: {e}")
        return None

def fetch_all():
    info = _get(f"https://api.github.com/users/{USER}") or {}
    repos, page = [], 1
    while page <= 5:
        batch = _get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&sort=pushed")
        if not isinstance(batch, list):
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return info, repos

# ── Tile generation (split repos into many tiles) ─────────────────────────────
def make_tiles(repos):
    """
    Generate 80-120+ tiles from repos by creating multiple tiles per repo.
    Strategy: each repo contributes base tiles + language sub-tiles + size buckets.
    """
    tiles = []
    for r in repos:
        if r.get("fork"):
            continue
        name = r.get("name", "")
        lang = r.get("language") or "Code"
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        size_kb = r.get("size", 0)

        # Base weight for this repo
        base_weight = math.log1p(size_kb) * 2 + stars * 5 + forks * 3 + 1.5

        # Activity score
        raw = stars * 4 + forks * 2 + math.log1p(size_kb) * 0.2
        base_score = math.tanh(raw / 10.0)

        # Jitter per repo
        rng = random.Random(hash(name) & 0xFFFFFF)
        jitter = rng.uniform(-0.3, 0.3)

        # ── Strategy 1: Main repo tile ──
        score1 = max(-1.0, min(1.0, base_score + jitter))
        idx1 = min(5, int(abs(score1) * 6))
        color1 = GREENS[idx1] if score1 >= 0 else REDS[idx1]
        metric1 = f"+{stars}★" if stars > 0 else (f"{size_kb//1024}MB" if size_kb > 1024 else f"{size_kb}KB")
        tiles.append(dict(
            label=name.upper()[:12],
            weight=base_weight * 1.5,
            score=score1,
            color=color1,
            metric=metric1,
            lang=lang,
        ))

        # ── Strategy 2: Language sub-tile (if repo has a language) ──
        if lang and lang != "Code":
            score2 = max(-1.0, min(1.0, base_score + jitter * 0.7))
            idx2 = min(5, int(abs(score2) * 6))
            color2 = GREENS[idx2] if score2 >= 0 else REDS[idx2]
            tiles.append(dict(
                label=lang.upper()[:8],
                weight=base_weight * 0.5,
                score=score2,
                color=color2,
                metric=f"{size_kb//100}",
                lang=lang,
            ))

        # ── Strategy 3: Split by size bucket (every repo gets file-type tiles) ──
        # Create 3 sub-tiles per repo: SRC, PKG, DOC
        for i, suffix in enumerate(["SRC", "PKG", "DOC"]):
            jit = jitter + (i - 1.0) * 0.35
            sc = max(-1.0, min(1.0, base_score + jit))
            idx = min(5, int(abs(sc) * 6))
            col = GREENS[idx] if sc >= 0 else REDS[idx]
            tiles.append(dict(
                label=f"{name[:7]}.{suffix[:2]}",
                weight=base_weight * 0.35,
                score=sc,
                color=col,
                metric=f"{size_kb//(i+2)}",
                lang=lang,
            ))

        # ── Strategy 4: Stars bucket (if repo has stars) ──
        if stars > 0:
            sc = base_score + jitter * 1.2
            sc = max(-1.0, min(1.0, sc))
            idx = min(5, int(abs(sc) * 6))
            col = GREENS[idx] if sc >= 0 else REDS[idx]
            tiles.append(dict(
                label=f"★{name[:8]}",
                weight=stars * 6 + base_weight * 0.3,
                score=sc,
                color=col,
                metric=f"+{stars}",
                lang=lang,
            ))

        # ── Strategy 5: Forks bucket (if repo has forks) ──
        if forks > 0:
            sc = base_score + jitter * 0.9
            sc = max(-1.0, min(1.0, sc))
            idx = min(5, int(abs(sc) * 6))
            col = GREENS[idx] if sc >= 0 else REDS[idx]
            tiles.append(dict(
                label=f"⑂{name[:8]}",
                weight=forks * 4 + base_weight * 0.25,
                score=sc,
                color=col,
                metric=f"{forks}F",
                lang=lang,
            ))

    # Sort by weight descending
    tiles.sort(key=lambda t: -t["weight"])
    print(f"  Generated {len(tiles)} tiles from {len([r for r in repos if not r.get('fork')])} repos")
    return tiles[:100]  # cap at 100 for density

# ── Grid-based layout (not treemap — force uniform-ish tiles) ─────────────────
def grid_layout(tiles, x, y, w, h):
    """
    Finviz-style: arrange tiles in a ~uniform grid with slight size variation.
    Not squarified treemap — this forces a denser, more uniform look.
    """
    if not tiles:
        return []

    n = len(tiles)
    # Target ~10-12 tiles per row for density
    cols = min(12, max(8, int(math.sqrt(n * 1.8))))
    rows = (n + cols - 1) // cols

    tw_avg = w / cols
    th_avg = h / rows

    rects = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= n:
                break
            tile = tiles[idx]
            # Add slight random variation (±15%) to tile size for organic look
            rng = random.Random(idx * 4271)
            tw = tw_avg * rng.uniform(0.88, 1.15)
            th = th_avg * rng.uniform(0.88, 1.15)
            rx = x + col * tw_avg
            ry = y + row * th_avg
            rects.append((rx, ry, tw, th, tile))
            idx += 1
        if idx >= n:
            break

    return rects

# ── SVG helpers ───────────────────────────────────────────────────────────────
def esc(v):
    return html.escape(str(v), quote=True)

def txt(x, y, content, size=12, color=WHITE, weight="400", anchor="middle", opacity=1.0):
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}" '
            f'dominant-baseline="central" xml:space="preserve"{op}>{esc(content)}</text>')

# ── Tile rendering ────────────────────────────────────────────────────────────
def render_tiles(tiles):
    rects = grid_layout(tiles, HM_X, HM_Y, HM_W, HM_H)
    GAP = 2
    parts = []

    for i, (rx, ry, rw, rh, meta) in enumerate(rects):
        rx2, ry2, rw2, rh2 = rx + GAP, ry + GAP, rw - GAP * 2, rh - GAP * 2
        if rw2 < 3 or rh2 < 3:
            continue

        fill = meta["color"]
        score = meta["score"]

        # Animation
        rng = random.Random(i * 7331)
        dur = round(rng.uniform(2.5, 5.5), 1)
        dly = round(rng.uniform(0.0, 3.5), 1)
        lo = round(rng.uniform(0.78, 0.90), 2)

        parts.append(f'<g id="t{i}">')
        parts.append(
            f'<rect x="{rx2:.1f}" y="{ry2:.1f}" width="{rw2:.1f}" height="{rh2:.1f}" '
            f'rx="1" fill="{fill}" stroke="{BG}" stroke-width="0.8">'
            f'<animate attributeName="opacity" values="1;{lo};1" dur="{dur}s" '
            f'begin="{dly}s" repeatCount="indefinite"/></rect>'
        )

        # Top edge highlight
        hl = "#55ff55" if score >= 0 else "#ff5555"
        parts.append(
            f'<rect x="{rx2:.1f}" y="{ry2:.1f}" width="{rw2:.1f}" height="1.5" '
            f'rx="0" fill="{hl}" opacity="0.65"/>'
        )

        # Text
        cx, cy = rx2 + rw2 / 2, ry2 + rh2 / 2
        if rw2 >= 45 and rh2 >= 28:
            name_sz = max(8, min(13, int(rw2 / 6)))
            met_sz = max(7, min(10, int(rw2 / 8)))
            max_ch = max(3, int(rw2 / (name_sz * 0.65)))
            lbl = meta["label"][:max_ch]
            if rh2 >= 42:
                parts.append(txt(cx, cy - met_sz * 0.8, lbl, name_sz, "#fff", "700"))
                parts.append(txt(cx, cy + name_sz * 0.6, meta["metric"], met_sz, "#fff", "400"))
            else:
                parts.append(txt(cx, cy, lbl, name_sz, "#fff", "700"))
        elif rw2 >= 22 and rh2 >= 18:
            sz = max(7, min(10, int(rw2 / 5)))
            parts.append(txt(cx, cy, meta["label"][:max(2, int(rw2/(sz*0.7)))], sz, "#fff", "700"))

        parts.append("</g>")

    return "\n".join(parts)

# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(info, repos):
    sx = W - SIDEBAR_W + 10
    sw = SIDEBAR_W - 16
    parts = []
    parts.append(f'<rect x="{W - SIDEBAR_W}" y="{HEADER_H}" width="{SIDEBAR_W}" '
                 f'height="{H - HEADER_H - TICK_H}" fill="{SIDEBAR_BG}"/>')
    parts.append(f'<rect x="{W - SIDEBAR_W}" y="{HEADER_H}" width="1" '
                 f'height="{H - HEADER_H - TICK_H}" fill="{BORDER}"/>')

    y = HEADER_H + 18
    parts.append(txt(sx + sw / 2, y, "MARKET SUMMARY", 9, BLUE, "600"))
    y += 4
    parts.append(f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" stroke="{BORDER}" stroke-width="1"/>')
    y += 14

    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    total_forks = sum(r.get("forks_count", 0) for r in repos if not r.get("fork"))
    repo_count = info.get("public_repos", "—")
    followers = info.get("followers", "—")

    for label, val, vc in [
        ("REPOS", str(repo_count), WHITE),
        ("FOLLOWERS", str(followers), WHITE),
        ("TOTAL ★", str(total_stars), YELL),
        ("FORKS", str(total_forks), DIM),
    ]:
        parts.append(txt(sx, y, label, 9, DIM, "500", anchor="start"))
        parts.append(txt(sx + sw, y, val, 13, vc, "700", anchor="end"))
        y += 22

    parts.append(f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" stroke="{BORDER}"/>')
    y += 14
    parts.append(txt(sx + sw / 2, y, "LANGUAGE DIST", 9, BLUE, "600"))
    y += 12

    lang_map = {}
    for r in repos:
        if not r.get("fork") and r.get("language"):
            lang_map[r["language"]] = lang_map.get(r["language"], 0) + 1
    total_lang = sum(lang_map.values()) or 1
    LCOL = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5",
            "HTML": "#e34c26", "CSS": "#563d7c", "Go": "#00add8", "Rust": "#dea584"}
    bar_items = sorted(lang_map.items(), key=lambda x: -x[1])[:7]
    bx = sx
    for lang, cnt in bar_items:
        seg = (cnt / total_lang) * sw
        col = LCOL.get(lang, "#4a90d9")
        if seg >= 1:
            parts.append(f'<rect x="{bx:.1f}" y="{y}" width="{seg:.1f}" height="7" rx="0" fill="{col}"/>')
            bx += seg
    y += 14
    for lang, cnt in bar_items[:6]:
        col = LCOL.get(lang, "#4a90d9")
        pct = round(cnt / total_lang * 100)
        parts.append(f'<rect x="{sx}" y="{y-7}" width="7" height="7" rx="1" fill="{col}"/>')
        parts.append(txt(sx + 10, y, lang[:12], 9, WHITE, "400", anchor="start"))
        parts.append(txt(sx + sw, y, f"{pct}%", 9, DIM, "400", anchor="end"))
        y += 13

    y += 4
    parts.append(f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" stroke="{BORDER}"/>')
    y += 14
    parts.append(txt(sx + sw / 2, y, "TOP REPOS", 9, BLUE, "600"))
    y += 13
    top5 = sorted([r for r in repos if not r.get("fork")],
                  key=lambda r: r.get("stargazers_count", 0) * 3 + r.get("forks_count", 0),
                  reverse=True)[:6]
    for r in top5:
        name_ = r["name"][:16]
        stars_ = r.get("stargazers_count", 0)
        col_ = GRTXT if stars_ > 0 else DIM
        parts.append(txt(sx, y, f"▸ {name_}", 9, WHITE, "400", anchor="start"))
        parts.append(txt(sx + sw, y, f"★{stars_}", 9, col_, "600", anchor="end"))
        y += 13

    y = H - TICK_H - 14
    parts.append(txt(sx + sw / 2, y, f"AUTO-REFRESH · {USER}", 8, DIM))
    return "\n".join(parts)

# ── Header ────────────────────────────────────────────────────────────────────
def render_header(total_stars):
    mid = (W - SIDEBAR_W) // 2
    return "\n".join([
        f'<rect x="0" y="0" width="{W}" height="{HEADER_H}" fill="{HEADER_BG}"/>',
        f'<rect x="0" y="{HEADER_H-1}" width="{W}" height="1" fill="{BORDER}"/>',
        txt(14, HEADER_H / 2, "KMCR", 14, BLUE, "700", anchor="start"),
        txt(58, HEADER_H / 2, "DEVELOPER MARKET", 11, DIM, anchor="start"),
        f'<rect x="{mid-28}" y="9" width="56" height="18" rx="3" fill="#0f2d17"/>',
        txt(mid, HEADER_H / 2, "● LIVE", 10, GRTXT, "700"),
        txt(W - SIDEBAR_W - 12, HEADER_H / 2, f"▲ +{total_stars}★  TODAY", 11, GRTXT, "600", anchor="end"),
        f'<text x="245" y="{HEADER_H*0.68:.0f}" font-family="{FONT}" font-size="13" '
        f'fill="{BLUE}" dominant-baseline="central"><animate attributeName="opacity" '
        f'values="1;1;0;0" dur="1.2s" repeatCount="indefinite"/>█</text>',
    ])

# ── Ticker ────────────────────────────────────────────────────────────────────
def render_ticker(tiles):
    items = [(t["label"][:10], f"{'▲' if t['score']>=0 else '▼'} {t['metric']}",
              GRTXT if t["score"] >= 0 else RDTXT) for t in tiles]
    items = items * 2
    px, parts = 0, []
    for sym, metric, col in items:
        parts.append(f'<text x="{px}" y="14" font-family="{FONT}" font-size="10" '
                     f'font-weight="600" fill="{WHITE}" dominant-baseline="central">{esc(sym)}</text>')
        parts.append(f'<text x="{px+82}" y="14" font-family="{FONT}" font-size="10" '
                     f'fill="{col}" dominant-baseline="central">{esc(metric)}</text>')
        parts.append(f'<text x="{px+148}" y="14" font-family="{FONT}" font-size="10" '
                     f'fill="{BORDER}" dominant-baseline="central">│</text>')
        px += 160
    ty = H - TICK_H
    return "\n".join([
        f'<rect x="0" y="{ty}" width="{W}" height="{TICK_H}" fill="{HEADER_BG}"/>',
        f'<rect x="0" y="{ty}" width="{W}" height="1" fill="{BORDER}"/>',
        f'<clipPath id="tc"><rect x="0" y="{ty}" width="{W-4}" height="{TICK_H}"/></clipPath>',
        '<g clip-path="url(#tc)">',
        f'<g transform="translate(0,{ty})" style="animation:ticker 30s linear infinite">',
        *parts, "</g></g>",
    ])

CSS = '<style>@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}</style>'

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Fetching GitHub data …")
    info, repos = fetch_all()
    print(f"  {len(repos)} repos")
    tiles = make_tiles(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    print(f"  {total_stars} total stars")

    svg = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="KMCR Developer Market Heatmap">',
        "<title>KMCR Developer Market Heatmap</title>", CSS,
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        render_tiles(tiles), render_sidebar(info, repos), render_header(total_stars),
        render_ticker(tiles), "</svg>",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT}  ({len(svg):,} chars)")

if __name__ == "__main__":
    main()
