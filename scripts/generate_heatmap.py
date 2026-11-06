#!/usr/bin/env python3
"""
Finviz-style animated stock market heatmap for a GitHub profile.

Design goals
------------
* Bright saturated green/red tiles — exactly like the Finviz S&P 500 heatmap
* Proper 2-D squarified treemap (no horizontal stripes)
* Tile size driven by repo size (log scale) so weights differ enough to
  produce varied tile shapes even when star counts are uniform
* Bold ticker + percentage text centred in each tile
* Dark charcoal background  (#0d1117 — GitHub's own dark bg)
* CSS @keyframes pulse per tile + SVG <animate> glow — all GitHub-safe,
  no JavaScript required
* Compact Bloomberg-style stat sidebar on the right
* Scrolling ticker tape at the bottom

Python standard library only. No pip installs.
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

W, H = 1060, 520          # total canvas
SIDEBAR_W = 210           # right panel width
PAD       = 6             # gap between canvas edge and heatmap
TICK_H    = 22            # ticker tape height at bottom
HEADER_H  = 38            # top header bar height

# Heatmap area
HM_X = PAD
HM_Y = HEADER_H + PAD
HM_W = W - SIDEBAR_W - PAD * 2 - 4
HM_H = H - HEADER_H - TICK_H - PAD * 2

# ── Colour palette ─────────────────────────────────────────────────────────────
BG         = "#0d1117"      # GitHub dark background
HEADER_BG  = "#010409"
SIDEBAR_BG = "#010409"
BORDER     = "#21262d"
GRID       = "#161b22"

# Bright Finviz-style greens (low → high intensity)
GREENS = [
    "#145214",   # very dark – barely active
    "#1a6b1a",
    "#1e8a1e",
    "#22a622",   # mid
    "#28cc28",
    "#2eeb2e",   # bright lime – very active
]
# Bright Finviz-style reds
REDS = [
    "#521414",
    "#6b1a1a",
    "#8a1e1e",
    "#a62222",   # mid
    "#cc2828",
    "#eb2e2e",   # bright red – stale/dead
]
NEUTRAL = "#1c2128"

FONT  = "ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace"
WHITE = "#e6edf3"
DIM   = "#8b949e"
BLUE  = "#58a6ff"
YELL  = "#e3b341"
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
    except (HTTPError, URLError, TimeoutError, ValueError) as e:
        print(f"  api warn {url}: {e}")
        return None


def fetch_all():
    info  = _get(f"https://api.github.com/users/{USER}") or {}
    repos, page = [], 1
    while page <= 5:
        batch = _get(
            f"https://api.github.com/users/{USER}/repos"
            f"?per_page=100&page={page}&sort=pushed"
        )
        if not isinstance(batch, list):
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return info, repos


# ── Tile data ─────────────────────────────────────────────────────────────────
def make_tiles(repos):
    tiles = []
    for r in repos:
        if r.get("fork"):
            continue
        name   = r.get("name", "")
        lang   = r.get("language") or ""
        stars  = r.get("stargazers_count", 0)
        forks  = r.get("forks_count", 0)
        size   = r.get("size", 0)          # KB

        # Weight: repo size dominates so tiles differ in size;
        # stars/forks add a bonus so popular repos are bigger
        weight = math.log1p(size) * 3 + stars * 8 + forks * 5 + 1.0

        # Activity score → colour selection
        # Use stars+forks as primary signal; size/language as tiebreaker
        raw   = stars * 4 + forks * 2 + math.log1p(size) * 0.3
        score = math.tanh(raw / 12.0)      # −1 … +1

        # Deterministic jitter so even-weight repos spread across shades
        rng    = random.Random(hash(name) & 0xFFFFFF)
        jitter = rng.uniform(-0.25, 0.25)
        score  = max(-1.0, min(1.0, score + jitter))

        # Colour intensity index 0-5
        idx = min(5, int(abs(score) * 6))
        color = GREENS[idx] if score >= 0 else REDS[idx]

        # Display label: repo name uppercased, trimmed
        label = name.upper()

        # Metric display (stars if any, else size in KB)
        if stars > 0:
            metric = f"+{stars}★"
        elif size > 1024:
            metric = f"{size//1024}MB"
        elif size > 0:
            metric = f"{size}KB"
        else:
            metric = "—"

        tiles.append(dict(
            name=name, label=label, lang=lang,
            stars=stars, forks=forks, size=size,
            weight=weight, score=score, color=color, metric=metric,
        ))

    tiles.sort(key=lambda t: -t["weight"])
    return tiles[:35]


# ── Squarified treemap ────────────────────────────────────────────────────────
def _aspect(a, b):
    """Worst aspect ratio of a rectangle with sides a and b."""
    if a == 0 or b == 0:
        return float("inf")
    return max(a / b, b / a)


def squarify(values, x, y, w, h):
    """
    Pure squarified treemap.
    values : list of (weight, meta)
    Returns : list of (rx, ry, rw, rh, meta)
    """
    if not values or w <= 0 or h <= 0:
        return []

    total = sum(v for v, _ in values)
    if total == 0:
        return []

    result    = []
    remaining = list(values)
    cx, cy, cw, ch = x, y, w, h

    while remaining:
        # Decide layout direction: use the shorter side
        short = cw if cw <= ch else ch
        row   = []
        row_sum = 0.0

        for item in remaining:
            v    = item[0]
            test = row + [item]
            ts   = row_sum + v
            # Compute worst aspect for test row
            if short == 0:
                break
            # Each row fills `ts/total` of the short side as a strip
            strip = (ts / total) * (cw * ch) / short if short > 0 else 0
            worst_new = max(
                _aspect((vi / ts) * short, strip / ((vi / ts) * short) if (vi / ts) * short > 0 else 1e9)
                for vi, _ in test
            ) if ts > 0 else float("inf")
            worst_old = max(
                _aspect((vi / row_sum) * short,
                        (row_sum / total) * (cw * ch) / short /
                        ((vi / row_sum) * short) if (vi / row_sum) * short > 0 else 1e9)
                for vi, _ in row
            ) if row else float("inf")

            if not row or worst_new <= worst_old:
                row.append(item)
                row_sum += v
            else:
                break

        if not row:
            row      = [remaining[0]]
            row_sum  = remaining[0][0]

        remaining = remaining[len(row):]

        # Lay out this row as a strip
        strip_frac = row_sum / total
        if cw <= ch:
            # Horizontal strip across full width
            strip_h = strip_frac * ch
            px = cx
            for v, meta in row:
                pw = (v / row_sum) * cw if row_sum else 0
                result.append((px, cy, pw, strip_h, meta))
                px += pw
            cy    += strip_h
            ch    -= strip_h
        else:
            # Vertical strip across full height
            strip_w = strip_frac * cw
            py = cy
            for v, meta in row:
                ph = (v / row_sum) * ch if row_sum else 0
                result.append((cx, py, strip_w, ph, meta))
                py += ph
            cx    += strip_w
            cw    -= strip_w

        # Rescale remaining weights relative to leftover area
        leftover = cw * ch
        used     = w * h * strip_frac
        remaining_area = w * h - (w * h - leftover - 0)  # running total
        # Renormalise weights for next iteration
        total -= row_sum

    return result


# ── SVG helpers ───────────────────────────────────────────────────────────────
def esc(v):
    return html.escape(str(v), quote=True)


def txt(x, y, content, size=12, color=WHITE, weight="400",
        anchor="middle", opacity=1.0, extra=""):
    op = f' opacity="{opacity}"' if opacity != 1.0 else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" '
        f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{color}" text-anchor="{anchor}" dominant-baseline="central" '
        f'xml:space="preserve"{op} {extra}>{esc(content)}</text>'
    )


# ── Tile rendering ────────────────────────────────────────────────────────────
def render_tiles(tiles):
    items  = [(t["weight"], t) for t in tiles]
    rects  = squarify(items, HM_X, HM_Y, HM_W, HM_H)
    GAP    = 3        # pixel gap between tiles
    parts  = []

    for i, (rx, ry, rw, rh, meta) in enumerate(rects):
        # Apply gap
        rx2, ry2, rw2, rh2 = rx + GAP, ry + GAP, rw - GAP * 2, rh - GAP * 2
        if rw2 < 4 or rh2 < 4:
            continue

        fill  = meta["color"]
        score = meta["score"]

        # Staggered pulse animation
        rng   = random.Random(i * 13337)
        dur   = round(rng.uniform(2.8, 6.5), 1)
        dly   = round(rng.uniform(0.0, 4.0), 1)
        lo    = round(rng.uniform(0.75, 0.88), 2)

        parts.append(f'<g id="t{i}">')

        # Tile body
        parts.append(
            f'<rect x="{rx2:.1f}" y="{ry2:.1f}" '
            f'width="{rw2:.1f}" height="{rh2:.1f}" rx="2" '
            f'fill="{fill}" stroke="{BG}" stroke-width="1">'
            f'<animate attributeName="opacity" '
            f'values="1;{lo};1" dur="{dur}s" begin="{dly}s" '
            f'repeatCount="indefinite"/>'
            f'</rect>'
        )

        # Bright top-edge highlight (like Finviz)
        hl_color = "#4dff4d" if score >= 0 else "#ff4d4d"
        parts.append(
            f'<rect x="{rx2:.1f}" y="{ry2:.1f}" '
            f'width="{rw2:.1f}" height="2" rx="0" fill="{hl_color}" opacity="0.6"/>'
        )

        # Text — scale to tile size
        cx = rx2 + rw2 / 2
        cy = ry2 + rh2 / 2

        if rw2 >= 60 and rh2 >= 36:
            # Full: name + metric
            name_size   = max(9, min(18, int(rw2 / 6.5)))
            metric_size = max(8, min(13, int(rw2 / 9)))
            max_chars   = max(3, int(rw2 / (name_size * 0.62)))
            label_str   = meta["label"][:max_chars]
            metric_col  = "#ffffff"

            if rh2 >= 56:
                # Two lines: name above, metric below centre
                parts.append(txt(cx, cy - metric_size * 0.9, label_str,
                                  name_size, "#ffffff", "700"))
                parts.append(txt(cx, cy + name_size * 0.7, meta["metric"],
                                  metric_size, metric_col, "400"))
                if rh2 >= 76 and rw2 >= 90:
                    parts.append(txt(cx, cy + name_size * 0.7 + metric_size + 3,
                                      meta["lang"], max(7, metric_size - 2),
                                      "#ffffff", "400", opacity=0.5))
            else:
                # Single line: name only
                parts.append(txt(cx, cy, label_str, name_size, "#ffffff", "700"))

        elif rw2 >= 28 and rh2 >= 20:
            # Tiny tile: abbreviated name
            name_size = max(7, min(11, int(rw2 / 5)))
            max_chars = max(2, int(rw2 / (name_size * 0.65)))
            parts.append(txt(cx, cy, meta["label"][:max_chars],
                              name_size, "#ffffff", "700"))

        parts.append("</g>")

    return "\n".join(parts)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(info, repos, tiles):
    sx   = W - SIDEBAR_W + 10
    sw   = SIDEBAR_W - 16
    parts = []

    # Panel bg
    parts.append(
        f'<rect x="{W - SIDEBAR_W}" y="{HEADER_H}" '
        f'width="{SIDEBAR_W}" height="{H - HEADER_H - TICK_H}" '
        f'fill="{SIDEBAR_BG}"/>'
    )
    parts.append(
        f'<rect x="{W - SIDEBAR_W}" y="{HEADER_H}" '
        f'width="1" height="{H - HEADER_H - TICK_H}" fill="{BORDER}"/>'
    )

    y = HEADER_H + 18
    parts.append(txt(sx + sw / 2, y, "MARKET SUMMARY",
                      9, BLUE, "600", anchor="middle"))
    y += 4
    parts.append(
        f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )
    y += 14

    total_stars  = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    total_forks  = sum(r.get("forks_count", 0)      for r in repos if not r.get("fork"))
    repo_count   = info.get("public_repos", "—")
    followers    = info.get("followers", "—")

    for label, val, vc in [
        ("REPOS",      str(repo_count),   WHITE),
        ("FOLLOWERS",  str(followers),    WHITE),
        ("TOTAL ★",    str(total_stars),  YELL),
        ("FORKS",      str(total_forks),  DIM),
    ]:
        parts.append(txt(sx,        y, label, 9,  DIM,   "500", anchor="start"))
        parts.append(txt(sx + sw,   y, val,   13, vc,    "700", anchor="end"))
        y += 22

    # Divider
    parts.append(
        f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )
    y += 14

    # Language dist
    parts.append(txt(sx + sw / 2, y, "LANGUAGE DIST", 9, BLUE, "600", anchor="middle"))
    y += 12

    lang_map: dict[str, int] = {}
    for r in repos:
        if not r.get("fork") and r.get("language"):
            lang_map[r["language"]] = lang_map.get(r["language"], 0) + 1
    total_lang = sum(lang_map.values()) or 1

    LCOL = {
        "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
        "Python": "#3572a5",     "HTML": "#e34c26",
        "CSS": "#563d7c",        "Go": "#00add8",
        "Rust": "#dea584",       "Java": "#b07219",
        "C++": "#f34b7d",        "C": "#555555",
        "Ruby": "#701516",       "Swift": "#fa7343",
    }

    # Stacked bar
    bar_items = sorted(lang_map.items(), key=lambda x: -x[1])[:7]
    bx = sx
    for lang, cnt in bar_items:
        seg = (cnt / total_lang) * sw
        col = LCOL.get(lang, "#4a90d9")
        if seg >= 1:
            parts.append(
                f'<rect x="{bx:.1f}" y="{y}" width="{seg:.1f}" height="7" '
                f'rx="0" fill="{col}"/>'
            )
            bx += seg
    y += 14

    for lang, cnt in bar_items[:6]:
        col  = LCOL.get(lang, "#4a90d9")
        pct  = round(cnt / total_lang * 100)
        parts.append(
            f'<rect x="{sx}" y="{y-7}" width="7" height="7" rx="1" fill="{col}"/>'
        )
        parts.append(txt(sx + 10, y, lang[:12], 9, WHITE, "400", anchor="start"))
        parts.append(txt(sx + sw, y, f"{pct}%", 9, DIM,   "400", anchor="end"))
        y += 13

    y += 4
    parts.append(
        f'<line x1="{sx}" y1="{y}" x2="{sx+sw}" y2="{y}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )
    y += 14

    # Top repos
    parts.append(txt(sx + sw / 2, y, "TOP REPOS", 9, BLUE, "600", anchor="middle"))
    y += 13

    top5 = sorted(
        [r for r in repos if not r.get("fork")],
        key=lambda r: r.get("stargazers_count", 0) * 3 + r.get("forks_count", 0),
        reverse=True,
    )[:6]
    for r in top5:
        name_  = r["name"][:16]
        stars_ = r.get("stargazers_count", 0)
        col_   = GRTXT if stars_ > 0 else DIM
        parts.append(txt(sx,       y, f"▸ {name_}", 9, WHITE, "400", anchor="start"))
        parts.append(txt(sx + sw,  y, f"★{stars_}", 9, col_,  "600", anchor="end"))
        y += 13

    # Footer
    y = H - TICK_H - 14
    parts.append(txt(sx + sw / 2, y, f"AUTO-REFRESH · {USER}", 8, DIM, anchor="middle"))

    return "\n".join(parts)


# ── Header bar ────────────────────────────────────────────────────────────────
def render_header(total_stars):
    mid = (W - SIDEBAR_W) // 2
    return "\n".join([
        f'<rect x="0" y="0" width="{W}" height="{HEADER_H}" fill="{HEADER_BG}"/>',
        f'<rect x="0" y="{HEADER_H-1}" width="{W}" height="1" fill="{BORDER}"/>',
        # Brand
        txt(14, HEADER_H / 2, "KMCR", 14, BLUE,  "700", anchor="start"),
        txt(58, HEADER_H / 2, "DEVELOPER MARKET", 11, DIM, anchor="start"),
        # Live badge
        f'<rect x="{mid-28}" y="9" width="56" height="18" rx="3" fill="#0f2d17"/>',
        txt(mid, HEADER_H / 2, "● LIVE", 10, GRTXT, "700"),
        # Stats
        txt(W - SIDEBAR_W - 12, HEADER_H / 2,
            f"▲ +{total_stars}★  TODAY", 11, GRTXT, "600", anchor="end"),
        # Blinking cursor
        f'<text x="245" y="{HEADER_H*0.68:.0f}" font-family="{FONT}" '
        f'font-size="13" fill="{BLUE}" dominant-baseline="central">'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.2s" '
        f'repeatCount="indefinite"/>█</text>',
    ])


# ── Ticker tape ───────────────────────────────────────────────────────────────
def render_ticker(tiles):
    items = []
    for t in tiles:
        sym  = t["label"][:10]
        col  = GRTXT if t["score"] >= 0 else RDTXT
        sign = "▲" if t["score"] >= 0 else "▼"
        items.append((sym, f"{sign} {t['metric']}", col))
    items = items * 2   # duplicate for seamless scroll

    px = 0
    parts = []
    for sym, metric, col in items:
        parts.append(
            f'<text x="{px}" y="14" font-family="{FONT}" font-size="10" '
            f'font-weight="600" fill="{WHITE}" dominant-baseline="central">'
            f'{esc(sym)}</text>'
        )
        parts.append(
            f'<text x="{px+82}" y="14" font-family="{FONT}" font-size="10" '
            f'fill="{col}" dominant-baseline="central">{esc(metric)}</text>'
        )
        parts.append(
            f'<text x="{px+148}" y="14" font-family="{FONT}" font-size="10" '
            f'fill="{BORDER}" dominant-baseline="central">│</text>'
        )
        px += 160

    ty = H - TICK_H
    return "\n".join([
        f'<rect x="0" y="{ty}" width="{W}" height="{TICK_H}" fill="{HEADER_BG}"/>',
        f'<rect x="0" y="{ty}" width="{W}" height="1" fill="{BORDER}"/>',
        f'<clipPath id="tc"><rect x="0" y="{ty}" width="{W-4}" height="{TICK_H}"/></clipPath>',
        f'<g clip-path="url(#tc)">',
        f'<g transform="translate(0,{ty})" style="animation:ticker 30s linear infinite">',
        *parts,
        "</g></g>",
    ])


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """\
<style>
  @keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
</style>"""


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Fetching GitHub data …")
    info, repos = fetch_all()
    print(f"  {len(repos)} repos")

    tiles       = make_tiles(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))
    print(f"  {len(tiles)} tiles · {total_stars} total stars")

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="KMCR Developer Market Heatmap">',
        "<title>KMCR Developer Market Heatmap</title>",
        CSS,
        # Background
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        # Heatmap tiles
        render_tiles(tiles),
        # Right sidebar
        render_sidebar(info, repos, tiles),
        # Top header
        render_header(total_stars),
        # Bottom ticker
        render_ticker(tiles),
        "</svg>",
    ]

    svg = "\n".join(svg_parts)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT}  ({len(svg):,} chars)")


if __name__ == "__main__":
    main()
