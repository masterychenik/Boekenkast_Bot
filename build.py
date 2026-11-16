#!/usr/bin/env python3
"""Zet content.json om in het INHOUD-blok van index.html.

Gebruik:
    python3 build.py            # herbouwt index.html uit content.json
    python3 build.py --check    # controleert of index.html actueel is (exit 0/1)
"""
import json
import sys
from pathlib import Path

MARK_START = "// ===INHOUD-START==="
MARK_END = "// ===INHOUD-EIND==="
MAX_BYTES = 1_000_000

def main() -> int:
    hier = Path(__file__).parent
    content = (hier / "content.json").read_text(encoding="utf-8")
    json.loads(content)  # faalt bij ongeldige JSON
    blok = f"{MARK_START}\nconst INHOUD = {content};\n{MARK_END}"

    pad = hier / "index.html"
    html = pad.read_text(encoding="utf-8")
    begin = html.find(MARK_START)
    eind = html.find(MARK_END)
    if begin == -1 or eind == -1:
        print("index.html mist de marker-commentregels.", file=sys.stderr)
        return 1
    nieuw = html[:begin] + blok + html[eind + len(MARK_END):]
    if len(nieuw.encode("utf-8")) > MAX_BYTES:
        print(f"WAARSCHUWING: index.html is {len(nieuw.encode('utf-8'))} bytes, "
              f"boven de limiet van {MAX_BYTES} bytes.", file=sys.stderr)
    if "--check" in sys.argv:
        if nieuw == html:
            print("index.html is actueel.")
            return 0
        print("index.html is NIET actueel; draai build.py.", file=sys.stderr)
        return 1
    pad.write_text(nieuw, encoding="utf-8")
    print(f"index.html herbouwd uit content.json "
          f"({len(nieuw.encode('utf-8'))} bytes).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
