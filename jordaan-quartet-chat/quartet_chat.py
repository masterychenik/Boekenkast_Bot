#!/usr/bin/env python3
"""Jordaan Kwartet chat: vier personages, elk met een eigen SLM via Ollama."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Persona:
    name: str
    voice: str
    system: str
    model: str
    temperature: float = 0.7


def default_personas(model: str) -> list[Persona]:
    return [
        Persona(
            name="Jaap",
            voice="de nuchteraar",
            model=model,
            temperature=0.3,
            system=(
                "Je bent Jaap, de nuchteraar van het Kwartet. Je reageert kort, zakelijk en "
                "met feiten. Je corrigeert onzin zakelijk maar vriendelijk. Antwoord in het "
                "Nederlands, maximaal 3 zinnen."
            ),
        ),
        Persona(
            name="Truus",
            voice="de verteller",
            model=model,
            temperature=0.9,
            system=(
                "Je bent Truus, de verteller van het Kwartet. Je vertelt warme anekdotes in "
                "Amsterdamse stijl, met een knipoog, en reageert op wat de anderen zeiden. "
                "Antwoord in het Nederlands, maximaal 4 zinnen."
            ),
        ),
        Persona(
            name="Piet",
            voice="de technicus",
            model=model,
            temperature=0.5,
            system=(
                "Je bent Piet, de technicus van het Kwartet. Je legt uit hoe dingen technisch "
                "werken (SLM's, modellen, prompts) en reageert op de technische kant van het "
                "gesprek. Antwoord in het Nederlands, maximaal 4 zinnen."
            ),
        ),
        Persona(
            name="Sien",
            voice="de samenvatter",
            model=model,
            temperature=0.8,
            system=(
                "Je bent Sien, de samenvatter van het Kwartet. Je reageert emotioneel, vat samen "
                "wat de anderen zeiden en eindigt met een korte conclusie. Antwoord in het "
                "Nederlands, maximaal 3 zinnen."
            ),
        ),
    ]


def ollama_chat(base_url: str, model: str, messages: list[dict], temperature: float) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"].strip()


def transcript_messages(persona: Persona, transcript: list[dict]) -> list[dict]:
    msgs = [{"role": "system", "content": persona.system}]
    for entry in transcript:
        if entry["speaker"] == "Gebruiker":
            msgs.append({"role": "user", "content": f"[Gebruiker] {entry['content']}"})
        else:
            msgs.append({"role": "assistant", "content": f"[{entry['speaker']}] {entry['content']}"})
    msgs.append(
        {"role": "user", "content": f"Nu ben jij aan de beurt, {persona.name}. Reageer op het bovenstaande."}
    )
    return msgs


def mock_chat(persona: Persona, transcript: list[dict]) -> str:
    last = transcript[-1]["content"][:60] if transcript else ""
    return f"(mock) Typisch {persona.voice}: reactie op {last!r}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Vier personages, elk met een eigen SLM, in één chat.")
    p.add_argument("--topic", help="Eerste bericht om het gesprek te starten (anders interactief).")
    p.add_argument("--rounds", type=int, default=2, help="Hoe vaak het Kwartet om de beurt reageert (standaard 2).")
    p.add_argument("--model", default="mistral", help="Standaardmodel voor alle personages (standaard: mistral).")
    p.add_argument(
        "--models",
        help="Elk personage een eigen model: 'jaap=mistral,truus=gemma3,piet=llama3.2,sien=qwen2.5'",
    )
    p.add_argument("--base-url", default="http://localhost:11434", help="Ollama API-adres.")
    p.add_argument("--mock", action="store_true", help="Testmodus zonder Ollama.")
    p.add_argument("--export", metavar="PAD", help="Schrijf de transcript als JSON naar PAD bij afsluiten.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    personas = default_personas(args.model)

    if args.models:
        for item in args.models.split(","):
            name, sep, model = item.partition("=")
            if not sep:
                continue
            for persona in personas:
                if persona.name.lower() == name.strip().lower():
                    persona.model = model.strip()

    print("=== Jordaan Kwartet Chat ===")
    for persona in personas:
        print(f"  - {persona.name} ({persona.voice}) -> model: {persona.model}")
    if args.mock:
        print("  [MOCK-MODUS: geen echte Ollama-calls]")
    print("Typ 'exit' om te stoppen.\n")

    code, transcript = run_chat(args, personas)
    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump({"messages": transcript}, f, ensure_ascii=False, indent=2)
        print(f"Transcript geschreven naar {args.export}")
    return code


def run_chat(args: argparse.Namespace, personas: list[Persona]) -> tuple[int, list[dict]]:
    transcript: list[dict] = []
    topic = args.topic

    while True:
        if topic is not None:
            text, topic = topic, None
        else:
            try:
                text = input("Jij: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nTot ziens!")
                return 0, transcript
            if not text:
                continue
            if text.lower() in {"exit", "quit", "stop"}:
                print("Tot ziens!")
                return 0, transcript

        transcript.append({"speaker": "Gebruiker", "content": text})
        print(f"\n[Gebruiker] {text}")

        for _ in range(args.rounds):
            for persona in personas:
                if args.mock:
                    reply = mock_chat(persona, transcript)
                else:
                    try:
                        reply = ollama_chat(
                            args.base_url,
                            persona.model,
                            transcript_messages(persona, transcript),
                            persona.temperature,
                        )
                    except (urllib.error.URLError, OSError) as exc:
                        print(
                            f"\nFout: kan Ollama niet bereiken op {args.base_url} ({exc}).\n"
                            "Draait Ollama? Start het met `ollama serve` en pull een model met "
                            "`ollama pull <model>`. Of test met --mock."
                        )
                        return 1, transcript
                    except (KeyError, json.JSONDecodeError) as exc:
                        print(f"\nFout: onverwacht antwoord van Ollama: {exc}")
                        return 1, transcript
                transcript.append({"speaker": persona.name, "content": reply})
                print(f"[{persona.name} | {persona.model}] {reply}")


if __name__ == "__main__":
    sys.exit(main())
