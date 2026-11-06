"""Draws the README figures into assets/. Run: python3 scripts/build_figures.py

Every number shown comes from the project repos or the portfolio. Each SVG embeds
only the font glyphs it uses, and needs the network only while building.
"""
import base64
import re
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

BROWSER = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
SIMPLE_ICONS = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{}.svg"

LIGHT = dict(paper="#F6F2E9", ink="#1E1C18", muted="#645F54", rule="#DCD5C6", a1="#C2410C", a2="#2F6FB5")
DARK = dict(paper="#171614", ink="#EFEAE0", muted="#A9A394", rule="#35322C", a1="#DD632C", a2="#4F8EDB")

TYPE = {
    "display": ("Newsreader", "opsz,wght@72,500", "Georgia,serif"),
    "serif": ("Newsreader", "opsz,wght@24,500", "Georgia,serif"),
    "mono": ("IBM Plex Mono", "wght@400", "Menlo,monospace"),
    "monob": ("IBM Plex Mono", "wght@500", "Menlo,monospace"),
}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=BROWSER), timeout=30).read()


def embed_font(key, chars):
    family, axes, _ = TYPE[key]
    query = urllib.parse.urlencode({"family": f"{family}:{axes}", "text": "".join(sorted(chars))})
    css = fetch(f"https://fonts.googleapis.com/css2?{query}").decode()
    url = re.search(r"url\((https://[^)]+)\)", css).group(1)
    data = base64.b64encode(fetch(url)).decode()
    return f"@font-face{{font-family:'f-{key}';src:url(data:font/woff2;base64,{data}) format('woff2');}}"


class Figure:
    def __init__(self, name, width, height, title):
        self.name, self.width, self.height, self.title = name, width, height, title
        self.body, self.styles, self.used = [], [], {}

    def add(self, markup):
        self.body.append(markup)

    def css(self, rules):
        self.styles.append(rules)

    def text(self, x, y, content, face="mono", size=14, color="ink", anchor="start", spacing=None, extra=""):
        self.used.setdefault(face, set()).update(content)
        track = f' letter-spacing="{spacing}"' if spacing else ""
        pull = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.add(f'<text x="{x}" y="{y}" font-size="{size}"{track}{pull} class="t-{face} f-{color}" {extra}>{escape(content)}</text>')

    def line(self, x1, y1, x2, y2, color="rule", weight=1, extra=""):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke-width="{weight}" class="s-{color}" {extra}/>')

    def save(self):
        def tokens(palette):
            return "".join(f"--{k}:{v};" for k, v in palette.items())

        colours = "".join(f".f-{k}{{fill:var(--{k})}}.s-{k}{{stroke:var(--{k});fill:none}}" for k in LIGHT)
        faces = "".join(f".t-{k}{{font-family:'f-{k}',{TYPE[k][2]}}}" for k in self.used)
        fonts = "".join(embed_font(k, v) for k, v in self.used.items())
        style = (
            f"{fonts}svg{{{tokens(LIGHT)}}}"
            f"@media (prefers-color-scheme:dark){{svg{{{tokens(DARK)}}}}}"
            f"{colours}{faces}{''.join(self.styles)}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}.motion{display:none}}"
        )
        document = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" role="img">'
            f"<title>{escape(self.title)}</title><style>{style}</style>"
            f'<rect x=".5" y=".5" width="{self.width-1}" height="{self.height-1}" rx="6" class="f-paper s-rule" style="fill:var(--paper)"/>'
            f'{"".join(self.body)}</svg>'
        )
        (OUT / self.name).write_text(document, encoding="utf-8")
        print(f"{self.name}: {len(document) // 1024} KB")


