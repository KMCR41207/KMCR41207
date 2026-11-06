#!/usr/bin/env python3
"""
Generate an animated stock-market-style heatmap SVG for a GitHub profile.

Visual design: Finviz/Bloomberg treemap — dark terminal background, rectangular
tiles sized by repository star+fork weight, colored green/red by recent activity.
Full CSS @keyframes animation so the SVG plays natively inside GitHub README.

Python standard library only. Safe to run locally or via GitHub Actions.
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
USER = "KMCR41207"
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "market-heatmap.svg"

# Canvas
W, H = 1120, 580

# Palette — financial terminal aesthetic
BG          = "#070A0F"
GRID_LINE   = "#131B2A"
PANEL_BG    = "#0C1220"
BORDER_DIM  = "#1A2740"
BORDER_ACT  = "#2A4070"

# Tile colours — five intensity steps each direction
GREENS = ["#0D2B1A", "#0F3D22", "#145C2F", "#1A7A3C", "#22A652", "#2ECC71"]
REDS   = ["#2B0D0D", "#3D0F0F", "#5C1414", "#7A1A1A", "#A62222", "#CC2E2E"]
NEUTRAL = "#111827"

# Typography
FONT = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
WHITE     = "#F0F4FF"
MUTED     = "#607090"
ACCENT    = "#4A90D9"
BRIGHT    = "#78B8FF"
GREEN_TXT = "#2ECC71"
RED_TXT   = "#CC2E2E"
YELLOW    = "#F1C26B"


# ── GitHub API helpers ────────────────────────────────────────────────────────
def _headers():
    h = {"Accept": "application/vnd.github+json", "User-Agent": "KMCR-heatmap-action"}
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def api(url):
    try:
        with urlopen(Request(url, headers=_headers()), timeout=15) as r:
            return json.load(r)
    except (HTTPError, URLError, TimeoutError, ValueError) as e:
        print(f"  API warn: {url}  →  {e}")
        return None


def fetch_profile():
    data = api(f"https://api.github.com/users/{USER}")
    if not isinstance(data, dict):
        return {"repos": "—", "followers": "—", "name": USER}
    return {
        "repos":     data.get("public_repos", "—"),
        "followers": data.get("followers", "—"),
        "name":      data.get("name") or USER,
        "bio":       data.get("bio") or "",
    }


def fetch_repos():
    """Return list of repo dicts, all public repos up to 500."""
    results, page = [], 1
    while page <= 5:
        batch = api(
            f"https://api.github.com/users/{USER}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )
        if not isinstance(batch, list):
            break
        results.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return results


def fetch_contributions_approx(repos):
    """Approximate total commits from event stream (no auth = 300 events)."""
    events = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    pushes = 0
    if isinstance(events, list):
        for ev in events:
            if ev.get("type") == "PushEvent":
                pushes += ev.get("payload", {}).get("size", 0)
    return pushes


# ── Treemap (squarified) ──────────────────────────────────────────────────────
def _worst(row, w, total_area):
    if not row or total_area == 0:
        return float("inf")
    s = sum(row)
    side = s / w
    if side == 0:
        return float("inf")
    return max(max(r / side for r in row), max(side / r for r in row)) if min(row) > 0 else float("inf")


def squarify(items, x, y, w, h):
    """items: list of (value, meta).  Returns list of (x,y,w,h,meta)."""
    if not items:
        return []
    total = sum(v for v, _ in items)
    if total == 0 or w <= 0 or h <= 0:
        return []

    def layout_row(row_items, x, y, w, h):
        row_sum = sum(v for v, _ in row_items)
        rects = []
        if w >= h:
            col_w = (row_sum / total) * w
            cy = y
            for v, meta in row_items:
                rh = (v / row_sum) * h if row_sum else 0
                rects.append((x, cy, col_w, rh, meta))
                cy += rh
        else:
            row_h = (row_sum / total) * h
            cx = x
            for v, meta in row_items:
                rw = (v / row_sum) * w if row_sum else 0
                rects.append((cx, y, rw, row_h, meta))
                cx += rw
        return rects

    result = []
    remaining = list(items)
    rx, ry, rw, rh = x, y, w, h
    row = []

    while remaining:
        item = remaining[0]
        short = rw if rw < rh else rh
        remaining_sum = sum(v for v, _ in remaining)
        row_vals  = [v for v, _ in row]
        test_vals = row_vals + [item[0]]
        if not row or _worst(test_vals, short, remaining_sum) <= _worst(row_vals, short, remaining_sum):
            row.append(item)
            remaining.pop(0)
        else:
            rects = layout_row(row, rx, ry, rw, rh)
            result.extend(rects)
            row_sum = sum(v for v, _ in row)
            if rw >= rh:
                used = (row_sum / total) * rw
                rx += used
                rw -= used
            else:
                used = (row_sum / total) * rh
                ry += used
                rh -= used
            row = []

    if row:
        result.extend(layout_row(row, rx, ry, rw, rh))
    return result


# ── Colour helpers ────────────────────────────────────────────────────────────
def activity_color(score):
    """score in [-1, 1].  Negative → red, positive → green."""
    if score > 0.7:
        return GREENS[5]
    if score > 0.4:
        return GREENS[4]
    if score > 0.15:
        return GREENS[3]
    if score > 0:
        return GREENS[2]
    if score == 0:
        return NEUTRAL
    if score > -0.15:
        return REDS[2]
    if score > -0.4:
        return REDS[3]
    if score > -0.7:
        return REDS[4]
    return REDS[5]


def brightness(hex_color):
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000


# ── SVG primitives ────────────────────────────────────────────────────────────
def esc(v):
    return html.escape(str(v), quote=True)


def t(x, y, content, size=13, color=WHITE, weight="400", anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}" '
        f'dominant-baseline="auto" xml:space="preserve" {extra}>{esc(content)}</text>'
    )


def rect(x, y, w, h, fill, rx=3, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" {extra}/>'


# ── Build repo tiles ──────────────────────────────────────────────────────────
def build_tile_data(repos):
    """Turn raw repo list into weighted, coloured tile descriptors."""
    tiles = []
    for r in repos:
        if r.get("fork"):
            continue                          # skip forks
        name  = r.get("name", "")
        lang  = r.get("language") or "Code"
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        size  = r.get("size", 0)
        # Weight: stars count double, forks count 1.5x, size gives baseline
        weight = max(stars * 2 + forks * 1.5 + math.log1p(size) * 0.5, 0.5)

        # Activity score: normalise stars+forks into [-1,1]
        raw = stars * 3 + forks * 1.5
        score = math.tanh(raw / 15.0)        # smooth sigmoid-like mapping

        # Deterministic pseudo-random jitter so idle repos get light green/red
        rng = random.Random(name)
        jitter = rng.uniform(-0.12, 0.12)
        score = max(-1.0, min(1.0, score + jitter))

        pct_display = f"+{stars}★" if stars else f"{forks} forks" if forks else "—"

        tiles.append({
            "name":   name,
            "lang":   lang,
            "weight": weight,
            "score":  score,
            "color":  activity_color(score),
            "pct":    pct_display,
            "stars":  stars,
            "forks":  forks,
        })

    # Sort descending by weight for treemap stability
    tiles.sort(key=lambda x: -x["weight"])
    return tiles[:40]   # cap at 40 tiles for readability


# ── Animation CSS ─────────────────────────────────────────────────────────────
def animation_css(tile_count):
    """Generate per-tile CSS keyframes for subtle pulse / glow animation."""
    css_parts = [
        "<style>",
        "  .tile { cursor: pointer; transition: opacity 0.4s; }",
        "  .tile:hover rect { stroke-width: 2; opacity: 1 !important; }",
        "  .tile:hover .tile-glow { opacity: 1 !important; }",
    ]

    # Each tile gets a unique animation with a staggered delay
    for i in range(tile_count):
        rng = random.Random(i * 31337)
        dur   = round(rng.uniform(3.5, 7.0), 2)
        delay = round(rng.uniform(0.0, 5.0), 2)
        # opacity oscillates subtly between 0.82 and 1.0
        css_parts.append(
            f"  @keyframes pulse{i} {{"
            f" 0%,100%{{opacity:0.86}} 50%{{opacity:1}} }}"
        )
        css_parts.append(
            f"  #tile{i} > rect.tile-fill"
            f" {{ animation: pulse{i} {dur}s {delay}s ease-in-out infinite; }}"
        )

    # Ticker tape scroll
    css_parts.append(
        "  @keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }"
    )
    css_parts.append("  .ticker-inner { animation: ticker 28s linear infinite; }")

    # Header blink cursor
    css_parts.append(
        "  @keyframes blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }"
    )
    css_parts.append("  .cursor { animation: blink 1.1s step-end infinite; }")

    # Glow pulse
    css_parts.append(
        "  @keyframes glow { 0%,100%{opacity:0} 60%{opacity:0.35} }"
    )

    css_parts.append("</style>")
    return "\n".join(css_parts)


# ── Sidebar stats ─────────────────────────────────────────────────────────────
SIDEBAR_X = W - 224
SIDEBAR_W = 216


def sidebar(profile, repos, total_stars, languages):
    lines = []
    sx = SIDEBAR_X + 12

    # Panel background
    lines.append(rect(SIDEBAR_X, 48, SIDEBAR_W, H - 52, PANEL_BG, rx=0))
    lines.append(
        f'<rect x="{SIDEBAR_X}" y="48" width="1" height="{H-52}" fill="{BORDER_ACT}"/>'
    )

    # Title
    lines.append(t(sx, 76, "MARKET SUMMARY", 10, ACCENT, "600"))
    lines.append(f'<rect x="{sx}" y="82" width="192" height="1" fill="{BORDER_DIM}"/>')

    # Stats grid
    stats = [
        ("REPOS",      str(profile.get("repos", "—")),  BRIGHT),
        ("FOLLOWERS",  str(profile.get("followers", "—")), BRIGHT),
        ("TOTAL ★",    str(total_stars) if isinstance(total_stars, int) else "—", YELLOW),
    ]
    sy = 100
    for label, val, col in stats:
        lines.append(t(sx, sy, label, 9, MUTED, "600"))
        lines.append(t(sx + 100, sy, val, 14, col, "700", anchor="end"))
        sy += 28

    lines.append(f'<rect x="{sx}" y="{sy}" width="192" height="1" fill="{BORDER_DIM}"/>')
    sy += 14

    # Language distribution
    lines.append(t(sx, sy, "LANGUAGE DIST", 10, ACCENT, "600"))
    sy += 16
    total_lang = sum(languages.values()) or 1
    bar_w = 192
    bx = sx
    LANG_COLORS = {
        "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "Python": "#3572A5",
        "HTML": "#E34C26",       "CSS": "#563D7C",        "Shell": "#89E051",
        "Java": "#B07219",       "C++": "#F34B7D",        "C": "#555555",
        "Go": "#00ADD8",         "Rust": "#DEA584",       "Ruby": "#701516",
        "PHP": "#4F5D95",        "Swift": "#FA7343",      "Kotlin": "#A97BFF",
    }
    bar_items = sorted(languages.items(), key=lambda x: -x[1])[:6]
    if bar_items:
        # Stacked bar
        for lang, cnt in bar_items:
            seg_w = (cnt / total_lang) * bar_w
            col   = LANG_COLORS.get(lang, "#4A90D9")
            if seg_w > 1:
                lines.append(
                    f'<rect x="{bx:.1f}" y="{sy}" width="{seg_w:.1f}" height="8" '
                    f'rx="0" fill="{col}"/>'
                )
                bx += seg_w
        sy += 14
        # Legend (max 6)
        for lang, cnt in bar_items[:6]:
            col = LANG_COLORS.get(lang, "#4A90D9")
            pct = round(cnt / total_lang * 100)
            lines.append(
                f'<rect x="{sx}" y="{sy-8}" width="8" height="8" rx="1" fill="{col}"/>'
            )
            lines.append(t(sx + 12, sy, f"{lang}", 10, WHITE))
            lines.append(t(sx + 192, sy, f"{pct}%", 10, MUTED, anchor="end"))
            sy += 14
    sy += 6

    lines.append(f'<rect x="{sx}" y="{sy}" width="192" height="1" fill="{BORDER_DIM}"/>')
    sy += 14

    # Top repos mini list
    lines.append(t(sx, sy, "TOP REPOS", 10, ACCENT, "600"))
    sy += 14
    top = sorted(repos, key=lambda r: r.get("stargazers_count", 0) + r.get("forks_count", 0), reverse=True)
    for repo in top[:5]:
        name   = repo.get("name", "")[:18]
        stars  = repo.get("stargazers_count", 0)
        forks  = repo.get("forks_count", 0)
        col    = GREEN_TXT if stars + forks > 0 else MUTED
        lines.append(t(sx, sy, f"▸ {name}", 10, WHITE))
        lines.append(t(sx + 192, sy, f"★{stars}", 10, col, anchor="end"))
        sy += 14

    sy += 6
    lines.append(f'<rect x="{sx}" y="{sy}" width="192" height="1" fill="{BORDER_DIM}"/>')
    sy += 12
    lines.append(t(sx, sy, f"AUTO-REFRESH  ·  {USER}", 9, MUTED))

    return "\n".join(lines)


# ── Ticker tape ───────────────────────────────────────────────────────────────
def ticker_tape(tiles):
    items = []
    for tile in tiles:
        col   = GREEN_TXT if tile["score"] >= 0 else RED_TXT
        sign  = "▲" if tile["score"] >= 0 else "▼"
        items.append((f"{tile['name'].upper()[:10]}", f"{sign} {tile['pct']}", col))
    # Duplicate for seamless loop
    items = items * 2

    tape_parts = []
    cx = 0
    for name, pct, col in items:
        tape_parts.append(
            f'<text x="{cx}" y="11" font-family="{FONT}" font-size="11" '
            f'font-weight="600" fill="{WHITE}" xml:space="preserve">{esc(name)}</text>'
        )
        tape_parts.append(
            f'<text x="{cx+90}" y="11" font-family="{FONT}" font-size="11" '
            f'font-weight="400" fill="{col}" xml:space="preserve">{esc(pct)}</text>'
        )
        tape_parts.append(
            f'<text x="{cx+154}" y="11" font-family="{FONT}" font-size="11" '
            f'fill="{BORDER_ACT}" xml:space="preserve">│</text>'
        )
        cx += 168

    return (
        f'<rect x="0" y="{H-22}" width="{W}" height="22" fill="{PANEL_BG}"/>'
        f'<rect x="0" y="{H-22}" width="{W}" height="1" fill="{BORDER_ACT}"/>'
        f'<clipPath id="ticker-clip"><rect x="0" y="{H-22}" width="{W-4}" height="22"/></clipPath>'
        f'<g clip-path="url(#ticker-clip)">'
        f'<g class="ticker-inner" transform="translate(0,{H-22})">'
        + "".join(tape_parts)
        + "</g></g>"
    )


# ── Main tile rendering ───────────────────────────────────────────────────────
HEATMAP_X, HEATMAP_Y = 8, 48
HEATMAP_W = SIDEBAR_X - HEATMAP_X - 4
HEATMAP_H = H - HEATMAP_Y - 26   # leave room for ticker


def render_tiles(tiles):
    if not tiles:
        return '<text x="200" y="200" fill="#607090" font-size="16">No repository data available.</text>'

    items = [(t["weight"], t) for t in tiles]
    rects = squarify(items, HEATMAP_X, HEATMAP_Y, HEATMAP_W, HEATMAP_H)

    parts = []
    for i, (rx, ry, rw, rh, meta) in enumerate(rects):
        GAP = 2
        rx, ry, rw, rh = rx + GAP, ry + GAP, rw - GAP * 2, rh - GAP * 2
        if rw < 2 or rh < 2:
            continue

        fill   = meta["color"]
        bright = brightness(fill) > 80
        txt_c  = "#071008" if bright else WHITE
        pct_c  = "#071008" if bright else (GREEN_TXT if meta["score"] >= 0 else RED_TXT)

        # Glow filter id per tile
        glow_id = f"glow{i}"

        parts.append(f'<g id="tile{i}" class="tile">')

        # Subtle inner glow via feGaussianBlur
        parts.append(
            f'<defs><filter id="{glow_id}" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>'
            f'<feComposite in="SourceGraphic" in2="blur" operator="over"/>'
            f'</filter></defs>'
        )

        # Base tile
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'rx="3" fill="{fill}" stroke="{GRID_LINE}" stroke-width="1" class="tile-fill"/>'
        )

        # Glow overlay (animated separately)
        parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" '
            f'rx="3" fill="{fill}" filter="url(#{glow_id})" class="tile-glow" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.3;0" '
            f'dur="{round(random.Random(i).uniform(4,9), 1)}s" '
            f'begin="{round(random.Random(i*7).uniform(0,5), 1)}s" '
            f'repeatCount="indefinite"/>'
            f'</rect>'
        )

        # Text — only render if tile is big enough
        if rw > 55 and rh > 28:
            # Repo name — truncate to fit
            max_chars = max(4, int(rw / 7.5))
            name_str  = meta["name"][:max_chars]
            lang_str  = meta["lang"]

            name_size = min(13, max(9, int(rw / 9)))
            meta_size = min(10, max(8, int(rw / 11)))

            cx = rx + rw / 2

            if rh > 48:
                parts.append(
                    f'<text x="{cx:.1f}" y="{ry + rh*0.42:.1f}" '
                    f'font-family="{FONT}" font-size="{name_size}" font-weight="700" '
                    f'fill="{txt_c}" text-anchor="middle" xml:space="preserve">{esc(name_str)}</text>'
                )
                parts.append(
                    f'<text x="{cx:.1f}" y="{ry + rh*0.42 + meta_size + 4:.1f}" '
                    f'font-family="{FONT}" font-size="{meta_size}" font-weight="400" '
                    f'fill="{pct_c}" text-anchor="middle" xml:space="preserve">{esc(meta["pct"])}</text>'
                )
                if rh > 68 and rw > 70:
                    parts.append(
                        f'<text x="{cx:.1f}" y="{ry + rh*0.42 + meta_size*2 + 9:.1f}" '
                        f'font-family="{FONT}" font-size="{max(7, meta_size-1)}" font-weight="400" '
                        f'fill="{txt_c}" opacity="0.55" text-anchor="middle" xml:space="preserve">'
                        f'{esc(lang_str)}</text>'
                    )
            else:
                # Single line for small tiles
                parts.append(
                    f'<text x="{cx:.1f}" y="{ry + rh*0.62:.1f}" '
                    f'font-family="{FONT}" font-size="{name_size}" font-weight="700" '
                    f'fill="{txt_c}" text-anchor="middle" xml:space="preserve">{esc(name_str)}</text>'
                )

        parts.append("</g>")

    return "\n".join(parts)


# ── Header bar ────────────────────────────────────────────────────────────────
def header_bar(total_stars):
    sign  = "▲"
    score = f"+{total_stars}★  TODAY"
    return "\n".join([
        f'<rect x="0" y="0" width="{W}" height="44" fill="{PANEL_BG}"/>',
        f'<rect x="0" y="44" width="{W}" height="1" fill="{BORDER_ACT}"/>',
        # Logo / brand
        f'<text x="14" y="28" font-family="{FONT}" font-size="14" font-weight="700" '
        f'fill="{BRIGHT}">KMCR</text>',
        f'<text x="60" y="28" font-family="{FONT}" font-size="14" font-weight="400" '
        f'fill="{MUTED}">DEVELOPER MARKET</text>',
        # Blinking cursor
        f'<text x="240" y="28" font-family="{FONT}" font-size="14" font-weight="400" '
        f'fill="{ACCENT}" class="cursor">█</text>',
        # Live badge
        f'<rect x="{W//2 - 30}" y="12" width="60" height="20" rx="3" fill="#0F3D22"/>',
        f'<text x="{W//2}" y="26" font-family="{FONT}" font-size="10" font-weight="700" '
        f'fill="{GREEN_TXT}" text-anchor="middle">● LIVE</text>',
        # Stars summary
        f'<text x="{SIDEBAR_X - 12}" y="28" font-family="{FONT}" font-size="12" '
        f'font-weight="600" fill="{GREEN_TXT}" text-anchor="end">{esc(sign)} {esc(score)}</text>',
    ])


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Fetching GitHub profile …")
    profile = fetch_profile()
    print(f"  {profile}")

    print("Fetching repositories …")
    repos = fetch_repos()
    print(f"  {len(repos)} repos fetched")

    # Total stars
    total_stars = sum(r.get("stargazers_count", 0) for r in repos
                      if not r.get("fork"))

    # Language distribution (count repos per language)
    languages: dict[str, int] = {}
    for r in repos:
        if r.get("fork"):
            continue
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    # Build tiles
    tiles = build_tile_data(repos)
    print(f"  {len(tiles)} tiles generated")

    tile_count = len(tiles)
    css        = animation_css(tile_count)
    tile_svg   = render_tiles(tiles)
    side_svg   = sidebar(profile, repos, total_stars, languages)
    head_svg   = header_bar(total_stars)
    tape_svg   = ticker_tape(tiles)

    svg = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="K Mani Charan Reddy — Developer Market Heatmap">',
        "<title>KMCR Developer Market Heatmap</title>",
        css,
        # Background
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        # Grid lines (subtle)
        "".join(
            f'<line x1="{HEATMAP_X}" y1="{y}" x2="{HEATMAP_X+HEATMAP_W}" y2="{y}" '
            f'stroke="{GRID_LINE}" stroke-width="0.5"/>'
            for y in range(HEATMAP_Y, H - 22, 40)
        ),
        head_svg,
        tile_svg,
        side_svg,
        tape_svg,
        "</svg>",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote  {OUTPUT}")


if __name__ == "__main__":
    main()
