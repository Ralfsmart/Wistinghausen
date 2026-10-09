"""Erzeugt alle HTML-Seiten aus der Vorlage und den Inhalten in /inhalt/*.json.

Die Inhalte werden fest in die Seiten geschrieben, damit Suchmaschinen sie ohne JavaScript lesen
können. js/site.js setzt sie im Browser zusätzlich frisch ein (so sind Änderungen aus dem
Admin-Bereich sofort sichtbar, auch bevor die Seiten neu erzeugt wurden).

Läuft automatisch bei jeder Änderung auf GitHub (.github/workflows/website.yml).
Vor einem FTP-Upload einmal von Hand ausführen:  python werkzeuge/seiten_erzeugen.py
"""
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

WURZEL = Path(__file__).resolve().parent.parent
INHALT = WURZEL / "inhalt"

# ---- Einstellungen ---------------------------------------------------------------------------
ADRESSE = "https://ralfsmart.github.io/Wistinghausen/"   # beim Umzug: "https://www.schreinerei-wistinghausen.de/"
ENTWURF = True        # True = Suchmaschinen aussperren (noindex). Zum Livegang auf False setzen.
VERSION = "17"        # bei Änderungen an CSS/JS erhöhen, damit Browser neu laden
FIRMENNAME_KURZ = "Schreinerei Wistinghausen"

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
RUBRIKEN = [kennung for _, _, kennung in MENUE[1:7]]
TEXTSEITEN = ["impressum", "datenschutz"]


def laden(name):
    return json.loads((INHALT / f"{name}.json").read_text(encoding="utf-8"))


FIRMA = laden("firma")


# ---- Textformatierung (gleiche Regeln wie in js/site.js) -------------------------------------
def esc(text):
    return html.escape(str(text or ""), quote=True)


def tel_link(nummer):
    return "tel:" + re.sub(r"[^\d+]", "", str(nummer or ""))


def zeile(text):
    h = esc(text)
    h = re.sub(r'\b(https?://[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])', r'<a href="\1" rel="noopener">\1</a>', h)
    h = re.sub(r'(^|[\s(])(www\.[\w-]+\.[^\s<“”"]*[^\s<.,;:!?)“”"])', r'\1<a href="https://\2" rel="noopener">\2</a>', h)

    def platzhalter(m):
        k = m.group(1)
        if k not in FIRMA:
            return m.group(0)
        w = esc(FIRMA[k])
        if k in ("telefon", "mobil"):
            return f'<a href="{tel_link(FIRMA[k])}">{w}</a>'
        if k == "email":
            return f'<a href="mailto:{w}">{w}</a>'
        return w

    h = re.sub(r"\{([a-z_]+)\}", platzhalter, h)
    h = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", h)
    return re.sub(r"==(.+?)==", r'<mark class="todo">\1</mark>', h)


def absaetze(text):
    teile = []
    for block in [b for b in re.split(r"\n\s*\n", str(text or "").strip()) if b]:
        zeilen = block.split("\n")
        if all(re.match(r"^\s*- ", z) for z in zeilen):
            teile.append("<ul>" + "".join(f"<li>{zeile(re.sub(r'^\s*- ', '', z))}</li>" for z in zeilen) + "</ul>")
        else:
            teile.append("<p>" + "<br>".join(zeile(z) for z in zeilen) + "</p>")
    return "".join(teile)


def firma_einsetzen(seite_html):
    """Füllt Elemente mit data-firma / data-firma-tel / data-firma-mail (wie firmaEinsetzen in site.js)."""
    seite_html = re.sub(
        r'<(\w+)([^>]*?\sdata-firma="(\w+)"[^>]*)>[^<]*</\1>',
        lambda m: f'<{m.group(1)}{m.group(2)}>{esc(FIRMA.get(m.group(3), ""))}</{m.group(1)}>',
        seite_html)

    def link(m):
        tag = m.group(0)
        tel = re.search(r'data-firma-tel="(\w+)"', tag)
        if tel:
            return tag.replace('href="#"', f'href="{tel_link(FIRMA.get(tel.group(1)))}"')
        if "data-firma-mail" in tag:
            return tag.replace('href="#"', f'href="mailto:{esc(FIRMA.get("email"))}"')
        return tag

    return re.sub(r"<a\b[^>]*>", link, seite_html)