def header():
    fig = Figure("header.svg", 1000, 300, "Krrish Kothari, full-stack and applied AI/ML developer in Mumbai")
    fig.css(
        "@keyframes rule{from{stroke-dashoffset:150}to{stroke-dashoffset:0}}"
        ".draw{stroke-dasharray:150;animation:rule 1.2s .3s cubic-bezier(.3,.7,.2,1) backwards}"
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}}"
        ".name{animation:rise .9s cubic-bezier(.3,.7,.2,1) backwards}"
    )
    for x, y, dx, dy in [(18, 18, 1, 1), (982, 18, -1, 1), (18, 282, 1, -1), (982, 282, -1, -1)]:
        fig.line(x, y, x + 14 * dx, y, "muted")
        fig.line(x, y, x, y + 14 * dy, "muted")
    fig.text(44, 56, "github.com/Krrishkothari", color="muted")
    fig.add('<circle cx="828" cy="51" r="5" class="f-a1"/>')
    fig.text(956, 56, "Open to work", color="ink", anchor="end")
    fig.text(40, 164, "Krrish Kothari", face="display", size=116, spacing="-3", extra='style="" ')
    fig.body[-1] = fig.body[-1].replace('class="t-display', 'class="name t-display')
    fig.add('<line x1="44" y1="190" x2="194" y2="190" stroke-width="3" class="s-a1 draw"/>')
    fig.text(212, 198, "Full-stack and applied AI/ML developer", face="serif", size=26)
    fig.line(44, 226, 956, 226)
    for x, label, value in [(44, "BASED IN", "Mumbai, India"), (340, "STUDYING", "B.Tech CSE (AI/ML)"), (712, "GRADUATING", "2028")]:
        fig.text(x, 256, label, size=13, color="muted", spacing="1.5")
        fig.text(x + 12 + len(label) * 9.4, 256, value, size=14, face="monob")
    fig.save()


# Counted from scraper/locations.config.js in the DevgnCineX repo.
CINEMAS = {
    "Bhuj": 1, "Ghazipur": 1, "Hapur": 1, "Raebareli": 1, "Surendranagar": 1,
    "Gandhinagar": 2, "Ghaziabad": 2, "Mulund": 2, "Ratlam": 2,
    "Ahmedabad": 3, "Anand": 3, "Bahadurgarh": 3, "Guwahati": 3, "Meerut": 3, "Thane": 3,
    "Kanpur": 5, "Gurugram": 6,
}


def seats():
    assert len(CINEMAS) == 17 and sum(CINEMAS.values()) == 42
    row_gap, top = 25, 118
    fig = Figure("seats.svg", 1000, top + row_gap * len(CINEMAS) + 28,
                 "Seating chart with one seat per tracked cinema: 42 cinemas in 17 locations, 17 Devgn Cinex screens and 25 competitors")
    fig.css(
        "@keyframes seat{from{opacity:0;transform:translateY(6px)}}"
        ".row{animation:seat .55s ease-out backwards}"
    )
    seat = "M2 16V6a5 5 0 0 1 5-5h20a5 5 0 0 1 5 5v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"

    fig.text(44, 56, "FIG. 1", size=13, color="muted", spacing="1.5")
    fig.text(44, 112, "42 cinemas", face="display", size=54, spacing="-1")
    fig.text(44, 166, "17 locations", face="display", size=54, spacing="-1")
    for i, note in enumerate(["Each seat is one cinema the", "DevgnCineX scraper checks", "on BookMyShow every hour."]):
        fig.text(44, 212 + i * 22, note, size=14, color="muted")
    fig.add(f'<path d="{seat}" transform="translate(44 300)" class="f-a1"/>')
    fig.text(88, 314, "Devgn Cinex screen (17)", size=14)
    fig.add(f'<path d="{seat}" transform="translate(44 332)" class="f-a2"/>')
    fig.text(88, 346, "Local competitor (25)", size=14)

    centre, pitch = 730, 42
    fig.add(f'<path d="M{centre-190} 92Q{centre} 66 {centre+190} 92" stroke-width="2" stroke-linecap="round" class="s-ink"/>')
    fig.text(centre, 58, "SCREEN", size=13, color="muted", anchor="middle", spacing="4")
    for i, (place, count) in enumerate(CINEMAS.items()):
        y = top + i * row_gap
        fig.text(486, y + 14, place, size=14, color="muted", anchor="end")
        fig.line(498, y + 9, centre - (count * pitch) / 2 - 4, y + 9)
        cells = "".join(
            f'<path d="{seat}" transform="translate({centre - (count * pitch) / 2 + n * pitch + 4:.0f} {y})" '
            f'class="{"f-a1" if n == (count - 1) // 2 else "f-a2"}"/>'
            for n in range(count)
        )
        fig.add(f'<g class="row" style="animation-delay:{i * .06:.2f}s">{cells}</g>')
    fig.save()


