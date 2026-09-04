#!/usr/bin/env python3
"""Bygger qr-album/mtf-40-album.html fra malen + optimaliserte bilder i scratchpad.

Bruk: python3 build-album.py <scratchpad-dir> (mappen med web/full, web/thumb, web-manifest.json)
"""
import base64
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRATCH = Path(sys.argv[1])
TEMPLATE = HERE / "mtf-40-album-template.html"
OUT = HERE / "mtf-40-album.html"

manifest = json.load(open(SCRATCH / "web-manifest.json"))

# ── Bildetekster ──────────────────────────────────────────────────────────
PHOTO_CAPS = {
    "pre1991-dscf0054": "Fra fotoarkivet",
    "pre1991-man-uten-henger-ce18311-xt4s7069-copy": "MAN-lastebil CE 18311",
    "pre1991-mtf-bil-gammel-xt4s7070": "MTF-bil av eldre årgang",
    "pre1991-biloppstilling": "Biloppstilling ved terminalen",
    "pre1991-bred-last-i-tunnell-sh-xt4s7067": "Spesialtransport: bred last gjennom tunnel",
    "pre1991-bred-last-med-svens-polis-eskorte-sh-xt4s7068": "Bred last med svensk politieskorte",
    "pre1991-bred-last-med-svensk-polis-sh-xt4s7066": "Bred last med svensk politi",
    "pre1991-bred-last-med-svensk-poliseskorte-sh-xt4s7065": "Bred last med svensk politieskorte",
    "pre1991-daf-uten-henger-ce18311-xt4s7071": "DAF-lastebil CE 18311",
    "pre1991-egenreklame-xt4s8340-copy": "Egenreklame: «Når du likevel kjører forbi på E6 …»",
    "pre1991-forste-bygget-xt4s8332-copy": "Det første bygget",
    "pre1991-gammel-prisliste-1983-xt4s8335-copy": "Prisliste, 1983",
    "pre1991-gammelt-bygg-xt4s7072": "Gammelt bygg",
    "pre1991-jan-tore-vold-hoyang-polaris-xt4s8334-copy": "Jan Tore Vold — Høyang Polaris",
    "pre1991-moss-vogmannsforenings-styre-xt4s8328-copy": "Moss Vognmannsforenings styre",
    "pre1991-mtf-bil-med-henger-xt4s7073": "MTF-bil med henger",
    "pre1991-prisliste-fra-1983-xt4s8345-copy": "Prisliste fra 1983",
    "pre1991-styret-i-transportsentralen-1978-79-xt4s7075": "Styret i Transportsentralen 1978–79",
    "pre1991-styret-i-transportsentralen-sh-1978-79-xt4s7075": "Styret i Transportsentralen 1978–79 (variant)",
    "pre1991-tore-volds-hoyang-bil-xt4s8341": "Tore Volds Høyang-bil",
    "pre1991-transportpriser-xt4s8336-copy": "Transportpriser, gjeldende fra 21. september 1987",
    "pre1991-transportsentralen-as-moss-med-bilpark": "Transportsentralen A/S Moss med bilpark",
}
PHOTO_SUB = {"pre1991": "Fotoalbum · Før 1991", "1991idag": "Fotoalbum · 1991 til i dag"}

MONTHS = ["", "januar", "februar", "mars", "april", "mai", "juni", "juli",
          "august", "september", "oktober", "november", "desember"]

def clip_caption(slug):
    """Avledet bildetekst for utklipp: avis + dato fra filnavnet."""
    m = re.match(r"utklipp-(\d{4})(\d{2})?(\d{2})?-?(.*)", slug)
    year, mo, day, rest = m.groups()
    paper = "Moss Avis"
    if rest and "moss-dagblad" in rest: paper = "Moss Dagblad"
    if rest and "sarpsborg" in rest: paper = "Sarpsborg Arbeiderblad"
    if mo and day and int(mo) >= 1:
        date = f"{int(day)}. {MONTHS[int(mo)]} {year}"
    else:
        date = year
    return paper, date

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def datauri(path):
    return "data:image/webp;base64," + base64.b64encode(path.read_bytes()).decode()

# ── META + FULL ───────────────────────────────────────────────────────────
meta, full, thumbs = {}, {}, {}
for group in ["pre1991", "1991idag", "utklipp"]:
    for item in manifest[group]:
        slug = item["slug"]
        if group == "utklipp":
            paper, date = clip_caption(slug)
            meta[slug] = {"g": "utklipp", "cap": f"{paper}, {date}", "sub": "Faksimile via Nasjonalbiblioteket"}
        else:
            cap = PHOTO_CAPS.get(slug, "Fra fotoarkivet")
            meta[slug] = {"g": group, "cap": cap, "sub": PHOTO_SUB[group]}
        full[slug] = datauri(SCRATCH / "web/full" / f"{slug}.webp")
        thumbs[slug] = datauri(SCRATCH / "web/thumb" / f"{slug}.webp")

html = TEMPLATE.read_text()

# ── {{CLIPS:slug1,slug2}} ────────────────────────────────────────────────
def clips_repl(m):
    slugs = m.group(1).split(",")
    btns = []
    kinds = set()
    for s in slugs:
        s = s.strip()
        if s not in thumbs:
            raise SystemExit(f"Ukjent utklipp-slug i mal: {s}")
        cap = meta[s]["cap"]
        group = meta[s]["g"]
        kind = "utklipp" if group == "utklipp" else "bilde"
        kinds.add(kind)
        btns.append(
            f'<button data-img="{s}" data-group="{group}" aria-label="Vis {kind}: {esc(cap)}">'
            f'<img src="{thumbs[s]}" alt="{esc(cap)}" loading="lazy"></button>'
        )
    n = len(slugs)
    word = "utklippet" if kinds == {"utklipp"} else "bildet"
    hint = f"Trykk på {word} for å {'lese' if word == 'utklippet' else 'se'} det" if n == 1 \
        else ("Trykk på et utklipp for å lese det" if kinds == {"utklipp"} else "Trykk på et bilde for å se det")
    return '<div class="clips">' + "".join(btns) + f'</div><p class="cliphint">{hint}</p>'

html = re.sub(r"\{\{CLIPS:([^}]+)\}\}", clips_repl, html)

# ── {{GALLERY:group}} ────────────────────────────────────────────────────
def gallery_repl(m):
    group = m.group(1)
    cells = []
    for item in manifest[group]:
        s = item["slug"]
        cap = meta[s]["cap"]
        cells.append(
            f'<button data-img="{s}" data-group="{group}" aria-label="Vis bilde: {esc(cap)}">'
            f'<img src="{thumbs[s]}" alt="{esc(cap)}" loading="lazy"></button>'
        )
    return '<div class="grid">' + "".join(cells) + "</div>"

html = re.sub(r"\{\{GALLERY:([^}]+)\}\}", gallery_repl, html)

html = html.replace("{{META_JSON}}", json.dumps(meta, ensure_ascii=False))
html = html.replace("{{FULL_JSON}}", json.dumps(full))

OUT.write_text(html)
print(f"Skrev {OUT} ({OUT.stat().st_size/1e6:.1f} MB), {len(meta)} bilder")
