#!/usr/bin/env python3
"""Generate a GitHub-profile terminal SVG with dynamic public GitHub stats.

Python standard library only. Safe to run locally (offline) or via Actions.
"""

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER = "KMCR41207"
OUTPUT = Path(__file__).resolve().parent.parent / "assets" / "terminal-profile.svg"

BG = "#080B12"
PANEL = "#101D35"
BORDER = "#263C68"
BLUE = "#6D9EFF"
BLUE_BRIGHT = "#245BDB"
WHITE = "#F5F7FA"
MUTED = "#8A94A6"
ACCENT = "#78B8FF"


def api_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "KMCR-profile-action"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        with urlopen(Request(url, headers=headers), timeout=12) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        print(f"Warning: GitHub API unavailable for {url}: {exc}")
        return None


def public_stats():
    info = api_json(f"https://api.github.com/users/{USER}")
    repos = info.get("public_repos", "—") if isinstance(info, dict) else "—"
    followers = info.get("followers", "—") if isinstance(info, dict) else "—"
    stars = 0
    page = 1
    complete = True
    while page <= 15:
        entries = api_json(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        if not isinstance(entries, list):
            complete = False
            break
        stars += sum(item.get("stargazers_count", 0) for item in entries)
        if len(entries) < 100:
            break
        page += 1
    else:
        complete = False
    return str(repos), str(followers), str(stars) if complete else "—"


def esc(value):
    return html.escape(str(value), quote=True)


def text(x, y, value, size=16, color=WHITE, weight="400", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" xml:space="preserve" {extra}>{esc(value)}</text>')


def rule(y):
    return f'<line x1="420" y1="{y}" x2="1070" y2="{y}" stroke="{BORDER}" stroke-dasharray="3 6" />'


def item(y, label, value):
    return text(438, y, label, 15, BLUE, "600") + text(660, y, value, 15, WHITE)


def main():
    repos, followers, stars = public_stats()
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="570" viewBox="0 0 1120 570" role="img" aria-label="K Mani Charan Reddy developer terminal profile">',
        '<defs><linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{BG}"/><stop offset="100%" stop-color="{PANEL}"/>'
        '</linearGradient></defs>',
        f'<rect width="1120" height="570" rx="20" fill="url(#panel)" stroke="{BORDER}" stroke-width="2"/>',
        f'<path d="M392 60 V520" stroke="{BORDER}" stroke-width="1" />',
        f'<circle cx="35" cy="32" r="6" fill="#f07178" />',
        f'<circle cx="58" cy="32" r="6" fill="#f1c26b" />',
        f'<circle cx="81" cy="32" r="6" fill="#64ca9e" />',
        text(108, 38, "kmcr@github: ~/profile", 14, MUTED),
        text(44, 92, "INITIALIZING PROFILE...", 15, ACCENT),
        rule(62),
    ]

    logo = [
        " K   K  M   M   CCCC   RRRR ",
        " K  K   MM MM  C       R   R",
        " KKK    M M M  C       RRRR ",
        " K  K   M   M  C       R R  ",
        " K   K  M   M   CCCC   R  RR",
    ]
    for i, ln in enumerate(logo):
        parts.append(text(38, 147 + 31 * i, ln, 17, ACCENT, "700"))
    parts.extend([
        f'<rect x="40" y="301" width="307" height="1" fill="{BORDER}" />',
        text(46, 342, "< developer / designer >", 17, WHITE, "600"),
        text(46, 374, "Based in Hyderabad, India", 15, MUTED),
        text(46, 406, "Building products that matter.", 14, ACCENT),
        text(46, 464, "STATUS: OPEN TO BUILD", 15, BLUE),
        text(46, 501, "github.com/KMCR41207", 15, WHITE),
        text(438, 99, "K MANI CHARAN REDDY", 28, WHITE, "700"),
        text(438, 131, "FULL-STACK DEVELOPER  /  UI/UX DESIGNER", 16, ACCENT),
        rule(153),
    ])

    details = [
        (183, "Role", "Developer & UI/UX Designer"),
        (211, "Education", "B.Tech CSE - MLRIT (2029)"),
        (239, "Location", "Hyderabad, Telangana, India"),
        (267, "Frontend", "React, TypeScript, JS, Tailwind"),
        (295, "Backend", "Node.js, REST APIs, MongoDB"),
        (323, "Platforms", "Supabase, Vercel, GitHub"),
        (351, "Design tools", "Figma, Cursor"),
        (379, "Languages", "English, Telugu, Hindi"),
        (407, "Passions", "Cars, Bikes, Photography"),
    ]
    for y, key, value in details:
        parts.append(item(y, key, value))
    parts.append(rule(430))
    parts.append(text(438, 461, "GITHUB  /  PUBLIC ACTIVITY", 17, BLUE, "700"))
    parts.append(item(493, "Repositories", repos))
    parts.append(item(519, "Followers", followers))
    parts.append(text(821, 493, "Total stars", 15, BLUE, "600"))
    parts.append(text(977, 493, stars, 15, WHITE))
    parts.append(text(821, 519, "User", 15, BLUE, "600"))
    parts.append(text(977, 519, USER, 15, WHITE))
    parts.append(text(438, 551, "Automatically refreshed with GitHub Actions", 12, MUTED))
    parts.append('</svg>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