# ---- Inhalte der einzelnen Seitentypen (Markup wie in js/site.js) ----------------------------
def startseite(d):
    fotos = "".join(f'<img src="{esc(b["datei"])}" alt="{esc(b.get("titel"))}">' for b in d.get("fotos", [])[:6])
    punkte = "".join(f"<li>{esc(p)}</li>" for p in d.get("abschnitt_punkte", []) if p)
    return f"""
      <section class="hero">
        <h1>{esc(d.get("hero_titel"))}</h1>
        <p>{esc(d.get("hero_text"))}</p>
        <a class="btn" data-firma-tel="telefon" href="#"><span data-firma="telefon"></span> anrufen</a>
        <a class="btn ghost" href="#kontakt">Kontakt</a>
      </section>
      <section class="split">
        <div>
          <h2>{esc(d.get("abschnitt_titel"))}</h2>
          {absaetze(d.get("abschnitt_text"))}
          {f"<ul>{punkte}</ul>" if punkte else ""}
        </div>
        <div class="photos">{fotos}</div>
      </section>
      {besonderheit(d)}
      {ueber_mich(d)}"""


def erstes_foto(liste):
    return next((b for b in (liste or []) if b and b.get("datei")), None)


def besonderheit(d):
    if not d.get("besonderheit_titel"):
        return ""
    foto = erstes_foto(d.get("besonderheit_fotos"))
    bild = f'<img src="{esc(foto["datei"])}" alt="{esc(foto.get("titel"))}">' if foto else ""
    link = (f'<a class="btn" href="{esc(d["besonderheit_link"])}">{esc(d["besonderheit_link_text"])}</a>'
            if d.get("besonderheit_link") and d.get("besonderheit_link_text") else "")
    return f"""
      <section class="besonders">
        {bild}
        <div>
          <h2>{esc(d.get("besonderheit_titel"))}</h2>
          {absaetze(d.get("besonderheit_text"))}
          {link}
        </div>
      </section>"""


def ueber_mich(d):
    if not d.get("ueber_titel") and not d.get("ueber_text"):
        return ""
    foto = erstes_foto(d.get("ueber_fotos"))
    bild = ""
    if foto:
        unterschrift = f'<figcaption>{esc(foto.get("titel"))}</figcaption>' if foto.get("titel") else ""
        bild = f'<figure><img src="{esc(foto["datei"])}" alt="{esc(foto.get("titel"))}">{unterschrift}</figure>'
    return f"""
      <section class="ueber" id="ueber-mich">
        {bild}
        <div>
          <h2>{esc(d.get("ueber_titel"))}</h2>
          {absaetze(d.get("ueber_text"))}
        </div>
      </section>"""


def bild_karte(b):
    titel = f'<b>{esc(b.get("titel"))}</b>' if b.get("titel") else ""
    unterschrift = (f'<figcaption>{titel}{esc(b.get("beschreibung"))}</figcaption>'
                    if b.get("titel") or b.get("beschreibung") else "")
    return f"""
      <figure>
        <button type="button" data-voll="{esc(b["datei"])}" aria-label="Foto vergrößern: {esc(b.get("titel"))}">
          <img src="{esc(b["datei"])}" alt="{esc(b.get("titel"))}" loading="lazy">
        </button>
        {unterschrift}
      </figure>"""