def pipeline():
    fig = Figure("pipeline.svg", 1000, 284,
                 "DevgnCineX data flow: node-cron, Playwright scrapers, normalize and validate, prices.json, Express API, React dashboard")
    fig.text(44, 48, "FIG. 2", size=13, color="muted", spacing="1.5")
    fig.text(120, 48, "How a price gets from BookMyShow to the dashboard", size=14, color="muted")
    rail_y, first, step = 174, 104, 158
    stops = [
        (("node-cron",), ("every hour",)),
        (("Playwright", "scrapers"), ("3 locations at", "a time, failures", "retried one by one")),
        (("Normalize", "and validate"), ("required fields", "checked")),
        (("prices.json",), ("writes batched", "every 15 s")),
        (("Express API",), ("filters and", "price history")),
        (("React", "dashboard"), ("comparison and", "Excel export")),
    ]
    last = first + step * (len(stops) - 1)
    route = f"M{first} {rail_y}H{last + 40}"
    fig.add(f'<path d="{route}" stroke-width="2" class="s-ink"/>')
    fig.add(f'<path d="M{last+32} {rail_y-6}l9 6-9 6" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" class="s-ink"/>')
    # Retry arc: failed locations go back through the scraper stop.
    retry = first + step
    fig.add(
        f'<path d="M{retry + 38} {rail_y - 1}C{retry + 38} {rail_y - 38} {retry - 38} {rail_y - 38} {retry - 38} {rail_y - 3}" '
        'stroke-width="1.5" class="s-muted"/>'
    )
    fig.add(
        f'<path d="M{retry - 44} {rail_y - 11}l6 8 6-8" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" class="s-muted"/>'
    )
    for begin in (0, 2.2, 4.4):
        fig.add(
            f'<circle r="5" class="f-a1 motion"><animateMotion dur="6.6s" begin="-{begin}s" repeatCount="indefinite" path="{route}"/></circle>'
        )
    for i, (name, notes) in enumerate(stops):
        x = first + step * i
        fig.add(f'<circle cx="{x}" cy="{rail_y}" r="8" stroke-width="2" class="s-ink" style="fill:var(--paper)"/>')
        for j, part in enumerate(reversed(name)):
            fig.text(x, rail_y - 52 - j * 24, part, face="serif", size=20, anchor="middle")
        for j, part in enumerate(notes):
            fig.text(x, rail_y + 36 + j * 20, part, size=13, color="muted", anchor="middle")
    fig.save()


def eye_closure():
    fig = Figure("eye-closure.svg", 1000, 280,
                 "Driver Sleep Detection alert stages: under 3 seconds is ignored as a blink, at 3 seconds an Arduino cuts the motor relay and sounds a buzzer, at 5 seconds an ESP32 sends a Telegram alert")
    origin, per_second = 72, 142
    x_at = lambda s: origin + s * per_second
    top, bottom = 104, 204
    fig.css(
        "@keyframes play{0%{transform:translateX(0)}68.75%,75%{transform:translateX(781px)}76%,100%{transform:translateX(0)}}"
        ".head{animation:play 8s linear infinite}"
        "@keyframes lid{0%{transform:scaleY(1)}4%,75%{transform:scaleY(.08)}79%,100%{transform:scaleY(1)}}"
        ".lid{transform-box:fill-box;transform-origin:center;animation:lid 8s linear infinite}"
        "@keyframes stage1{0%,37%{opacity:.35}37.5%,75%{opacity:1}76%,100%{opacity:.35}}"
        "@keyframes stage2{0%,62%{opacity:.35}62.5%,75%{opacity:1}76%,100%{opacity:.35}}"
        ".one{animation:stage1 8s linear infinite}.two{animation:stage2 8s linear infinite}"
    )
    fig.text(44, 48, "FIG. 3", size=13, color="muted", spacing="1.5")
    fig.text(120, 48, "What happens the longer the driver's eyes stay closed", size=14, color="muted")

    fig.add(f'<rect x="{x_at(3)}" y="{top}" width="{per_second*2}" height="{bottom-top}" class="f-a1 one" style="fill-opacity:.13"/>')
    fig.add(f'<rect x="{x_at(5)}" y="{top}" width="{per_second}" height="{bottom-top}" class="f-a1 two" style="fill-opacity:.3"/>')
    fig.text(x_at(0) + 16, top + 42, "Under 3 s", face="serif", size=20)
    fig.text(x_at(0) + 16, top + 66, "Ignored as a normal blink", size=13, color="muted")
    fig.text(x_at(3) + 16, top + 42, "Arduino", face="serif", size=20)
    fig.text(x_at(3) + 16, top + 66, "Cuts the motor relay", size=13, color="muted")
    fig.text(x_at(3) + 16, top + 84, "and sounds a buzzer", size=13, color="muted")
    fig.text(x_at(5) + 12, top + 42, "ESP32", face="serif", size=20)
    fig.text(x_at(5) + 12, top + 66, "Sends a", size=13, color="muted")
    fig.text(x_at(5) + 12, top + 84, "Telegram alert", size=13, color="muted")

    fig.line(x_at(0), bottom, x_at(6), bottom, "ink", 2)
    for s in range(7):
        fig.line(x_at(s), bottom, x_at(s), bottom + 7, "ink", 2 if s in (3, 5) else 1)
        fig.text(x_at(s), bottom + 26, f"{s} s", size=13, color="ink" if s in (3, 5) else "muted", anchor="middle",
                 face="monob" if s in (3, 5) else "mono")
    fig.text(44, 262, "Opening the eyes restores motor power and silences the buzzer.", size=13, color="muted")

    eye = "M-22 0C-12-14 12-14 22 0C12 14-12 14-22 0Z"
    fig.add(
        f'<g class="head motion"><line x1="{x_at(0)}" y1="{top-14}" x2="{x_at(0)}" y2="{top}" stroke-width="2" class="s-ink"/>'
        f'<circle cx="{x_at(0)}" cy="{bottom}" r="6" class="f-a1"/>'
        f'<g transform="translate({x_at(0)} {top-30})"><g class="lid"><path d="{eye}" stroke-width="2" vector-effect="non-scaling-stroke" class="s-ink" style="fill:var(--paper)"/>'
        '<circle r="6" class="f-ink"/></g></g></g>'
    )
    fig.save()


