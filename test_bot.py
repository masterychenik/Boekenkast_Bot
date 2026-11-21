#!/usr/bin/env python3
"""Tests voor BibBob (Boekenkast_Bot).

Bootst de solve-logica van index.html na in Python:
- FAQ eerst: best scorende FAQ-item -> direct antwoord (FAQ-kaart).
- Vervolgvraag binnen het specialisme van de actieve kast -> die kast blijft.
- Anders: consult van alle vier de kasten -> kast met beste match wint en blijft.
- Geen match -> open kast houdt zijn vragen aan, anders fallback.

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

def kast_score(sleutel: str, vraag: str, data):
    """Beste match van één kast op de vraag: (score, item) of None."""
    w = words(vraag)
    if not w:
        return None
    beste = None
    for item in data["kasten"][sleutel]["items"]:
        score = sum(1 for k in item["k"] if raak(w, k))
        if score > 0 and (beste is None or score > beste[0]):
            beste = (score, item)
    return beste

# De kast die het laatst een antwoord gaf; vervolgvragen blijven daar.
laatste_kast = None

def reset():
    global laatste_kast
    laatste_kast = None

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
    global laatste_kast
    faq = faq_oplossing(vraag, data)
    kast_res = kast_oplossing(vraag, data)
    # 1. FAQ eerst, maar alleen bij sterke match (score >= 2)
    #    of als geen enkele kast iets vindt.
    if faq and (faq[0] >= 2 or kast_res is None):
        laatste_kast = None
        return {"bron": "faq", "a": faq[1]["a"]}
    # 2. Vervolgvraag binnen het specialisme van de actieve kast:
    #    die kast blijft en antwoordt uit eigen boeken.
    if laatste_kast:
        eigen = kast_score(laatste_kast, vraag, data)
        if eigen:
            return {"bron": "vervolg", "kast": laatste_kast, "a": eigen[1]["a"]}
    # 3. Geen FAQ: consult van alle vier de kasten; beste kast wint en blijft.
    if kast_res:
        laatste_kast = kast_res[0]
        return {"bron": "consult", "kast": kast_res[0], "a": kast_res[1]["a"]}
    # 4. Nergens een match.
    if laatste_kast:
        return {"bron": "vervolg-geen", "kast": laatste_kast, "a": None}
    return {"bron": "fallback", "a": None}

def main() -> int:
    data = laad()
    fouten = []

    # 1. Alle FAQ-items worden door de FAQ zelf beantwoord.
    for item in data["faq"]:
        reset()
        r = solve(item["v"], data)
        if r["bron"] != "faq" or r["a"] != item["a"]:
            fouten.append(f"FAQ '{item['v']}' -> {r}")

    # 2. Alle kast-vragen landen na het consult bij de eigen kast.
    for sleutel, kast in data["kasten"].items():
        for item in kast["items"]:
            reset()
            r = solve(item["v"], data)
            if r["bron"] == "faq":
                fouten.append(f"Kast-vraag '{item['v']}' ging naar de FAQ: {r['a'][:40]}")
            elif r["bron"] != "consult" or r.get("kast") != sleutel:
                fouten.append(f"Kast '{sleutel}' vraag '{item['v']}' -> {r}")

    # 3. Trefwoorden matchen in de eigen voorbeeldvraag (woord of woordbegin).
    for sleutel, kast in data["kasten"].items():
        for item in kast["items"]:
            w = words(item["v"])
            if not any(raak(w, k) for k in item["k"]):
                fouten.append(f"Trefwoorden matchen niet in eigen vraag: {item['v']}")

    # 4. Vervolgvraag binnen het specialisme: de actieve kast blijft.
    reset()
    r = solve("Hoe werkt certificeren?", data)
    if r["bron"] != "consult" or r.get("kast") != "certificeren":
        fouten.append(f"Eerste certificeren-vraag -> {r}")
    r = solve("Wie geeft een certificaat af?", data)
    if r["bron"] != "vervolg" or r.get("kast") != "certificeren":
        fouten.append(f"Vervolgvraag certificeren -> {r} (verwacht vervolg bij certificeren)")
    # Vraag over een ander domein -> nieuwe consult, kast wisselt.
    r = solve("Wanneer krijgt een student een diploma?", data)
    if r["bron"] != "consult" or r.get("kast") != "diplomeren":
        fouten.append(f"Wissel naar diplomeren -> {r} (verwacht consult bij diplomeren)")
    # Vraag zonder match blijft in de actieve kast.
    r = solve("xyzzy flonk blarp", data)
    if r["bron"] != "vervolg-geen" or r.get("kast") != "diplomeren":
        fouten.append(f"Onzin als vervolgvraag -> {r} (verwacht vervolg-geen bij diplomeren)")

    # 5. Onzin zonder actieve kast -> fallback.
    reset()
    r = solve("xyzzy flonk blarp", data)
    if r["bron"] != "fallback":
        fouten.append(f"Onzin-vraag -> {r['bron']} (verwacht fallback)")

    # 6. Fallback-teksten aanwezig.
    if len(data.get("fallback", [])) < 1:
        fouten.append("Geen fallback-teksten in content.json")

    # 7. Elke kast-sleutel heeft een toneel-element "kast_<sleutel>" in index.html,
    #    en de scène-code gebruikt kastId() (geen direct best.kast als element-id).
    pad = HIER / "index.html"
    if pad.exists():
        html = pad.read_text(encoding="utf-8")
        for sleutel in data["kasten"]:
            if f'id="kast_{sleutel}"' not in html:
                fouten.append(f"index.html mist toneel-element voor kast '{sleutel}'")
        if "getElementById(best.kast)" in html or "kastAan(best.kast" in html:
            fouten.append("index.html gebruikt best.kast direct als element-id; gebruik kastId()")
        for kenmerk in ["laatsteKast", "kastKnoppen(", "kastScore(", "overleggen"]:
            if kenmerk not in html:
                fouten.append(f"index.html mist council/vervolgvraag-functionaliteit: {kenmerk}")
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