def rubrik(kennung, d):
    leistungen = "".join(f"<li>{esc(l)}</li>" for l in d.get("leistungen", []) if l)
    bilder = "".join(bild_karte(b) for b in d.get("bilder", []) if b.get("datei"))
    hinweis = ('<p class="note">Beispieltext: Bitte an die eigene Arbeitsweise anpassen und danach im Admin-Bereich '
               'den Haken bei „Beispieltext“ entfernen.</p>') if d.get("beispieltext") else ""
    untertitel = f'<p class="lead">{esc(d.get("untertitel"))}</p>' if d.get("untertitel") else ""
    liste = f'<aside class="r-list"><h2>Leistungen</h2><ul>{leistungen}</ul></aside>' if leistungen else ""
    galerie = (f'<h2>Einblicke</h2><p class="galerie-hinweis">Für Details einfach auf ein Foto klicken oder tippen.</p><div class="galerie">{bilder}</div>'
               if bilder else "")
    return f"""
      <div class="r-head">
        <span class="r-icon" style="background-image:url(icons/{kennung}.svg)" aria-hidden="true"></span>
        <div>
          <h1>{esc(d.get("titel"))}</h1>
          {untertitel}
        </div>
      </div>
      {hinweis}
      <div class="r-body">
        <div class="r-text">{absaetze(d.get("einleitung"))}</div>
        {liste}
      </div>
      {galerie}
      <section class="cta">
        <span class="cta-leiste wood" aria-hidden="true"></span>
        <div><h2 data-firma="aufruf_titel"></h2><p data-firma="aufruf_text"></p></div>
        <div class="cta-knoepfe">
          <a class="btn" data-firma-tel="telefon" href="#"><span data-firma="telefon"></span></a>
          <a class="btn ghost" data-firma-mail href="#">E-Mail schreiben</a>
        </div>
      </section>"""


def textseite(d):
    teile = []
    for a in d.get("abschnitte", []):
        if a.get("ueberschrift"):
            teile.append(f'<h2>{esc(a.get("ueberschrift"))}</h2>')
        teile.append(absaetze(a.get("text")))
    hinweis = f'<p class="note">{esc(d.get("hinweis"))}</p>' if d.get("hinweis") else ""
    stand = f'<p><em>Stand: {esc(d.get("stand"))}</em></p>' if d.get("stand") else ""
    return f"""
      <h1>{esc(d.get("titel"))}</h1>
      {hinweis}
      {"".join(teile)}
      {stand}"""


KONTAKT = """
<div class="strip wood" aria-hidden="true"></div>
<section class="wrap" id="kontakt" style="padding-top:48px">
  <h2>Kontakt</h2>
  <div class="kontakt-reihe">
  <div class="contact">
    <div><h3 data-firma="name"></h3><p><span data-firma="strasse"></span><br><span data-firma="ort"></span></p></div>
    <div><h3>Werkstatt</h3><p><span data-firma="werkstatt_strasse"></span><br><span data-firma="werkstatt_ort"></span></p></div>
    <div><h3>Telefon</h3><p><a data-firma-tel="telefon" data-firma="telefon" href="#"></a><br>Mobil <a data-firma-tel="mobil" data-firma="mobil" href="#"></a></p></div>
    <div><h3>E-Mail</h3><p><a data-firma-mail data-firma="email" href="#"></a></p></div>
  </div>
  <figure class="anfahrt">
    <img src="bilder/anfahrt.svg" width="800" height="560" loading="lazy"
         alt="Anfahrtsskizze: von der B31-Ausfahrt Uhldingen-Mühlhofen über die Bahnhofstraße nach Mühlhofen zur Unteren Weitfeld Straße">
    <figcaption><a href="{KARTE}" target="_blank" rel="noopener">Route zur Schreinerei v. Wistinghausen in Google Maps ↗</a></figcaption>
  </figure>
  </div>
</section>"""


# ---- Strukturierte Firmendaten für Google (schema.org) ---------------------------------------
def firmendaten_json_ld():
    plz_ort = re.match(r"\s*(\d{5})\s+(.+)", FIRMA.get("ort", ""))
    daten = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": FIRMA.get("name"),
        "description": "Schreinerei und Meisterbetrieb: Küchen, Möbel, Innenausbau, Türen, Außenholzbau und Rührfässer.",
        "url": ADRESSE,
        "logo": ADRESSE + "bilder/Wappen-2.gif",
        "image": ADRESSE + "bilder/kueche-6.JPG",
        "telephone": FIRMA.get("telefon"),
        "email": FIRMA.get("email"),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": FIRMA.get("strasse"),
            "postalCode": plz_ort.group(1) if plz_ort else "",
            "addressLocality": plz_ort.group(2) if plz_ort else FIRMA.get("ort"),
            "addressCountry": "DE",
        },
    }
    # "</" darf im Skript-Block nicht vorkommen
    return json.dumps(daten, ensure_ascii=False, indent=2).replace("</", "<\\/")


