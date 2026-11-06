#!/usr/bin/env python3
"""
KMCR GitHub profile SVG with an animated ASCII Formula 1 car.

The car is entirely character-based ASCII art, rendered as SVG text with
smooth entrance animation, wheel rotation, engine idle, and speed effects.
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

# Motorsport-inspired palette
BG = "#080B12"
PANEL = "#101D35"
BORDER = "#263C68"
BLUE = "#397CED"
RACING_BLUE = "#245BDB"
WHITE = "#F5F7FA"
MUTED = "#8A94A6"
ACCENT = "#78B8FF"
RED = "#F34355"
YELLOW = "#FFD447"
CARBON = "#78889F"

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
    return text(438, y, label, 15, RACING_BLUE, 600) + text(660, y, value, 15)


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


def formula_one_ascii():
    """
    Modern F1 car rendered as pure ASCII art with layered SVG groups for animation.
    Each layer (rear wing, wheels, body, front wing, speed effects) is independently
    animatable via CSS keyframes.
    """
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

    # === REAR WING & SUPPORTS ===
    polygon([(4,9),(24,9),(22,12),(4,13)], "wing")
    line(4,9,23,9,"edge")
    polygon([(3,8),(6,8),(6,18),(4,18)], "wing")
    polygon([(17,11),(19,11),(23,21),(21,21)], "carbon")
    polygon([(10,13),(24,13),(24,15),(9,15)], "blue")

    # === UNDERTRAY & DIFFUSER ===
    polygon([(15,20),(41,19),(64,20),(88,23),(94,24),(93,26),(12,26),(9,23)], "carbon")
    line(11,26,89,26,"edge")
    polygon([(6,24),(24,24),(18,27),(4,27)], "carbon")

    # === ENGINE COVER & AIR INTAKE ===
    polygon([(20,20),(27,15),(37,13),(47,14),(55,17),(64,20)], "body")
    polygon([(40,14),(44,8),(49,8),(50,14)], "body")
    line(44,8,49,8,"edge")
    polygon([(34,15),(44,13),(50,15),(48,16),(34,17)], "blue")

    # === HALO & HELMET ===
    ellipse(53,16,4,3,"helmet")
    ellipse(54,15,2.2,1.4,"visor")
    line(47,13,49,10,"edge")
    line(49,10,59,11,"edge")
    line(59,11,62,17,"edge")
    line(53,11,53,18,"carbon")
    line(49,10,59,11,"blue")

    # === SIDEPOD & FLOOR ===
    polygon([(27,18),(39,16),(60,17),(69,22),(66,25),(30,24)], "body")
    polygon([(31,19),(41,17),(58,19),(62,21),(47,22),(31,22)], "blue")
    polygon([(30,22),(55,23),(65,24),(62,25),(29,25)], "shadow")
    line(31,18,47,17,"edge")
    line(47,22,64,23,"carbon")
    line(30,25,67,25,"red")

    # === RACING LIVERY ===
    polygon([(43,19),(48,18),(52,19),(50,21),(43,21)], "yellow")
    polygon([(49,20),(53,19),(58,20),(56,22),(51,22)], "red")
    line(51,18,55,18,"yellow")
    line(57,20,61,20,"yellow")

    # === NOSE & FRONT SUSPENSION ===
    polygon([(60,19),(76,19),(91,23),(91,25),(66,23)], "body")
    line(65,19,79,20,"edge")
    line(73,21,87,25,"carbon")
    line(78,19,87,24,"carbon")
    line(76,24,87,21,"carbon")

    # === FRONT WING ===
    polygon([(85,23),(97,23),(97,25),(83,25)], "wing")
    polygon([(83,26),(98,26),(98,28),(79,28)], "blue")
    line(85,23,97,23,"edge")
    line(80,28,97,28,"red")
    line(96,23,96,27,"edge")

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

    layers = {
        "rear_wing": [],
        "rear_wheel": [],
        "body": [],
        "front_wheel": [],
        "front_wing": [],
    }

    # Assign cells to logical layers for animation
    start_x, start_y = 26, 115
    char_width, row_height = 3.40, 6.50
    font_size = 9.4

    for y,row in enumerate(cells):
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
            char_svg = text(0,0,chars,font_size,colors[typ],600,
                f'transform="translate({start_x+i*char_width:.2f} {start_y+y*row_height:.2f}) scale(0.615 1)"')
            
            # Layer assignment based on x position
            if i < 25:
                layers["rear_wing"].append(char_svg)
            elif i < 35 and 20 <= y <= 28:
                layers["rear_wheel"].append(char_svg)
            elif i > 70 and 20 <= y <= 28:
                layers["front_wheel"].append(char_svg)
            elif i > 80:
                layers["front_wing"].append(char_svg)
            else:
                layers["body"].append(char_svg)
            i=j

    # === REAR WHEEL (separate, for rotation animation) ===
    cx,cy,rx,ry = 24,23,8,5.7
    wheel_chars = []
    for dy in range(-6,7):
        for dx in range(-9,10):
            x,y = cx+dx,cy+dy
            if not (0 <= x < W and 0 <= y < H):
                continue
            r = (dx/rx)**2 + (dy/ry)**2
            if r > 1.2:
                continue
            if r > 0.95:
                c,tex = colors["tire_outer"],textures["tire_outer"]
            elif r > 0.85:
                c,tex = colors["tire"],textures["tire"]
            elif r > 0.78:
                c,tex = colors["rim_yellow"],textures["rim_yellow"]
            elif r > 0.35:
                c,tex = colors["hub"],textures["hub"]
            elif r > 0.20:
                c,tex = colors["carbon"],textures["carbon"]
            else:
                c,tex = colors["axle"],textures["axle"]
            wheel_chars.append(text(0,0,tex,font_size,c,600,
                f'transform="translate({start_x+x*char_width:.2f} {start_y+y*row_height:.2f}) scale(0.615 1)"'))
    layers["rear_wheel"] = wheel_chars

    # === FRONT WHEEL (separate, for rotation animation) ===
    cx,cy,rx,ry = 79,23,7.8,5.7
    wheel_chars = []
    for dy in range(-6,7):
        for dx in range(-9,10):
            x,y = cx+dx,cy+dy
            if not (0 <= x < W and 0 <= y < H):
                continue
            r = (dx/rx)**2 + (dy/ry)**2
            if r > 1.2:
                continue
            if r > 0.95:
                c,tex = colors["tire_outer"],textures["tire_outer"]
            elif r > 0.85:
                c,tex = colors["tire"],textures["tire"]
            elif r > 0.78:
                c,tex = colors["rim_yellow"],textures["rim_yellow"]
            elif r > 0.35:
                c,tex = colors["hub"],textures["hub"]
            elif r > 0.20:
                c,tex = colors["carbon"],textures["carbon"]
            else:
                c,tex = colors["axle"],textures["axle"]
            wheel_chars.append(text(0,0,tex,font_size,c,600,
                f'transform="translate({start_x+x*char_width:.2f} {start_y+y*row_height:.2f}) scale(0.615 1)"'))
    layers["front_wheel"] = wheel_chars

    # === SPEED LINES (fade in/out effect behind car) ===
    speed_lines = []
    for i,sy in enumerate([125,140,155,170,185,200]):
        opacity = 0.15 + (i%3)*0.08
        speed_lines.append(f'<line x1="15" y1="{sy}" x2="45" y2="{sy}" '
                          f'stroke="{ACCENT}" stroke-width="1.5" opacity="{opacity}" '
                          f'stroke-dasharray="4 2"/>')
    layers["speed_effects"] = speed_lines

    return layers


def main():
    repos, followers, stars = public_stats()
    
    car_layers = formula_one_ascii()

    # CSS animations for the F1 car
    car_animations = """<style>
    @keyframes entrance { 
      0% { transform: translateX(-50px); opacity: 0; }
      40% { opacity: 1; }
      100% { transform: translateX(0); opacity: 1; }
    }
    @keyframes idle {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-0.8px); }
    }
    @keyframes wheelSpin {
      0%, 100% { opacity: 1; }
      25% { opacity: 0.92; }
      50% { opacity: 1; }
      75% { opacity: 0.88; }
    }
    @keyframes speedFade {
      0%, 100% { opacity: 0.2; }
      50% { opacity: 0.5; }
    }
    @keyframes exhaust {
      0%, 100% { opacity: 0.15; }
      50% { opacity: 0.35; }
    }
    #car-rear-wing { animation: entrance 1.2s ease-out, idle 3.5s ease-in-out 1.2s infinite; }
    #car-body { animation: entrance 1.4s ease-out, idle 3.2s ease-in-out 1.4s infinite; }
    #car-front-wing { animation: entrance 1.6s ease-out, idle 3.8s ease-in-out 1.6s infinite; }
    #car-rear-wheel { animation: entrance 1.3s ease-out, wheelSpin 0.9s linear 1.3s infinite; }
    #car-front-wheel { animation: entrance 1.5s ease-out, wheelSpin 0.85s linear 1.5s infinite; }
    #speed-effects { animation: speedFade 2.5s ease-in-out infinite; }
    </style>"""

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="570" viewBox="0 0 1120 570" '
        'role="img" aria-label="KMCR Developer Profile with Animated F1 Car">',
        '<title>KMCR — Full-Stack Developer</title>',
        car_animations,
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
        # F1 car with layered animation
        '<g id="speed-effects">',
        *car_layers["speed_effects"],
        '</g>',
        '<g id="car-rear-wing">',
        *car_layers["rear_wing"],
        '</g>',
        '<g id="car-rear-wheel">',
        *car_layers["rear_wheel"],
        '</g>',
        '<g id="car-body">',
        *car_layers["body"],
        '</g>',
        '<g id="car-front-wheel">',
        *car_layers["front_wheel"],
        '</g>',
        '<g id="car-front-wing">',
        *car_layers["front_wing"],
        '</g>',
        f'<path d="M40 326 H347" stroke="{BORDER}"/>',
        text(46,353,"< developer / designer >",17,WHITE,600),
        text(46,384,"Based in Hyderabad, India",15,MUTED),
        text(46,415,"Building products that matter.",14,ACCENT),
        text(46,466,"STATUS: OPEN TO BUILD",15,RACING_BLUE),
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
        text(438,461,"GITHUB  /  PUBLIC ACTIVITY",17,RACING_BLUE,700),
        item(493,"Repositories",repos),
        item(519,"Followers",followers),
        text(821,493,"Total stars",15,RACING_BLUE,600),
        text(977,493,stars),
        text(821,519,"User",15,RACING_BLUE,600),
        text(977,519,USER),
        text(438,551,"Automatically refreshed with GitHub Actions",12,MUTED),
        '</svg>',
    ]
    
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text("\n".join(parts),encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__=="__main__":
    main()
