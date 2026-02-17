#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI
load_dotenv()

# --- ÁLLÍTHATÓ BEÁLLÍTÁSOK ---
MODEL = "gpt-4.1-nano"   # teszt: "gpt-4.1-nano", éles: "gpt-5.2"
#MODEL = "gpt-5.2"
TEMPERATURE = 0.0        # determinisztikusabb kimenethez
# ----------------------------


INSTRUCTIONS = """\
Feladat: A megadott HTML-t teljes egészében fordítsd le magyarról angolra úgy, hogy a HTML szerkezete, a tagek, attribútumok, linkek (href/src), id/class nevek, data-* attribútumok, JavaScript, CSS, kódrészletek és kódfence-ek (pl. <pre><code>…</code></pre>) változatlanok maradjanak.

SZIGORÚ SZABÁLYOK:
1) Csak a természetes nyelvű magyar szöveget, szöveges konstansokat és megjegyzéseket fordítsd angolra.
2) Ne módosítsd a HTML struktúrát: ne adj hozzá / ne vegyél el tageket, ne rendezz át semmit.
3) Ne módosíts semmilyen URL-t, fájlnevet, útvonalat, query paramétert, e-mail címet, telefonszámot.
4) Ne módosíts JS kódot, inline scriptet, CSS-t, semmilyen javascript programkódot kivéve a példákat.
5) Kódrészletnek számít bármi a <script>…</script>, <style>…</style>, valamint <pre>, <code>, <kbd>, <samp> elemekben van. Ezeket érintetlenül hagyod.
6) A <textarea>...</textarea> elemekben található példakódokban a magyar nyelv megjegyéseket és a magyar nyelvű szöveges konstansokat fordítsd le angolra.
7) A fordítás legyen természetes, semleges angol, szakmai szövegnél pontos terminológiával.
8) NEM készítesz kivonatot, NEM hagysz ki mondatot. Minden magyar mondatnak legyen angol megfelelője.
9) A kimenet kizárólag a teljes, lefordított HTML legyen, semmilyen magyarázatot ne írj. A kimenet a standard <!doctype html>-el kezdődjön, ahogy az eredeti.
"""

def translate_html(client: OpenAI, html: str) -> str:
    # Biztonságos delimiterek, hogy a modell "egyben" kezelje a bemenetet
    user_input = f"<<<HTML\n{html}\nHTML\n"

    resp = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,  # system/developer jellegű üzenet
        input=user_input,
        temperature=TEMPERATURE,
        # Ha túl nagy a HTML és nem fér be, alapból 400-at kaphatsz.
        # Ha inkább vágjon a bemenet elejéből (nem ideális fordításhoz), állítsd:
        # truncation="auto",
    )

    text = getattr(resp, "output_text", None)
    if not text:
        raise RuntimeError("Nincs resp.output_text (üres válasz vagy nem szöveges kimenet).")

    return text

def main() -> int:
    if len(sys.argv) != 3:
        print("Használat: python translate_html.py input.html output.html", file=sys.stderr)
        return 2

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Hiba: nincs beállítva az OPENAI_API_KEY környezeti változó.", file=sys.stderr)
        return 2

    html = in_path.read_text(encoding="utf-8")

    client = OpenAI(api_key=api_key)
    translated = translate_html(client, html)

    out_path.write_text(translated, encoding="utf-8")
    print(f"Kész: {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