# (label, detail, start as (year, month), end as (year, month) inclusive, colour, still running)
HISTORY = [
    ("B.Tech CSE (AI/ML)", "Atlas SkillTech University, Jul 2024 to Jun 2028", (2024, 7), None, "a2"),
    ("Rotaract Club", "Finance Secretary, Aug 2024 to May 2025", (2024, 8), (2025, 5), "a2"),
    ("Cognifyz Technologies", "ML Intern, Apr to May 2025", (2025, 4), (2025, 5), "a1"),
    ("SPARC Society", "Esports Co-Head, since Aug 2025", (2025, 8), None, "a2"),
    ("Sypha AI", "Software Development Intern, Nov 2025 to Jan 2026", (2025, 11), (2026, 1), "a1"),
    ("ODOO x ADANI hackathon", "Finalist, Jan 2026", (2026, 1), "point", "ink"),
    ("Devgn Cinex", "AI Intern, May to Aug 2026", (2026, 5), (2026, 8), "a1"),
]


def timeline():
    row, top, left, right = 50, 94, 462, 956
    start, months = (2024, 7), 30
    per_month = (right - left) / months
    x_at = lambda ym, end=False: left + ((ym[0] - start[0]) * 12 + ym[1] - start[1] + (1 if end else 0)) * per_month
    bottom = top + row * len(HISTORY)
    fig = Figure("timeline.svg", 1000, bottom + 62,
                 "Timeline from July 2024 of education, internships at Cognifyz, Sypha AI and Devgn Cinex, leadership roles and a hackathon final")
    fig.css(
        "@keyframes grow{from{transform:scaleX(0)}}"
        ".bar{transform-box:fill-box;transform-origin:left;animation:grow .9s cubic-bezier(.3,.7,.2,1) backwards}"
    )
    fig.add(
        '<defs>' + "".join(
            f'<linearGradient id="fade-{c}"><stop offset=".7" stop-color="var(--{c})"/><stop offset="1" stop-color="var(--{c})" stop-opacity="0"/></linearGradient>'
            for c in ("a2",)
        ) + '</defs>'
    )
    fig.text(44, 48, "FIG. 4", size=13, color="muted", spacing="1.5")
    fig.text(120, 48, "Education, internships and roles since 2024", size=14, color="muted")
    fig.add('<rect x="680" y="38" width="14" height="10" rx="3" class="f-a1"/>')
    fig.text(700, 48, "Internship", size=13, color="muted")
    fig.add('<rect x="802" y="38" width="14" height="10" rx="3" class="f-a2"/>')
    fig.text(822, 48, "Study, leadership", size=13, color="muted")

    for label, ym in [("Jul 2024", (2024, 7)), ("Jan 2025", (2025, 1)), ("Jul 2025", (2025, 7)), ("Jan 2026", (2026, 1)), ("Jul 2026", (2026, 7))]:
        x = x_at(ym)
        fig.line(round(x, 1), top - 8, round(x, 1), bottom, "rule")
        fig.text(round(x, 1), bottom + 24, label, size=13, color="muted", anchor="middle")

    for i, (name, detail, begin, end, colour) in enumerate(HISTORY):
        y = top + i * row
        fig.text(44, y + 15, name, face="serif", size=19)
        fig.text(44, y + 34, detail, size=12.5, color="muted")
        delay = f"animation-delay:{.15 + i * .1:.2f}s"
        x0 = round(x_at(begin), 1)
        if end == "point":
            fig.add(f'<circle cx="{x0}" cy="{y + 16}" r="7" class="f-ink"/>')
        elif end is None:
            fig.add(f'<rect x="{x0}" y="{y + 7}" width="{right - x0:.1f}" height="18" rx="4" class="bar" fill="url(#fade-{colour})" style="{delay}"/>')
        else:
            width = round(x_at(end, True) - x0, 1)
            fig.add(f'<rect x="{x0}" y="{y + 7}" width="{width}" height="18" rx="4" class="bar f-{colour}" style="{delay}"/>')
    fig.text(44, bottom + 46, "A bar that fades out is still running.", size=12.5, color="muted")
    fig.save()


