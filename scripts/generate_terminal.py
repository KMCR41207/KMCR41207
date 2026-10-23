#!/usr/bin/env python3
"""KMCR GitHub profile SVG: a detailed Formula 1 car drawn ONLY with ASCII text.

This script uses the Python standard library and is compatible with GitHub Actions.
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER = "KMCR41207"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "terminal-profile.svg"
BG = "#080B12"
PANEL = "#101D35"
BORDER = "#263C68"
BLUE = "#6D9EFF"
WHITE = "#F5F7FA"
MUTED = "#8A94A6"
ACCENT = "#78B8FF"
RED = "#F34355"
YELLOW = "#FFD447"

FONT = "'Courier New',Consolas,'DejaVu Sans Mono',monospace"


def esc(value):
    return html.escape(str(value), quote=True)


def text(x, y, content, size=15, color=WHITE, weight=400, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'xml:space="preserve" {extra}>{esc(content)}</text>')


def rule(y):
    return f'<path d="M420 {y} H1070" stroke="{BORDER}" stroke-dasharray="3 6" />'


def item(y, label, value):
    return text(438, y, label, 15, BLUE, 600) + text(660, y, value, 15)


def api_json(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "KMCR-profile-svg"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=9) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        print(f"GitHub API unavailable: {error}")
        return None


def public_stats():
    user = api_json(f"https://api.github.com/users/{USER}")
    repos = user.get("public_repos", "—") if isinstance(user, dict) else "—"
    followers = user.get("followers", "—") if isinstance(user, dict) else "—"
    stars = 0
    complete = True
    for page in range(1, 16):
        entries = api_json(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        if not isinstance(entries, list):
            complete = False
            break
        stars += sum(entry.get("stargazers_count", 0) for entry in entries)
        if len(entries) < 100:
            break
    else:
        complete = False
    return str(repos), str(followers), str(stars) if complete else "—"


# The car is not an image, bitmap, path, or an embedded file.
# Each visible part, including tyres, halo, rear wing, sidepods, and front wing,
# is drawn as an individually colored ASCII character.
def formula_one_ascii():
    W, H = 98, 29
    cells = [[None for _ in range(W)] for _ in range(H)]

    def put(x, y, color):
        if 0 <= x < W and 0 <= y < H:
            cells[y][x] = color

    def polygon(points, color):
        for y in range(H):
            for x in range(W):
                crossed = False
                j = len(points) - 1
                for i in range(len(points)):
                    x1, y1 = points[i]
                    x2, y2 = points[j]
                    if (y1 > y) != (y2 > y):
                        if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                            crossed = not crossed
                    j = i
                if crossed:
                    put(x, y, color)

    def ellipse(cx, cy, rx, ry, color, inner=0):
        for y in range(H):
            for x in range(W):
                r = ((x-cx)/rx)**2 + ((y-cy)/ry)**2
                if inner <= r <= 1:
                    put(x, y, color)

    def line(x1, y1, x2, y2, color, width=0):
        steps = max(1, int(3 * max(abs(x2-x1),abs(y2-y1))))
        for i in range(steps+1):
            t = i / steps
            x = round(x1+(x2-x1)*t)
            y = round(y1+(y2-y1)*t)
            for dy in range(-width,width+1):
                for dx in range(-width,width+1):
                    put(x+dx,y+dy,color)

    # Undertray and dramatic narrow diffuser; rear of car is at left.
    polygon([(15,20),(41,19),(64,20),(88,23),(94,24),(93,26),(12,26),(9,23)], "carbon")
    line(11,26,89,26,"edge")
    polygon([(6,24),(24,24),(18,27),(4,27)], "carbon")

    # Tall Red Bull style rear wing, two supports and rear aero flaps.
    polygon([(4,9),(24,9),(22,12),(4,13)], "wing")
    line(4,9,23,9,"edge")
    polygon([(3,8),(6,8),(6,18),(4,18)], "wing")
    polygon([(17,11),(19,11),(23,21),(21,21)], "carbon")
    polygon([(10,13),(24,13),(24,15),(9,15)], "blue")

    # Engine cover and air intake above driver's seat.
    polygon([(20,20),(27,15),(37,13),(47,14),(55,17),(64,20)], "body")
    polygon([(40,14),(44,8),(49,8),(50,14)], "body")
    line(44,8,49,8,"edge")
    polygon([(34,15),(44,13),(50,15),(48,16),(34,17)], "blue")

    # Halo hoop around the driver's helmet. Visor is deliberately pale.
    ellipse(53,16,4,3,"helmet")
    ellipse(54,15,2.2,1.4,"visor")
    line(47,13,49,10,"edge")
    line(49,10,59,11,"edge")
    line(59,11,62,17,"edge")
    line(53,11,53,18,"carbon")
    line(49,10,59,11,"blue")

    # Enlarged sculpted sidepod, floor and floor-edge details.
    polygon([(27,18),(39,16),(60,17),(69,22),(66,25),(30,24)], "body")
    polygon([(31,19),(41,17),(58,19),(62,21),(47,22),(31,22)], "blue")
    polygon([(30,22),(55,23),(65,24),(62,25),(29,25)], "shadow")
    line(31,18,47,17,"edge")
    line(47,22,64,23,"carbon")
    line(30,25,67,25,"red")

    # Racing bull inspired red/yellow livery made of character clusters.
    polygon([(43,19),(48,18),(52,19),(50,21),(43,21)], "yellow")
    polygon([(49,20),(53,19),(58,20),(56,22),(51,22)], "red")
    line(51,18,55,18,"yellow")
    line(57,20,61,20,"yellow")

    # Long low nose and front suspension arms.
    polygon([(60,19),(76,19),(91,23),(91,25),(66,23)], "body")
    line(65,19,79,20,"edge")
    line(73,21,87,25,"carbon")
    line(78,19,87,24,"carbon")
    line(76,24,87,21,"carbon")

    # Front wing, multiple aerodynamic layers, nose tip and wing tips.
    polygon([(85,23),(97,23),(97,25),(83,25)], "wing")
    polygon([(83,26),(98,26),(98,28),(79,28)], "blue")
    line(85,23,97,23,"edge")
    line(80,28,97,28,"red")
    line(96,23,96,27,"edge")

    # Wheels are placed in the foreground, over body and suspension.
    # Yellow Pirelli-style ring plus dark textured rubber and bright axle.
    for cx,cy,rx,ry in [(24,23,8,5.7),(79,23,7.8,5.7)]:
        ellipse(cx,cy,rx+0.4,ry+0.4,"tire_outer")
        ellipse(cx,cy,rx-0.2,ry-0.25,"tire")
        ellipse(cx,cy,rx-1.1,ry-0.7,"rim_yellow",0.78)
        ellipse(cx,cy,rx-2.4,ry-1.9,"hub")
        ellipse(cx,cy,2.6,1.9,"carbon")
        ellipse(cx,cy,1.4,1.1,"axle")
        line(cx-rx+1,cy-3,cx-rx+3,cy-4,"tire_highlight")

    colors = {
        "tire_outer":"#718198", "tire":"#273447", "rim_yellow":"#FFD447",
        "hub":"#5E718A", "axle":"#EFF5FE", "tire_highlight":"#CBD5E6",
        "carbon":"#78889F", "shadow":"#172845", "body":"#274F9C",
        "blue":"#397CED", "edge":"#90C8FF", "wing":"#2353AF",
        "helmet":"#EEEFF2", "visor":"#202B40", "yellow":"#FFD647",
        "red":"#F34E52"
    }
    textures = {
        "tire_outer":"@", "tire":"%", "rim_yellow":"o", "hub":"O", "axle":"@",
        "tire_highlight":"+", "carbon":"=", "shadow":":", "body":"#",
        "blue":"@", "edge":"/", "wing":"#", "helmet":"@",
        "visor":"-", "yellow":"X", "red":"*",
    }

    # Compose each row as runs of SVG text with identical color. Every visible
    # car pixel remains a literal monospace character, not a vector drawing.
    out = []
    start_x, start_y = 26, 115
    char_width, row_height = 3.40, 6.50
    font_size = 9.4
    for y,row in enumerate(cells):
        group = []
        i = 0
        while i < W:
            if row[i] is None:
                i+=1
                continue
            typ = row[i]
            j = i
            while j < W and row[j] == typ:
                j+=1
            chars = textures[typ] * (j-i)
            # Horizontal character squashing allows >95 columns in the left pane.
            out.append(text(0,0,chars,font_size,colors[typ],600,
                f'transform="translate({start_x+i*char_width:.2f} {start_y+y*row_height:.2f}) scale(0.615 1)"'))
            i=j
    return out


def main():
    repos, followers, stars = public_stats()
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="570" viewBox="0 0 1120 570" role="img" aria-label="Developer profile with an ASCII Formula One car">',
        '<defs><linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{PANEL}"/>'
        '</linearGradient></defs>',
        f'<rect width="1120" height="570" rx="20" fill="url(#panel)" stroke="{BORDER}" stroke-width="2"/>',
        f'<path d="M392 60 V520" stroke="{BORDER}"/>',
        '<circle cx="35" cy="32" r="6" fill="#F07178"/>',
        '<circle cx="58" cy="32" r="6" fill="#F1C26B"/>',
        '<circle cx="81" cy="32" r="6" fill="#64CA9E"/>',
        text(108,38,"kmcr@github: ~/profile",14,MUTED),
        text(44,92,"INITIALIZING PROFILE...",15,ACCENT),
        rule(62),
    ]
    parts += formula_one_ascii()
    parts += [
        text(52,315,"// RB-RACING  |  ASCII SPEC",12,YELLOW,600),
        f'<path d="M40 326 H347" stroke="{BORDER}"/>',
        text(46,353,"< developer / designer >",17,WHITE,600),
        text(46,384,"Based in Hyderabad, India",15,MUTED),
        text(46,415,"Building products that matter.",14,ACCENT),
        text(46,466,"STATUS: OPEN TO BUILD",15,BLUE),
        text(46,501,"github.com/KMCR41207",15,WHITE),
        text(438,99,"K MANI CHARAN REDDY",28,WHITE,700),
        text(438,131,"FULL-STACK DEVELOPER  /  UI/UX DESIGNER",16,ACCENT),
        rule(153),
    ]
    details = [
        (183,"Role","Developer & UI/UX Designer"),
        (211,"Education","B.Tech CSE - MLRIT (2029)"),
        (239,"Location","Hyderabad, Telangana, India"),
        (267,"Frontend","React, TypeScript, JS, Tailwind"),
        (295,"Backend","Node.js, REST APIs, MongoDB"),
        (323,"Platforms","Supabase, Vercel, GitHub"),
        (351,"Design tools","Figma, Cursor"),
        (379,"Languages","English, Telugu, Hindi"),
        (407,"Passions","Cars, Bikes, Photography"),
    ]
    for y,key,value in details:
        parts.append(item(y,key,value))
    parts += [
        rule(430),
        text(438,461,"GITHUB  /  PUBLIC ACTIVITY",17,BLUE,700),
        item(493,"Repositories",repos),
        item(519,"Followers",followers),
        text(821,493,"Total stars",15,BLUE,600),
        text(977,493,stars),
        text(821,519,"User",15,BLUE,600),
        text(977,519,USER),
        text(438,551,"Automatically refreshed with GitHub Actions",12,MUTED),
        '</svg>',
    ]
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text("\n".join(parts),encoding="utf-8")
    print(f"Wrote {OUTPUT}")

if __name__=="__main__":
    main()
