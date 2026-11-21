# BibBob (Boekenkast_Bot)

Chatbot met vier boekenkasten als wetenschappers, elk met een eigen specialisme. De flow:

1. **FAQ eerst**: past een FAQ-item bij de vraag, dan komt daar direct het antwoord vandaan.
2. **Geen FAQ-item?** Dan komen de vier kasten bij elkaar en overleggen ze welk specialisme de vraag raakt (elke kast telt treffers in zijn eigen boeken).
3. **De kast van het winnende specialisme blijft** en beantwoordt de vraag én alle vervolgvragen binnen dat specialisme.
4. **Eigen specialisme-SLM**: elke kast leest alleen uit zijn eigen kennis (`items` in `content.json`) — in deze statische versie zijn dat de eigen boeken/trefwoorden van de kast als specialisme-kennisbron.

## Content

Alle inhoud staat in `content.json`: `faq` (korte vragen met klaarstaande antwoorden) en `kasten` (per domein: `naam`, `kast_naam`, `hallo` en `items` met vraag `v`, trefwoorden `k` en antwoord `a`).

## Domeinen

- Kast Geesje: Studentgegevens
- Kast Vera: Resultaatverwerking
- Kast Cees: Certificeren
- Kast Didi: Diplomeren

Antwoorden met `[VUL IN: ...]` zijn placeholders die nog worden ingevuld.

## Draaien

`index.html` is een statische single-file app. Na een wijziging in `content.json`:

    python3 build.py        # herbouwt het INHOUD-blok in index.html
    python3 build.py --check
    python3 test_bot.py     # spiegelt de solve-logica en test haar (exit 0 = geslaagd)
