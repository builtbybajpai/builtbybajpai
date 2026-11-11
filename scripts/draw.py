"""Draw every plate in this profile from the files in data/.

    python scripts/draw.py

Writes assets/dark/*.svg (a night sky) and assets/light/*.svg (a printed star atlas).
No dependencies beyond the standard library.
"""
from __future__ import annotations

import csv
import hashlib
import math
import random
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OBSERVED = "12 Nov 2026"

SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', 'Times New Roman', serif"
MONO = "ui-monospace, 'SF Mono', 'Cascadia Mono', 'Segoe UI Mono', Consolas, Menlo, monospace"
SANS = "-apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(
        sky0="#02030a", sky1="#070b22", sky2="#111a46",
        ink="#eef1ff", dim="#9aa3c7", faint="#4b557f", rule="#1f2752",
        gold="#f6c46a", cyan="#86dcff", violet="#c3a2ff", rose="#ff8fa3",
        ground="#010208", groundtext="#7f88ad", frame="#232c5c",
        star=["#ffffff", "#e8eeff", "#cfe0ff", "#ffe9c2", "#ffd28a", "#bfe6ff"],
        day0="#0f1a3f", day1="#0c1636", horizon="#f6a85a",
        strip="#02030a", paper=False,
    ),
    "light": dict(
        sky0="#f7f2e7", sky1="#f2ebdc", sky2="#e9dfca",
        ink="#18203d", dim="#545c7a", faint="#a69e8a", rule="#d6ccb5",
        gold="#b5520f", cyan="#1c5a94", violet="#62379c", rose="#b23a55",
        ground="#18203d", groundtext="#d9d2c0", frame="#d6ccb5",
        star=["#18203d", "#1f2a52", "#2a3563", "#5a3a1c", "#7a3f12", "#1c4a7a"],
        day0="#f7f2e7", day1="#f7f2e7", horizon="#b5520f",
        strip="#f7f2e7", paper=True,
    ),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def seeded(*parts: object) -> random.Random:
    h = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def frame(w: int, h: int, t: dict, title: str, body: str, defs: str = "", style: str = "") -> str:
    reduce = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{esc(title)}">'
        f"<title>{esc(title)}</title>"
        f"<style>{style}{reduce}</style>"
        f'<defs><clipPath id="cl"><rect width="{w}" height="{h}" rx="20"/></clipPath>{defs}</defs>'
        f'<g clip-path="url(#cl)">{body}</g>'
        f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="19.5" fill="none" stroke="{t["frame"]}" stroke-width="1.5"/>'
        "</svg>"
    )


def sky_bg(w: int, h: int, t: dict, gid: str = "sky") -> tuple[str, str]:
    if t["paper"]:
        defs = (
            f'<radialGradient id="{gid}" cx="50%" cy="40%" r="75%">'
            f'<stop offset="0" stop-color="{t["sky0"]}"/><stop offset=".7" stop-color="{t["sky1"]}"/>'
            f'<stop offset="1" stop-color="{t["sky2"]}"/></radialGradient>'
        )
    else:
        defs = (
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{t["sky0"]}"/><stop offset=".65" stop-color="{t["sky1"]}"/>'
            f'<stop offset="1" stop-color="{t["sky2"]}"/></linearGradient>'
        )
    return defs, f'<rect width="{w}" height="{h}" fill="url(#{gid})"/>'


def scatter_stars(w: int, h: int, t: dict, n: int, seed: str, ymax: float | None = None, twinkle: float = 0.18) -> str:
    rnd = seeded(seed)
    out = []
    ymax = ymax or h
    for i in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, ymax)
        r = rnd.choice([0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.3, 1.6]) * (0.9 if t["paper"] else 1)
        c = rnd.choice(t["star"])
        o = rnd.uniform(0.35, 0.95)
        if rnd.random() < twinkle:
            d = rnd.uniform(0, 6)
            dur = rnd.uniform(2.8, 6.5)
            out.append(f'<circle class="tw" style="animation-delay:-{d:.2f}s;animation-duration:{dur:.2f}s" cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{c}" opacity="{o:.2f}"/>')
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{c}" opacity="{o:.2f}"/>')
    return "".join(out)


TWINKLE = ".tw{animation:tw 4s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.95}50%{opacity:.15}}"


