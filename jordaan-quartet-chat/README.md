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
```

In de uitvoer zie je per bericht welk model het heeft gegenereerd: `[Piet | llama3.2] ...`.

## Hoe het werkt

- Elke agent krijgt dezelfde chatgeschiedenis (met sprekerslabels `[Naam] ...`) plus zijn eigen system prompt.
- Na jouw bericht reageren de vier personages om de beurt, `rounds` keer, en zien daarbij elkaars reacties — net als een echt kwartet.
- `--models` koppelt per personage een ander Ollama-model, zodat elk karakter echt een eigen SLM heeft.
