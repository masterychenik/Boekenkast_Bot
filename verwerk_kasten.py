#!/usr/bin/env python3
"""Maak webp-plaatjes van de kast-tekeningen en bak ze in index.html.

Werkwijze (draait op een GitHub Actions-runner met Pillow):
- leest img/kast_<domein>.b64 (base64 van de jpg-tekening)
- verwijdert de witte achtergrond (floodfill vanaf de randen, drempel min(RGB) >= 235)
- verkleint naar maximaal 200 px hoog
- slaat op als webp en zet het als data-URI in het KI-blok van index.html
- verwijdert daarna de .b64-bestanden en dit script is eenmalig.
"""
import base64
import io
import json
import re
from collections import deque
from pathlib import Path

from PIL import Image

HIER = Path(__file__).parent
MARK_START = "// ===KI-START==="
MARK_END = "// ===KI-EIND==="
MAX_HOOGTE = 200
DREMPEL = 235

KASTEN = [
    "kast_studentgegevens",
    "kast_resultaatverwerking",
    "kast_certificeren",
    "kast_diplomeren",
]


def wit_weg(img: Image.Image) -> Image.Image:
    """Maak wit dat vanaf de rand bereikbaar is transparant."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    gezien = [[False] * w for _ in range(h)]
    q = deque()

    def wit(p):
        r, g, b, a = px[p]
        return min(r, g, b) >= DREMPEL

    for x in range(w):
        for y in (0, h - 1):
            if wit((x, y)) and not gezien[y][x]:
                gezien[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if wit((x, y)) and not gezien[y][x]:
                gezien[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not gezien[ny][nx] and wit((nx, ny)):
                gezien[ny][nx] = True
                q.append((nx, ny))
    return img


def maak_webp(b64tekst: str) -> str:
    data = base64.b64decode(b64tekst)
    img = Image.open(io.BytesIO(data))
    img = wit_weg(img)
    if img.height > MAX_HOOGTE:
        nw = round(img.width * MAX_HOOGTE / img.height)
        img = img.resize((nw, MAX_HOOGTE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=80, method=6)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> int:
    ki = {}
    for kast in KASTEN:
        pad = HIER / "img" / f"{kast}.b64"
        if not pad.exists():
            print(f"ontbreekt: {pad}", flush=True)
            return 1
        ki[kast] = "data:image/webp;base64," + maak_webp(pad.read_text().strip())
        print(f"{kast}: {len(ki[kast])} bytes data-uri", flush=True)

    htmlpad = HIER / "index.html"
    html = htmlpad.read_text(encoding="utf-8")
    blok = f"{MARK_START}\nconst KI = {json.dumps(ki)};\n{MARK_END}"
    begin, eind = html.find(MARK_START), html.find(MARK_END)
    if begin == -1 or eind == -1:
        print("KI-markers ontbreken in index.html", flush=True)
        return 1
    html = html[:begin] + blok + html[eind + len(MARK_END):]
    htmlpad.write_text(html, encoding="utf-8")
    print(f"index.html nu {len(html.encode('utf-8'))} bytes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
