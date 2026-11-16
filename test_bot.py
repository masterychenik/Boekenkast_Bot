#!/usr/bin/env python3
"""Tests voor Boekenkast_Bot.

Bootst de solve-logica van index.html na in Python:
- FAQ eerst: best scorende FAQ-item -> direct antwoord (FAQ-kaart).
- Anders kasten: beste item per score -> antwoord uit die kast.
- Moeilijke woorden -> consult-scene (alle kasten, dan antwoord).
- Geen match -> fallback.

Draaien: python3 test_bot.py   (exitcode 0 = geslaagd)
"""
import json
import re
import sys
from pathlib import Path

HIER = Path(__file__).parent

def norm(t: str) -> str:
    t = t.lower()
    t = re.sub(r"[!?.,;:()'\"]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def words(t: str):
    return [w for w in norm(t).split() if len(w) >= 3]

def raak(woordlijst, k: str) -> bool:
    return any(x == k or x.startswith(k) for x in woordlijst)

def laad():
    return json.loads((HIER / "content.json").read_text(encoding="utf-8"))

def is_moeilijk(vraag: str, data) -> bool:
    v = norm(vraag)
    return any(m and m in v for m in data.get("moeilijk", "").split("|"))

def faq_oplossing(vraag: str, data):
    """Best scorende FAQ-item als (score, item), of None."""
    w = words(vraag)
    if not w:
        return None
    beste = None
    for item in data.get("faq", []):
        score = sum(1 for k in item["k"] if raak(w, k))
        if score > 0 and (beste is None or score > beste[0]):
            beste = (score, item)
    return beste

def kast_oplossing(vraag: str, data):
    """Best scorende kast-item over alle kasten, of None."""
    w = words(vraag)
    if not w:
        return None
    beste = None
    for sleutel, kast in data["kasten"].items():
        for item in kast["items"]:
            score = sum(1 for k in item["k"] if raak(w, k))
            if score > 0 and (beste is None or score > beste[0]):
                beste = (score, sleutel, item)
    if beste:
        return beste[1], beste[2]
    return None

def solve(vraag: str, data):
    faq = faq_oplossing(vraag, data)
    kast_res = kast_oplossing(vraag, data)
    # FAQ eerst, maar alleen bij sterke match (score >= 2)
    # of als geen enkele kast iets vindt.
    if faq and (faq[0] >= 2 or kast_res is None):
        return {"bron": "faq", "a": faq[1]["a"]}
    if is_moeilijk(vraag, data):
        return {"bron": "consult", "a": None}
    if kast_res:
        return {"bron": "kast", "kast": kast_res[0], "a": kast_res[1]["a"]}
    return {"bron": "fallback", "a": None}

def main() -> int:
    data = laad()
    fouten = []

    # 1. Alle FAQ-items worden door de FAQ zelf beantwoord.
    for item in data["faq"]:
        r = solve(item["v"], data)
        if r["bron"] != "faq" or r["a"] != item["a"]:
            fouten.append(f"FAQ '{item['v']}' -> {r}")

    # 2. Alle kast-vragen komen uit de eigen kast;
    #    moeilijke items zijn bewust consult (alle kasten denken mee).
    for sleutel, kast in data["kasten"].items():
        for item in kast["items"]:
            if is_moeilijk(item["v"], data):
                continue
            r = solve(item["v"], data)
            if r["bron"] == "faq":
                fouten.append(f"Kast-vraag '{item['v']}' ging naar de FAQ: {r['a'][:40]}")
            elif r["bron"] != "kast" or r.get("kast") != sleutel:
                fouten.append(f"Kast '{sleutel}' vraag '{item['v']}' -> {r}")

    # 3. Trefwoorden matchen in de eigen voorbeeldvraag (woord of woordbegin).
    for sleutel, kast in data["kasten"].items():
        for item in kast["items"]:
            w = words(item["v"])
            if not any(raak(w, k) for k in item["k"]):
                fouten.append(f"Trefwoorden matchen niet in eigen vraag: {item['v']}")

    # 4. Moeilijk woord -> consult, mits de FAQ niet al dekt.
    if not is_moeilijk("waarom is dit zo?", data):
        fouten.append("Moeilijk-woord 'waarom' niet herkend")
    r = solve("Wat is het verschil tussen certificeren en diplomeren?", data)
    if r["bron"] != "consult":
        fouten.append(f"Verschil-vraag -> {r['bron']} (verwacht consult)")

    # 5. Onzin -> fallback.
    r = solve("xyzzy flonk blarp", data)
    if r["bron"] != "fallback":
        fouten.append(f"Onzin-vraag -> {r['bron']} (verwacht fallback)")

    # 6. Fallback-teksten aanwezig.
    if len(data.get("fallback", [])) < 1:
        fouten.append("Geen fallback-teksten in content.json")

    # 7. index.html bevat de actuele content en blijft onder 1 MB.
    pad = HIER / "index.html"
    if pad.exists():
        html = pad.read_text(encoding="utf-8")
        content = (HIER / "content.json").read_text(encoding="utf-8").strip()
        if content not in html:
            fouten.append("index.html bevat niet (meer) de actuele content.json")
        if len(html.encode("utf-8")) > 1_000_000:
            fouten.append("index.html is groter dan 1 MB")
    else:
        fouten.append("index.html bestaat niet")

    if fouten:
        print(f"GEFAALD ({len(fouten)} fouten):")
        for f in fouten:
            print(f"  - {f}")
        return 1
    print("Alle tests geslaagd.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