def glow_filter(fid: str, std: float) -> str:
    return (
        f'<filter id="{fid}" x="-200%" y="-200%" width="500%" height="500%">'
        f'<feGaussianBlur stdDeviation="{std}" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


# ───────────────────────────── PLATE I · HERO ─────────────────────────────
def hero(t: dict) -> str:
    W, H = 1200, 580
    PX, PY = 905, 150  # celestial pole
    defs, bg = sky_bg(W, H, t)
    defs += glow_filter("g6", 6) + glow_filter("g2", 2)
    defs += '<filter id="blur40" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>'
    fade = t["sky0"]
    defs += (
        f'<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{fade}" stop-opacity=".94"/>'
        f'<stop offset=".42" stop-color="{fade}" stop-opacity=".78"/><stop offset=".62" stop-color="{fade}" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="meteor" x1="0" x2="1"><stop offset="0" stop-color="{t["ink"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{t["ink"]}" stop-opacity=".95"/></linearGradient>'
        f'<radialGradient id="lamp"><stop offset="0" stop-color="{t["gold"]}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{t["gold"]}" stop-opacity="0"/></radialGradient>'
    )
    body = [bg]

    if not t["paper"]:  # aurora wash
        body.append(
            '<g filter="url(#blur40)" opacity=".55">'
            f'<ellipse cx="760" cy="120" rx="320" ry="70" fill="#1d6f8a"><animate attributeName="opacity" values=".35;.7;.35" dur="14s" repeatCount="indefinite"/></ellipse>'
            f'<ellipse cx="1040" cy="210" rx="260" ry="60" fill="#5b3aa8"><animate attributeName="opacity" values=".6;.25;.6" dur="17s" repeatCount="indefinite"/></ellipse>'
            f'<ellipse cx="560" cy="60" rx="240" ry="40" fill="#1f4f9a" opacity=".5"/></g>'
        )
    else:  # atlas print: graticule
        g = []
        for r in range(80, 1100, 80):
            g.append(f'<circle cx="{PX}" cy="{PY}" r="{r}" fill="none" stroke="{t["rule"]}" stroke-width="1" stroke-dasharray="2 6"/>')
        for a in range(0, 360, 15):
            x2 = PX + 1400 * math.cos(math.radians(a))
            y2 = PY + 1400 * math.sin(math.radians(a))
            g.append(f'<line x1="{PX}" y1="{PY}" x2="{f(x2)}" y2="{f(y2)}" stroke="{t["rule"]}" stroke-width=".8" stroke-dasharray="1 7"/>')
        body.append("<g>" + "".join(g) + "</g>")

    body.append(scatter_stars(W, H, t, 230, "hero-field", ymax=480))

    # star trails: a long exposure around the pole, turning very slowly
    rnd = seeded("trails")
    trails = []
    for i in range(420):
        r = 14 + (rnd.random() ** 0.85) * 1050
        a0 = rnd.uniform(0, 360)
        span = rnd.uniform(16, 58)
        a1 = a0 + span
        x0, y0 = PX + r * math.cos(math.radians(a0)), PY + r * math.sin(math.radians(a0))
        x1, y1 = PX + r * math.cos(math.radians(a1)), PY + r * math.sin(math.radians(a1))
        c = rnd.choice(t["star"] + [t["gold"], t["cyan"]])
        sw = rnd.choice([0.6, 0.8, 1.0, 1.2, 1.5, 1.9])
        o = rnd.uniform(0.25, 0.85) if not t["paper"] else rnd.uniform(0.35, 0.8)
        trails.append(
            f'<path d="M{f(x0)} {f(y0)}A{f(r)} {f(r)} 0 0 1 {f(x1)} {f(y1)}" fill="none" stroke="{c}" '
            f'stroke-width="{sw}" stroke-linecap="round" opacity="{o:.2f}"/>'
        )
    body.append(
        f'<g>{"".join(trails)}<animateTransform attributeName="transform" type="rotate" '
        f'from="0 {PX} {PY}" to="360 {PX} {PY}" dur="900s" repeatCount="indefinite"/></g>'
    )
    # pole star
    body.append(
        f'<g filter="url(#g6)"><circle cx="{PX}" cy="{PY}" r="3.4" fill="{t["ink"]}"/></g>'
        f'<path d="M{PX-16} {PY}H{PX+16}M{PX} {PY-16}V{PY+16}" stroke="{t["ink"]}" stroke-width=".8" opacity=".7"/>'
    )

    # meteor
    body.append(
        '<g opacity="0"><g transform="rotate(27)"><line x1="0" y1="0" x2="150" y2="0" stroke="url(#meteor)" stroke-width="2" stroke-linecap="round"/>'
        f'<circle cx="150" cy="0" r="2.2" fill="{t["ink"]}" filter="url(#g2)"/></g>'
        '<animateTransform attributeName="transform" type="translate" values="520 30;520 30;760 152;760 152" keyTimes="0;.02;.1;1" dur="11s" '
        'repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;.02;.04;.1;1" dur="11s" repeatCount="indefinite"/>'
        "</g>"
    )

    body.append(f'<rect width="{W}" height="{H}" fill="url(#fadeL)"/>')

    # ground and observatory
    ground = (
        f"M0 {H}V515C180 500 380 497 560 492C700 488 800 470 880 466C960 462 1100 470 {W} 476V{H}Z"
    )
    body.append(f'<path d="{ground}" fill="{t["ground"]}"/>')
    DX, DY = 1010, 468  # dome base centre
    body.append(
        f'<g fill="{t["ground"]}">'
        f'<rect x="{DX-62}" y="{DY-44}" width="124" height="48"/>'
        f'<path d="M{DX-70} {DY-44}A70 70 0 0 1 {DX+70} {DY-44}Z"/>'
        f"</g>"
        # open slit with lamp light
        f'<path d="M{DX-9} {DY-112}L{DX+9} {DY-112}L{DX+12} {DY-44}L{DX-12} {DY-44}Z" fill="{t["gold"]}" opacity=".9"/>'
        f'<circle cx="{DX}" cy="{DY-70}" r="55" fill="url(#lamp)" opacity=".35"><animate attributeName="opacity" values=".25;.45;.25" dur="6s" repeatCount="indefinite"/></circle>'
        # telescope pointing at the pole
        f'<g transform="rotate(-38 {DX} {DY-78})"><rect x="{DX-6}" y="{DY-150}" width="12" height="78" rx="2" fill="{t["ground"]}"/></g>'
        # windows
        f'<rect x="{DX-40}" y="{DY-30}" width="10" height="14" fill="{t["gold"]}" opacity=".85"/>'
        f'<rect x="{DX+30}" y="{DY-30}" width="10" height="14" fill="{t["gold"]}" opacity=".55"/>'
    )
    # a few trees on the ridge
    trees = []
    for x, s in [(820, 1), (842, .7), (1110, .85), (1130, 1.1), (1158, .75), (680, .8)]:
        base = 470 if x > 800 else 488
        trees.append(f'<path d="M{x} {base-46*s}L{x+11*s} {base}H{x-11*s}Z" fill="{t["ground"]}"/>')
    body.append("".join(trees))

    # type
    body.append(
        f'<text x="72" y="118" font-family="{MONO}" font-size="15" letter-spacing="4.5" fill="{t["dim"]}">OBSERVING LOG  ·  PLATE I</text>'
        f'<text x="66" y="218" font-family="{SERIF}" font-size="96" fill="{t["ink"]}" letter-spacing="-1">Akshay Bajpai</text>'
        f'<text x="72" y="275" font-family="{SERIF}" font-style="italic" font-size="33" fill="{t["gold"]}">Wrangling AI, mostly after dark.</text>'
        f'<text font-family="{SANS}" font-size="21" fill="{t["dim"]}">'
        f'<tspan x="72" y="340">I build production LLM systems that answer to humans:</tspan>'
        f'<tspan x="72" y="370">agents, retrieval, and text-to-SQL that shows its work</tspan>'
        f'<tspan x="72" y="400">and waits for a person before it runs.</tspan></text>'
        f'<text x="72" y="552" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{t["groundtext"]}">'
        f"AI ENGINEER  ·  TELOMERE  ·  INDIA  ·  FIRST LIGHT 26 MAY 2026</text>"
    )
    return frame(W, H, t, "Akshay Bajpai. Wrangling AI, mostly after dark. A long-exposure night sky with star trails over an observatory whose lamp is on.", "".join(body), defs, TWINKLE)


# ───────────────────────────── PLATE II · MAGNITUDES ─────────────────────────────
def magnitudes(t: dict, n_commits: int, after_dark_pct: int) -> str:
    W, H = 1200, 400
    defs, bg = sky_bg(W, H, t, "skym")
    defs += glow_filter("gm", 3)
    cells = [
        ("775", "contributions this year", "all of them since first light in May", t["gold"]),
        ("662", "commits to the AI platform", "68% of every commit in that repo", t["cyan"]),
        ("107", "pull requests opened", "76 merged, the rest in review", t["violet"]),
        ("2,683", "files touched", "backend, agents, infra and UI", t["cyan"]),
        ("8,000+", "columns the reports agent reads", "across 193 tables, all approved", t["violet"]),
        (f"{after_dark_pct}%", "of commits land after dark", "between 18:00 and 05:00 IST", t["gold"]),
    ]
    body = [bg, scatter_stars(W, H, t, 70, "mag-field", twinkle=0.3)]
    body.append(
        f'<text x="56" y="56" font-family="{MONO}" font-size="15" letter-spacing="4.5" fill="{t["dim"]}">PLATE II  ·  MAGNITUDES</text>'
        f'<text x="{W-56}" y="56" text-anchor="end" font-family="{MONO}" font-size="14" letter-spacing="2" fill="{t["faint"]}">OBSERVED {OBSERVED.upper()}</text>'
        f'<line x1="56" y1="76" x2="{W-56}" y2="76" stroke="{t["rule"]}" stroke-width="1"/>'
    )
    cw, ch = (W - 112) / 3, 150
    for i, (num, l1, l2, col) in enumerate(cells):
        cx = 56 + (i % 3) * cw
        cy = 96 + (i // 3) * ch
        # sparkle sized by row
        sx, sy = cx + 14, cy + 44
        body.append(
            f'<g filter="url(#gm)" class="tw" style="animation-delay:-{i*0.9:.1f}s;animation-duration:{4+i*0.6:.1f}s">'
            f'<path d="M{sx} {sy-11}Q{sx+1.5} {sy-1.5} {sx+11} {sy}Q{sx+1.5} {sy+1.5} {sx} {sy+11}Q{sx-1.5} {sy+1.5} {sx-11} {sy}Q{sx-1.5} {sy-1.5} {sx} {sy-11}Z" fill="{col}"/></g>'
            f'<text x="{cx+36}" y="{cy+66}" font-family="{SERIF}" font-size="64" fill="{t["ink"]}">{esc(num)}</text>'
            f'<text x="{cx+38}" y="{cy+102}" font-family="{SANS}" font-size="19" font-weight="600" fill="{t["ink"]}">{esc(l1)}</text>'
            f'<text x="{cx+38}" y="{cy+128}" font-family="{SANS}" font-size="17" fill="{t["dim"]}">{esc(l2)}</text>'
        )
        if i % 3:
            body.append(f'<line x1="{cx-6}" y1="{cy+18}" x2="{cx-6}" y2="{cy+128}" stroke="{t["rule"]}" stroke-width="1"/>')
    return frame(W, H, t, "Magnitudes: 775 contributions this year; 662 commits to the AI platform, 68% of the repo; 107 pull requests, 76 merged; 2,683 files touched; 8,000+ columns across 193 tables; 80% of commits after dark.", "".join(body), defs, TWINKLE)


# ───────────────────────────── PLATE III · SKY CHART ─────────────────────────────
def load_commits() -> list[tuple[datetime, int]]:
    rows = []
    with open(DATA / "commits.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((datetime.strptime(r["when"], "%Y-%m-%d %H:%M"), int(r["lines"] or 0)))
    rows.sort()
    return rows


def smooth(pts: list[tuple[float, float]]) -> str:
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d


def sky_chart(t: dict, commits: list[tuple[datetime, int]]) -> str:
    W, H = 1200, 760
    X0, X1, YT, YB = 120, 1140, 128, 512
    start = datetime(2026, 6, 1)
    end = datetime(2026, 11, 13)
    span = (end - start).total_seconds()

    def X(dt: datetime) -> float:
        return X0 + (dt - start).total_seconds() / span * (X1 - X0)

    def Y(dt: datetime) -> float:
        h = dt.hour + dt.minute / 60
        s = (h - 6) % 24
        return YB - s / 24 * (YB - YT)

    YH = YB - 12 / 24 * (YB - YT)  # 18:00, the horizon

    defs, bg = sky_bg(W, H, t, "skys")
    defs += glow_filter("gs", 2.4) + glow_filter("gb", 5)
    defs += (
        f'<linearGradient id="day" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["horizon"]}" stop-opacity="{.16 if t["paper"] else .30}"/>'
        f'<stop offset=".10" stop-color="{t["day1"]}" stop-opacity="{0 if t["paper"] else .9}"/><stop offset="1" stop-color="{t["day0"]}" stop-opacity="{0 if t["paper"] else .9}"/></linearGradient>'
        f'<linearGradient id="curve" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["gold"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{t["gold"]}" stop-opacity="0"/></linearGradient>'
    )
    body = [bg]
    # night & day regions
    body.append(f'<rect x="{X0}" y="{f(YH)}" width="{X1-X0}" height="{f(YB-YH)}" fill="url(#day)"/>')
    if t["paper"]:
        body.append(f'<rect x="{X0}" y="{YT}" width="{X1-X0}" height="{f(YH-YT)}" fill="{t["sky2"]}" opacity=".55"/>')
    # grid: hours
    for hh, lab in [(6, "06:00"), (12, "NOON"), (18, "18:00"), (0, "MIDNIGHT"), (3, "03:00")]:
        y = Y(datetime(2026, 1, 1, hh))
        if hh == 6:
            y = YB
        dash = "" if hh == 18 else ' stroke-dasharray="2 6"'
        col = t["horizon"] if hh == 18 else t["rule"]
        sw = 1.6 if hh == 18 else 1
        body.append(f'<line x1="{X0}" y1="{f(y)}" x2="{X1}" y2="{f(y)}" stroke="{col}" stroke-width="{sw}"{dash}/>')
        body.append(f'<text x="{X0-14}" y="{f(y+5)}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{t["horizon"] if hh == 18 else t["dim"]}">{lab}</text>')
    body.append(f'<text x="{X0-14}" y="{YT+5}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{t["dim"]}">DAWN</text>')
    # grid: months
    for m, lab in [(6, "JUN"), (7, "JUL"), (8, "AUG"), (9, "SEP"), (10, "OCT"), (11, "NOV")]:
        x = X(datetime(2026, m, 1))
        body.append(f'<line x1="{f(x)}" y1="{YT}" x2="{f(x)}" y2="{YB}" stroke="{t["rule"]}" stroke-width="1" stroke-dasharray="2 6"/>')
        body.append(f'<text x="{f(x+8)}" y="{YB+26}" font-family="{MONO}" font-size="14" letter-spacing="2" fill="{t["dim"]}">{lab}</text>')

    # background field (faint, not data)
    rnd = seeded("sky-field")
    for _ in range(140):
        x, y = rnd.uniform(X0, X1), rnd.uniform(YT, YH)
        body.append(f'<circle cx="{f(x)}" cy="{f(y)}" r=".5" fill="{t["faint"]}" opacity=".6"/>')

    # constellations: commits from one sitting
    rnd = seeded("jitter")
    pts = []
    for dt, lines in commits:
        pts.append((X(dt) + rnd.uniform(-2.6, 2.6), Y(dt), dt, lines))
    seg = []
    for a, b in zip(pts, pts[1:]):
        if (b[2] - a[2]) <= timedelta(minutes=50):
            seg.append(f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}")
    body.append(f'<path d="{"".join(seg)}" fill="none" stroke="{t["cyan"]}" stroke-width=".7" opacity="{.5 if t["paper"] else .32}"/>')

    # stars
    stars_small, stars_big = [], []
    rnd = seeded("stars")
    for x, y, dt, lines in pts:
        r = min(5.2, 1.0 + 0.95 * math.log10(1 + lines))
        night = y < YH
        c = rnd.choice(t["star"][:3]) if r < 3 else (t["gold"] if rnd.random() < .6 else t["cyan"])
        o = (0.95 if night else 0.55) if not t["paper"] else (0.9 if night else 0.6)
        cls = ""
        if rnd.random() < 0.14:
            cls = f' class="tw" style="animation-delay:-{rnd.uniform(0, 6):.2f}s;animation-duration:{rnd.uniform(3, 7):.2f}s"'
        el = f'<circle{cls} cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{c}" opacity="{o}"/>'
        (stars_big if r >= 3 else stars_small).append(el)
    body.append("".join(stars_small))
    body.append(f'<g filter="url(#gs)">{"".join(stars_big)}</g>')

    # region labels
    n = len(commits)
    dark = sum(1 for dt, _ in commits if dt.hour >= 18 or dt.hour < 5)
    body.append(
        f'<text x="{X1}" y="{YT-12}" text-anchor="end" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{t["ink"]}">AFTER DARK  ·  {dark} COMMITS</text>'
        f'<text x="{X1-14}" y="{YB-16}" text-anchor="end" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{t["dim"]}">DAYLIGHT  ·  {n-dark}</text>'
        f'<text x="{X0+10}" y="{f(YH+22)}" font-family="{SERIF}" font-style="italic" font-size="17" fill="{t["horizon"]}">sunset</text>'
    )
    # peak hour annotation
    by_hour = Counter(dt.hour for dt, _ in commits)
    ph, pc = by_hour.most_common(1)[0]
    yph = Y(datetime(2026, 1, 1, ph, 30))
    body.append(
        f'<line x1="{X1+4}" y1="{f(yph)}" x2="{X1+14}" y2="{f(yph)}" stroke="{t["gold"]}" stroke-width="2"/>'
        f'<text x="{X1+20}" y="{f(yph-4)}" font-family="{MONO}" font-size="12" fill="{t["gold"]}">{ph:02d}h</text>'
        f'<text x="{X1+20}" y="{f(yph+11)}" font-family="{MONO}" font-size="12" fill="{t["gold"]}">peak</text>'
    )

    # light curve (commits per week)
    LT, LB = 575, 675
    wk = Counter(((dt - start).days // 7) for dt, _ in commits)
    nweeks = math.ceil((end - start).days / 7)
    mx = max(wk.values())
    cp = []
    for i in range(nweeks):
        x = X(start + timedelta(days=7 * i + 3.5))
        y = LB - wk.get(i, 0) / mx * (LB - LT)
        cp.append((x, y))
    cp = [(X0, LB)] + cp + [(X1, LB)]
    line = smooth(cp)
    body.append(f'<line x1="{X0}" y1="{LB}" x2="{X1}" y2="{LB}" stroke="{t["rule"]}" stroke-width="1"/>')
    body.append(f'<path d="{line}L{X1} {LB}L{X0} {LB}Z" fill="url(#curve)"/>')
    body.append(f'<path d="{line}" fill="none" stroke="{t["gold"]}" stroke-width="2.2" filter="url(#gs)"/>')
    pk = max(range(nweeks), key=lambda i: wk.get(i, 0))
    pkx = X(start + timedelta(days=7 * pk + 3.5))
    pky = LB - wk[pk] / mx * (LB - LT)
    body.append(
        f'<circle cx="{f(pkx)}" cy="{f(pky)}" r="4" fill="{t["gold"]}"/>'
        f'<text x="{f(pkx-12)}" y="{f(pky-4)}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{t["gold"]}">brightest week · {wk[pk]} commits</text>'
        f'<text x="{X0-14}" y="{LT+12}" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{t["dim"]}">LIGHT</text>'
        f'<text x="{X0-14}" y="{LT+28}" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{t["dim"]}">CURVE</text>'
    )

    # header and caption
    body.append(
        f'<text x="56" y="56" font-family="{MONO}" font-size="15" letter-spacing="4.5" fill="{t["dim"]}">PLATE III  ·  SKY CHART, JUNE TO NOVEMBER 2026</text>'
        f'<text x="{W-56}" y="56" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="20" fill="{t["ink"]}">Every point is one real commit.</text>'
        f'<line x1="56" y1="76" x2="{W-56}" y2="76" stroke="{t["rule"]}" stroke-width="1"/>'
        f'<text x="56" y="{H-30}" font-family="{SANS}" font-size="16" fill="{t["dim"]}">'
        f"{n} commits, plotted by day and by hour (IST), with night at the top. Size follows lines changed; faint lines join commits made in one sitting.</text>"
    )
    return frame(W, H, t, f"Sky chart: {n} commits from June to November 2026 plotted by date and hour; {dark} of them ({round(100*dark/n)}%) were made between 18:00 and 05:00 IST. Peak hour {ph:02d}:00.", "".join(body), defs, TWINKLE)


# ───────────────────────────── PLATE IV · ORRERY ─────────────────────────────
def orrery(t: dict) -> str:
    W, H = 1200, 720
    CX, CY = 600, 392
    orbits = [(175, 66), (318, 120), (462, 174)]
    defs, bg = sky_bg(W, H, t, "skyo")
    defs += glow_filter("go", 4) + glow_filter("gc", 14)

    def P(i: int, deg: float) -> tuple[float, float]:
        rx, ry = orbits[i]
        return CX + rx * math.cos(math.radians(deg)), CY + ry * math.sin(math.radians(deg))

    def ellipse_path(i: int) -> str:
        rx, ry = orbits[i]
        return f"M{CX-rx} {CY}A{rx} {ry} 0 1 1 {CX+rx} {CY}A{rx} {ry} 0 1 1 {CX-rx} {CY}"

    body = [bg, scatter_stars(W, H, t, 160, "orr-field", twinkle=0.22)]
    for i in range(3):
        rx, ry = orbits[i]
        body.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" fill="none" stroke="{t["faint"]}" stroke-width="1.1" opacity=".9"/>')
    # comets: traffic on each orbit
    for i, (dur, col) in enumerate([(13, t["cyan"]), (21, t["violet"]), (31, t["gold"])]):
        for k in range(2):
            body.append(
                f'<circle r="2.6" fill="{col}" filter="url(#go)"><animateMotion dur="{dur}s" begin="-{k*dur/2:.1f}s" repeatCount="indefinite" path="{ellipse_path(i)}"/></circle>'
            )
    # the star at the centre
    sun_core = t["gold"]
    body.append(
        f'<circle cx="{CX}" cy="{CY}" r="30" fill="{sun_core}" opacity=".35" filter="url(#gc)"><animate attributeName="r" values="26;34;26" dur="5s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{CX}" cy="{CY}" r="15" fill="{sun_core}"/>'
        f'<circle cx="{CX}" cy="{CY}" r="7" fill="{t["sky0"] if t["paper"] else "#fff6e0"}" opacity="{.5 if t["paper"] else .9}"/>'
        f'<text x="{CX}" y="{CY-30}" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{t["ink"]}">LLM GATEWAY</text>'
        f'<text x="{CX}" y="{CY+40}" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{t["dim"]}">routing · caching · fallbacks</text>'
    )

    planets = [
        # (orbit, angle, radius, colour, name, callout xy, anchor, lines)
        (2, 208, 21, t["gold"], "Reports", (56, 128), "start",
         ["Plain English in, SQL out.", "Shows a preview, then waits for", "an admin to confirm. Never runs alone."]),
        (1, 322, 15, t["violet"], "Knowledge", (W - 56, 128), "end",
         ["Answers from each agency's own", "documents and pages, scoped to", "who is asking, grounded or silent."]),
        (0, 152, 17, t["cyan"], "Intake", (56, 600), "start",
         ["Long application forms, as a", "conversation: personas, risk flags,", "and every answer synced to the CRM."]),
    ]
    for oi, deg, r, col, name, (tx, ty), anchor, lines in planets:
        px, py = P(oi, deg)
        gid = f"pl{name}"
        hx = 30 if px < CX else 70
        defs += (
            f'<radialGradient id="{gid}" cx="{hx}%" cy="35%" r="75%"><stop offset="0" stop-color="{t["ink"] if not t["paper"] else "#ffffff"}" stop-opacity=".9"/>'
            f'<stop offset=".35" stop-color="{col}"/><stop offset="1" stop-color="{t["sky0"]}" stop-opacity=".9"/></radialGradient>'
        )
        # leader line to callout
        lx = tx + (150 if anchor == "start" else -150)
        ly = ty + (104 if ty < 300 else -30)
        body.append(f'<path d="M{f(px)} {f(py)}L{f(lx)} {f(ly)}" stroke="{col}" stroke-width="1" stroke-dasharray="3 4" opacity=".75"/>')
        body.append(f'<circle cx="{f(lx)}" cy="{f(ly)}" r="2.5" fill="{col}"/>')
        if name == "Reports":
            body.append(f'<ellipse cx="{f(px)}" cy="{f(py)}" rx="{r*1.9}" ry="{r*0.55}" fill="none" stroke="{col}" stroke-width="2" opacity=".8" transform="rotate(-14 {f(px)} {f(py)})"/>')
        body.append(f'<circle cx="{f(px)}" cy="{f(py)}" r="{r}" fill="url(#{gid})" filter="url(#go)"/>')
        # a moon
        body.append(
            f'<g><circle cx="{f(px + r + 11)}" cy="{f(py)}" r="3" fill="{t["ink"]}" opacity=".85"/>'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {f(px)} {f(py)}" to="360 {f(px)} {f(py)}" dur="{7 + r/3:.1f}s" repeatCount="indefinite"/></g>'
        )
        # callout
        body.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" font-family="{SERIF}" font-size="30" fill="{t["ink"]}">{name}</text>')
        body.append(f'<text x="{tx}" y="{ty}" dy="0" text-anchor="{anchor}" font-family="{SANS}" font-size="17" fill="{t["dim"]}">'
                    + "".join(f'<tspan x="{tx}" dy="{26 if j else 32}">{esc(s)}</tspan>' for j, s in enumerate(lines)) + "</text>")
        body.append(f'<circle cx="{tx + (-14 if anchor == "start" else 14)}" cy="{ty-10}" r="5" fill="{col}"/>')

    # platform callout, bottom right
    tx, ty = W - 56, 600
    body.append(
        f'<text x="{tx}" y="{ty}" text-anchor="end" font-family="{SERIF}" font-size="30" fill="{t["ink"]}">Underneath</text>'
        f'<text text-anchor="end" font-family="{SANS}" font-size="17" fill="{t["dim"]}">'
        f'<tspan x="{tx}" y="{ty+32}">One chat API; the token picks the bot</tspan>'
        f'<tspan x="{tx}" y="{ty+58}">and the tenant. AWS CDK, Lambda, RDS,</tspan>'
        f'<tspan x="{tx}" y="{ty+84}">Redis, SQS, WebSockets; 3 US regions.</tspan></text>'
    )

    body.append(
        f'<text x="56" y="56" font-family="{MONO}" font-size="15" letter-spacing="4.5" fill="{t["dim"]}">PLATE IV  ·  ORRERY</text>'
        f'<text x="{W-56}" y="56" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="20" fill="{t["ink"]}">The system those nights went into.</text>'
        f'<line x1="56" y1="76" x2="{W-56}" y2="76" stroke="{t["rule"]}" stroke-width="1"/>'
    )
    return frame(W, H, t, "Orrery of a multi-tenant AI platform: an LLM gateway at the centre with three assistants in orbit. Reports turns plain English into SQL and waits for an admin to confirm. Knowledge answers from each agency's own documents. Intake turns long forms into a conversation synced to the CRM. Underneath: AWS CDK, Lambda, RDS, Redis, SQS and WebSockets across three US regions.", "".join(body), defs, TWINKLE)


# ───────────────────────────── PLATE V · SPECTRA ─────────────────────────────
EXTRA: dict[str, list[str]] = {}
SKIP = {"Leadership & practice"}
SHORT = {
    "Machine learning & data science": "Machine learning",
    "Vision, audio & documents": "Vision, audio & docs",
    "Desktop, edge & automation": "Desktop, edge & automation",
    "Observability & security": "Observability & security",
}
FEATURED = {
    "Languages": "Python · TypeScript · SQL · Bash",
    "AI & LLM systems": "Claude · OpenRouter · RAG · text-to-SQL",
    "Backend & APIs": "FastAPI · Pydantic · JWT · WebSockets",
    "Data stores & SQL": "MySQL · Redis · SQLAlchemy · sqlglot",
    "Cloud & infrastructure": "AWS CDK · Lambda · SQS · RDS",
    "Frontend": "React · Preact · Vite",
    "Testing & quality": "pytest · Playwright · Vitest · Ruff",
}
RAINBOW = ["#7a2cff", "#3d4dff", "#00a8ff", "#00d4b0", "#5ee05a", "#ffe24a", "#ff9a2e", "#ff3d3d"]


def load_inventory() -> list[tuple[str, list[str]]]:
    out = []
    for line in (DATA / "inventory.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \*\*(.+?)\.\*\* (.*)", line.strip())
        if not m or m.group(1) in SKIP:
            continue
        items = [x.strip() for x in m.group(2).split(", ") if x.strip()]
        items += EXTRA.get(m.group(1), [])
        out.append((m.group(1), items))
    return out


def lerp_hex(a: str, b: str, u: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * u):02x}" for x, y in zip(ca, cb))


def rainbow_at(u: float) -> str:
    u = min(max(u, 0), 1) * (len(RAINBOW) - 1)
    i = min(int(u), len(RAINBOW) - 2)
    return lerp_hex(RAINBOW[i], RAINBOW[i + 1], u - i)


def spectra(t: dict, inv: list[tuple[str, list[str]]]) -> str:
    total = sum(len(v) for _, v in inv)
    RH = 60
    W, H = 1200, 136 + RH * len(inv) + 56
    SX0, SX1 = 372, 820
    defs, bg = sky_bg(W, H, t, "skyp")
    defs += glow_filter("gl", 1.6)
    defs += '<linearGradient id="rb" x1="0" x2="1">' + "".join(
        f'<stop offset="{i/(len(RAINBOW)-1):.3f}" stop-color="{c}"/>' for i, c in enumerate(RAINBOW)) + "</linearGradient>"
    defs += (
        f'<linearGradient id="scan" x1="0" x2="1"><stop offset="0" stop-color="{t["ink"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{t["ink"]}" stop-opacity="{.10 if t["paper"] else .16}"/><stop offset="1" stop-color="{t["ink"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="strips">'
        + "".join(f'<rect x="{SX0}" y="{136 + i*RH}" width="{SX1-SX0}" height="24" rx="3"/>' for i in range(len(inv)))
        + "</clipPath>"
    )
    body = [bg]
    body.append(
        f'<text x="56" y="56" font-family="{MONO}" font-size="15" letter-spacing="4.5" fill="{t["dim"]}">PLATE V  ·  SPECTRA</text>'
        f'<text x="{W-56}" y="56" text-anchor="end" font-family="{SERIF}" font-style="italic" font-size="20" fill="{t["ink"]}">Every line is one technology in this work.</text>'
        f'<line x1="56" y1="76" x2="{W-56}" y2="76" stroke="{t["rule"]}" stroke-width="1"/>'
        f'<text x="56" y="112" font-family="{SERIF}" font-size="26" fill="{t["ink"]}">{total} technologies across {len(inv)} domains, in this codebase</text>'
        f'<text x="{SX0}" y="112" dx="0" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{t["faint"]}"></text>'
        f'<text x="{SX0}" y="{H-74}" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{t["dim"]}">400 nm</text>'
        f'<text x="{SX1}" y="{H-74}" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{t["dim"]}">700 nm</text>'
    )
    for i, (dom, items) in enumerate(inv):
        y = 136 + i * RH
        label = SHORT.get(dom, dom)
        body.append(
            f'<text x="56" y="{y+18}" font-family="{SANS}" font-size="19" font-weight="600" fill="{t["ink"]}">{esc(label)}</text>'
            f'<text x="{SX0-18}" y="{y+18}" text-anchor="end" font-family="{MONO}" font-size="16" fill="{t["gold"]}">{len(items)}</text>'
            f'<text x="{SX1+22}" y="{y+18}" font-family="{SANS}" font-size="16" fill="{t["dim"]}">{esc(FEATURED.get(dom, ""))}</text>'
        )
        if t["paper"]:
            body.append(f'<rect x="{SX0}" y="{y}" width="{SX1-SX0}" height="24" rx="3" fill="url(#rb)" opacity=".62"/>')
        else:
            body.append(f'<rect x="{SX0}" y="{y}" width="{SX1-SX0}" height="24" rx="3" fill="{t["strip"]}" stroke="{t["rule"]}"/>')
        lines = []
        for name in items:
            rnd = seeded(dom, name)
            u = rnd.random() ** 0.95
            x = SX0 + 4 + u * (SX1 - SX0 - 8)
            sw = rnd.choice([1.1, 1.4, 1.8, 2.4, 3.0])
            if t["paper"]:
                lines.append(f'<line x1="{f(x)}" y1="{y}" x2="{f(x)}" y2="{y+24}" stroke="{t["ink"]}" stroke-width="{sw}" opacity="{rnd.uniform(.55, .95):.2f}"/>')
            else:
                c = rainbow_at((x - SX0) / (SX1 - SX0))
                lines.append(f'<line x1="{f(x)}" y1="{y+1}" x2="{f(x)}" y2="{y+23}" stroke="{c}" stroke-width="{sw}" opacity="{rnd.uniform(.7, 1):.2f}"/>')
        body.append(f'<g{"" if t["paper"] else " filter=\"url(#gl)\""}>{"".join(lines)}</g>')
    # spectrograph scan
    body.append(
        f'<g clip-path="url(#strips)"><rect x="-120" y="0" width="120" height="{H}" fill="url(#scan)">'
        f'<animate attributeName="x" values="{SX0-120};{SX1}" dur="7s" repeatCount="indefinite"/></rect></g>'
    )
    body.append(
        f'<text x="56" y="{H-30}" font-family="{SANS}" font-size="16" fill="{t["dim"]}">'
        f"Line positions are a fingerprint, not a score. The full list is under the plate, as text.</text>"
    )
    return frame(W, H, t, f"Spectra: {total} technologies across {len(inv)} domains, each domain drawn as an emission spectrum with one line per technology.", "".join(body), defs)


# ───────────────────────────── PLATE VI · DAWN ─────────────────────────────
def dawn(t: dict) -> str:
    W, H = 1200, 250
    defs = (
        f'<linearGradient id="dawn" x1="0" y1="0" x2="0" y2="1">'
        + (
            f'<stop offset="0" stop-color="{t["sky0"]}"/><stop offset=".55" stop-color="{t["sky1"]}"/><stop offset="1" stop-color="#ead7b4"/>'
            if t["paper"] else
            '<stop offset="0" stop-color="#03040d"/><stop offset=".45" stop-color="#16184a"/><stop offset=".78" stop-color="#7a3a5c"/><stop offset="1" stop-color="#f19a5b"/>'
        )
        + "</linearGradient>"
        f'<radialGradient id="sun"><stop offset="0" stop-color="{t["gold"]}"/><stop offset=".55" stop-color="{t["gold"]}" stop-opacity=".9"/><stop offset="1" stop-color="{t["gold"]}" stop-opacity="0"/></radialGradient>'
    )
    defs += glow_filter("gd", 10)
    body = [f'<rect width="{W}" height="{H}" fill="url(#dawn)"/>', scatter_stars(W, H, t, 90, "dawn-field", ymax=110, twinkle=0.35)]
    body.append(
        f'<g><circle cx="{W/2}" cy="232" r="70" fill="url(#sun)" filter="url(#gd)"/>'
        f'<circle cx="{W/2}" cy="232" r="38" fill="{t["gold"]}"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 18;0 0;0 18" dur="12s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>'
    )
    body.append(f'<path d="M0 {H}V214C260 204 420 210 600 207C800 204 960 200 {W} 210V{H}Z" fill="{t["ground"]}"/>')
    body.append(
        f'<text x="{W/2}" y="92" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="34" fill="{t["ink"] if t["paper"] else "#fff4e4"}">Lights off at dawn. Shipped by morning.</text>'
        f'<text x="{W/2}" y="132" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{t["dim"] if t["paper"] else "#e8c9b6"}">END OF LOG  ·  PLATE VI</text>'
    )
    return frame(W, H, t, "Dawn over the horizon: lights off at dawn, shipped by morning.", "".join(body), defs, TWINKLE)


def main() -> None:
    commits = load_commits()
    dark = sum(1 for dt, _ in commits if dt.hour >= 18 or dt.hour < 5)
    pct = round(100 * dark / len(commits))
    inv = load_inventory()
    for name, t in THEMES.items():
        out = ROOT / "assets" / name
        out.mkdir(parents=True, exist_ok=True)
        plates = {
            "hero.svg": hero(t),
            "magnitudes.svg": magnitudes(t, len(commits), pct),
            "sky.svg": sky_chart(t, commits),
            "orrery.svg": orrery(t),
            "spectra.svg": spectra(t, inv),
            "dawn.svg": dawn(t),
        }
        for fn, svg in plates.items():
            (out / fn).write_text(svg, encoding="utf-8")
    print(f"{len(commits)} commits, {pct}% after dark, {sum(len(v) for _, v in inv)} technologies in {len(inv)} domains")


if __name__ == "__main__":
    main()
