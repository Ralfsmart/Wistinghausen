"""Erzeugt die HTML-Gerüste aller Seiten aus einer gemeinsamen Vorlage.

Kopf, Menü und Fußzeile stehen so nur an einer Stelle. Die eigentlichen Inhalte
kommen zur Laufzeit aus /inhalt/*.json (siehe js/site.js) und werden über /admin gepflegt.
Nur nötig, wenn sich Menü, Seitenaufbau oder Impressum/Datenschutz ändern.
Aufruf:  python werkzeuge/seiten_erzeugen.py
"""
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
TEILE = Path(__file__).resolve().parent / "teile"
VERSION = "8"  # bei Änderungen an CSS/JS erhöhen, damit Browser neu laden

MENUE = [
    ("Start", "index.html", "start"),
    ("Küchen", "kuechen.html", "kuechen"),
    ("Möbel", "moebel.html", "moebel"),
    ("Innenausbau", "innenausbau.html", "innenausbau"),
    ("Türen", "tueren.html", "tueren"),
    ("Außen", "aussen.html", "aussen"),
    ("Fässer", "faesser.html", "faesser"),
    ("Kontakt", "index.html#kontakt", "kontakt"),
]

KONTAKT = """
<div class="strip wood" aria-hidden="true"></div>
<section class="wrap" id="kontakt" style="padding-top:48px">
  <h2>Kontakt</h2>
  <div class="contact">
    <div><h3 data-firma="name"></h3><p><span data-firma="strasse"></span><br><span data-firma="ort"></span></p></div>
    <div><h3>Werkstatt</h3><p><span data-firma="werkstatt_strasse"></span><br><span data-firma="werkstatt_ort"></span></p></div>
    <div><h3>Telefon</h3><p><a data-firma-tel="telefon" data-firma="telefon" href="#"></a><br>Mobil <a data-firma-tel="mobil" data-firma="mobil" href="#"></a></p></div>
    <div><h3>E-Mail</h3><p><a data-firma-mail data-firma="email" href="#"></a></p></div>
  </div>
</section>"""


def seite(datei, titel, kennung, hauptteil, beschreibung=""):
    def eintrag(name, ziel, icon):
        aktiv = ' aria-current="page"' if ziel == datei else ""
        return (f'        <li><a href="{ziel}"{aktiv}><span class="ni" style="background-image:url(icons/{icon}.svg?v={VERSION})"'
                f' aria-hidden="true"></span>{name}</a></li>')
    menue = "\n".join(eintrag(*m) for m in MENUE)
    html = f"""<!doctype html>
<html lang="de" data-basis="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
<meta name="description" content="{beschreibung}">
<meta name="robots" content="noindex"><!-- Entwurf: vor dem Livegang entfernen -->
<link rel="stylesheet" href="css/style.css?v={VERSION}">
<script src="js/site.js?v={VERSION}" defer></script>
</head>
<body class="nav-badges" data-seite="{kennung}">

<header class="site wood">
  <div class="wrap top">
    <a class="brand" href="index.html">
      <img src="bilder/Wappen-2.gif" alt="Wappen der Schreinerei">
      <div><b>Schreinerei Wistinghausen</b><span data-firma="zusatz">Meisterbetrieb</span></div>
    </a>
    <button class="menu-btn" aria-expanded="false" onclick="const n=document.querySelector('nav.main');this.setAttribute('aria-expanded',n.classList.toggle('open'))">☰ Menü</button>
    <nav class="main" aria-label="Hauptmenü">
      <ul>
{menue}
      </ul>
    </nav>
  </div>
</header>

{hauptteil}

<footer class="wood">
  <div class="wrap">
    <span>© <span data-firma="name">Schreinerei Arnim v. Wistinghausen</span> · <span data-firma="zusatz">Meisterbetrieb</span></span>
    <span><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></span>
  </div>
</footer>
</body>
</html>
"""
    (WURZEL / datei).write_text(html, encoding="utf-8")
    print("erzeugt:", datei)


NOSCRIPT = '<noscript><p class="note">Bitte JavaScript aktivieren, um die Inhalte zu sehen.</p></noscript>'

if __name__ == "__main__":
    seite("index.html", "Schreinerei Wistinghausen – Meisterbetrieb", "start",
          f'<main class="wrap" id="inhalt">{NOSCRIPT}</main>\n{KONTAKT}',
          "Schreinerei Arnim v. Wistinghausen – Küchen, Möbel, Innenausbau, Türen, Außenholzbau und Rührfässer.")
    for name, datei, kennung in MENUE[1:7]:
        seite(datei, f"{name} – Schreinerei Wistinghausen", kennung,
              f'<main class="wrap rubrik" id="inhalt">{NOSCRIPT}</main>')
    for datei, titel in [("impressum.html", "Impressum"), ("datenschutz.html", "Datenschutz")]:
        teil = (TEILE / datei).read_text(encoding="utf-8")
        seite(datei, f"{titel} – Schreinerei Wistinghausen", "text", teil)
