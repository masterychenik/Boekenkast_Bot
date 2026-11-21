# Jordaan Kwartet Chat

Vier personages — elk met een eigen SLM via [Ollama](https://ollama.com) — die in één chat met elkaar en met jou praten. Elke agent heeft zijn eigen persona (system prompt), temperatuur en optioneel zijn eigen model.

## Personages

| Personage | Rol | Stijl |
|---|---|---|
| Jaap | de nuchteraar | kort, zakelijk, feiten |
| Truus | de verteller | Amsterdamse anekdotes |
| Piet | de technicus | legt techniek uit (SLM's, prompts) |
| Sien | de samenvatter | emotioneel, concludeert |

## Installatie

1. Installeer Ollama: https://ollama.com
2. Pull modellen, bijvoorbeeld: `ollama pull mistral` en `ollama pull llama3.2`
3. Ollama draait meestal automatisch als service; handmatig: `ollama serve`

De script gebruikt alleen de Python-standaardbibliotheek — geen `pip install` nodig.

## Gebruik

```bash
# Interactief gesprek starten
python3 quartet_chat.py

# Direct met een topic beginnen, 3 rondes
python3 quartet_chat.py --topic "Wat vinden jullie van AI?" --rounds 3

# Ander standaardmodel voor alle vier
python3 quartet_chat.py --model llama3.2

# Elk personage zijn eigen SLM geven
python3 quartet_chat.py --models "jaap=mistral,truus=gemma3,piet=llama3.2,sien=qwen2.5"

# Testmodus zonder Ollama (alleen orchestratie testen)
python3 quartet_chat.py --mock --topic "test" --rounds 1

# Chat opslaan als JSON, daarna visueel afspelen in de browser
python3 quartet_chat.py --topic "Wat vinden jullie van AI?" --export chat.json
# open daarna kwartet-canvas.html in een browser en laad chat.json
```

## Canvas-visualisatie

`kwartet-canvas.html` tekent het gesprek geanimeerd op een HTML5 `<canvas>`: avatar + spraakballon per bericht, met play/pauze, snelheid en de optie om een eigen `--export chat.json` te laden. Werkt met een ingebouwde demo-chat, ook zonder Ollama.

## Op een iPad (of telefoon) draaien

**Visualisatie — werkt offline, geen server nodig:**
1. Zet `kwartet-canvas.html` op je iPad (AirDrop, iCloud Drive/Files-app, of mail het naar jezelf)
2. Open het in Safari — de demo-chat speelt automatisch af; via "Eigen chat laden" laad je een `--export chat.json` in

**Live chat met echte SLM's vanaf de iPad (via Ollama op je Mac,zelfde Wi-Fi):**
1. Op de Mac: `ollama pull mistral` en start Ollama voor het netwerk:
   `OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS=* ollama serve`
   Let op: dit zet een onbeveiligde API open op je Wi-Fi — alleen op een vertrouwd thuisnetwerk. Zonder `OLLAMA_HOST` luistert Ollama standaard alleen op 127.0.0.1.
2. Noteer het IP van de Mac (Systeeminstellingen → Netwerk)
3. Open `kwartet-canvas.html` op de iPad, klap "Live modus" open, vul `http://<mac-ip>:11434` in, kies per personage een model en een onderwerp → ▶ Live starten
4. Werkt `file://` niet? Serveer de map op de Mac: `python3 -m http.server 8000` en open op de iPad `http://<mac-ip>:8000/jordaan-quartet-chat/kwartet-canvas.html`

In de uitvoer zie je per bericht welk model het heeft gegenereerd: `[Piet | llama3.2] ...`.

## Hoe het werkt

- Elke agent krijgt dezelfde chatgeschiedenis (met sprekerslabels `[Naam] ...`) plus zijn eigen system prompt.
- Na jouw bericht reageren de vier personages om de beurt, `rounds` keer, en zien daarbij elkaars reacties — net als een echt kwartet.
- `--models` koppelt per personage een ander Ollama-model, zodat elk karakter echt een eigen SLM heeft.