# ---- Seitengerüst ----------------------------------------------------------------------------
def seite(datei, kennung, titel, beschreibung, hauptteil, zusatz_kopf=""):
    def eintrag(name, ziel, icon):
        aktiv = ' aria-current="page"' if ziel == datei else ""
        return (f'        <li><a href="{ziel}"{aktiv}><span class="ni" style="background-image:url(icons/{icon}.svg?v={VERSION})"'
                f' aria-hidden="true"></span>{name}</a></li>')

    menue = "\n".join(eintrag(*m) for m in MENUE)
    url = ADRESSE + ("" if datei == "index.html" else datei)
    robots = '<meta name="robots" content="noindex">' if ENTWURF else ""
    inhalt = f"""<!doctype html>
<html lang="de" data-basis="">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titel)}</title>
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="description" content="{esc(beschreibung)}">
{robots}
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="{FIRMENNAME_KURZ}">
<meta property="og:title" content="{esc(titel)}">
<meta property="og:description" content="{esc(beschreibung)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{ADRESSE}bilder/kueche-6.JPG">
<link rel="stylesheet" href="css/style.css?v={VERSION}">
<script src="js/site.js?v={VERSION}" defer></script>{zusatz_kopf}
</head>
<body class="nav-badges" data-seite="{kennung}">

<header class="site wood">
  <div class="wrap top">
    <a class="brand" href="index.html">
      <img src="bilder/Wappen-2.gif" alt="Wappen der Schreinerei">
      <div><b>{FIRMENNAME_KURZ}</b><span data-firma="zusatz"></span></div>
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
    <span>© <span data-firma="name"></span> · <span data-firma="zusatz"></span></span>
    <span><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></span>
  </div>
</footer>
</body>
</html>
"""
    (WURZEL / datei).write_text(firma_einsetzen(inhalt), encoding="utf-8")
    print("erzeugt:", datei)


def seo(d, titel_auto, beschreibung_auto):
    return (d.get("seo_titel") or titel_auto).strip(), (d.get("seo_beschreibung") or beschreibung_auto or "").strip()


if __name__ == "__main__":
    # Startseite
    d = laden("start")
    titel, beschr = seo(d, f"{FIRMENNAME_KURZ} – Schreiner-Meisterbetrieb am Bodensee", d.get("hero_text"))
    ld = f'\n<script type="application/ld+json">\n{firmendaten_json_ld()}\n</script>'
    karte = "https://www.google.com/maps/search/?api=1&amp;query=" + quote_plus(f"{FIRMA.get('name')}, {FIRMA.get('strasse')}, {FIRMA.get('ort')}")
    kontakt = KONTAKT.replace("{KARTE}", karte)
    seite("index.html", "start", titel, beschr, f'<main class="wrap" id="inhalt">{startseite(d)}\n</main>\n{kontakt}', ld)

    # Rubriken
    for kennung in RUBRIKEN:
        d = laden(kennung)
        titel, beschr = seo(d, f"{d.get('titel')} | {FIRMENNAME_KURZ}", d.get("untertitel"))
        seite(f"{kennung}.html", kennung, titel, beschr, f'<main class="wrap rubrik" id="inhalt">{rubrik(kennung, d)}\n</main>')

    # Impressum, Datenschutz
    for kennung in TEXTSEITEN:
        d = laden(kennung)
        seite(f"{kennung}.html", kennung, f"{d.get('titel')} | {FIRMENNAME_KURZ}",
              f"{d.get('titel')} der {FIRMA.get('name')}", f'<main class="wrap legal" id="inhalt">{textseite(d)}\n</main>')

    # Seitenübersicht und robots.txt für Suchmaschinen
    heute = date.today().isoformat()
    seiten = ["index.html"] + [f"{k}.html" for k in RUBRIKEN + TEXTSEITEN]
    urls = "\n".join(f"  <url><loc>{ADRESSE}{'' if s == 'index.html' else s}</loc><lastmod>{heute}</lastmod></url>"
                     for s in seiten)
    (WURZEL / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8")
    regeln = "Disallow: /" if ENTWURF else "Disallow: /admin/\nDisallow: /werkzeuge/"
    (WURZEL / "robots.txt").write_text(f"User-agent: *\n{regeln}\n\nSitemap: {ADRESSE}sitemap.xml\n", encoding="utf-8")
    print("erzeugt: sitemap.xml, robots.txt")
