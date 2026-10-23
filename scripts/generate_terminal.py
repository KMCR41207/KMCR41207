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