# (name, Simple Icons slug or two-letter mark where no icon exists)
TOOLS = {
    "Languages": [("Python", "python"), ("JavaScript", "javascript"), ("Java", "openjdk"), ("C", "c"), ("C++", "cplusplus"), ("C#", "#C#"), ("PHP", "php")],
    "Frontend": [("React", "react"), ("Next.js", "nextdotjs"), ("AngularJS", "#Ng"), ("Tailwind CSS", "tailwindcss")],
    "Backend": [("Node.js", "nodedotjs"), ("Express", "express"), ("FastAPI", "fastapi"), ("Flask", "flask"), ("Django", "django"), ("Spring Boot", "springboot")],
    "Data": [("PostgreSQL", "postgresql"), ("MySQL", "mysql"), ("SQL Server", "#SQ"), ("MongoDB", "mongodb"), ("Firebase", "firebase"), ("Redis", "redis")],
    "AI/ML": [("LangChain", "langchain"), ("Gemini API", "googlegemini")],
    "Other": [("Docker", "docker"), ("Azure", "#Az"), ("Playwright", "#Pw"), ("Postman", "postman"), ("Git", "git")],
}


def tools():
    row, top = 58, 80
    names = ", ".join(n for group in TOOLS.values() for n, _ in group)
    fig = Figure("tools.svg", 1000, top + row * len(TOOLS) + 12, f"Tools I've used: {names}")
    fig.text(44, 48, "TOOLS I'VE USED", size=13, color="muted", spacing="1.5")
    for i, (group, items) in enumerate(TOOLS.items()):
        y = top + i * row
        if i:
            fig.line(44, y - 12, 956, y - 12)
        fig.text(44, y + 23, group, face="serif", size=19)
        x = 170
        for name, mark in items:
            fig.add(f'<rect x="{x + .5}" y="{y + .5}" width="33" height="33" rx="6" stroke-width="1" class="s-rule"/>')
            if mark.startswith("#"):
                fig.text(x + 17, y + 22, mark[1:], size=12.5, face="monob", anchor="middle")
            else:
                path = re.search(r' d="([^"]+)"', fetch(SIMPLE_ICONS.format(mark)).decode()).group(1)
                fig.add(f'<path transform="translate({x + 7} {y + 7}) scale(.8333)" d="{path}" class="f-ink"/>')
            fig.text(x + 42, y + 22, name, size=14)
            x += 42 + len(name) * 8.5 + 20
        assert x <= 980, f"{group} row overflows"
    fig.save()


if __name__ == "__main__":
    header()
    seats()
    pipeline()
    eye_closure()
    timeline()
    tools()
