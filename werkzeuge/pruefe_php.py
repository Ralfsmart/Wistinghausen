"""Prüft, ob der PHP-Generator (admin/seiten.php) dasselbe erzeugt wie der Python-Generator.

Die Inhalte werden dazu in ein Testverzeichnis kopiert und mit absichtlich schwierigen Texten ergänzt
(Anführungszeichen, &, Links, Aufzählungen, Formatierung, leere und fehlende Felder).

Aufruf:  python werkzeuge/pruefe_php.py            (PHP wird im PATH oder per winget-Ordner gesucht)
         set PHP=C:\\pfad\\php.exe & python werkzeuge/pruefe_php.py
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent


def php_finden():
    """Sucht php.exe: Umgebungsvariable PHP, dann der winget-Paketordner, dann PATH."""
    if os.environ.get("PHP"):
        return os.environ["PHP"]
    muster = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\PHP.PHP.*\php.exe")
    treffer = sorted(glob.glob(muster))
    if treffer:
        return treffer[-1]
    gefunden = shutil.which("php")
    if gefunden:
        return gefunden
    sys.exit("PHP nicht gefunden (Umgebungsvariable PHP setzen).")


SCHWIERIG = {
    "start": {
        "hero_titel": 'Titel mit "Anführungszeichen" & <Spitzklammern> und \'Apostroph\'',
        "hero_text": "",
        "abschnitt_text": (
            "Absatz mit **fett**, *kursiv*, ++unterstrichen++ und ==Markierung==.\n\n"
            "- Punkt eins\n- Punkt **zwei**\n- Punkt {telefon}\n\n"
            "Link https://www.gesetze-im-internet.de/hwo/ und www.example.de, E-Mail {email}.\n"
            "Zweite Zeile mit 5 * 3 = 15 und ***beides***.\n\n\n"
            "   Absatz nach vielen Leerzeilen   "
        ),
        "abschnitt_punkte": ["Eins & zwei", "", "Drei \"vier\""],
        "fotos": [{"datei": "bilder/a b.jpg", "titel": "Titel \"mit\" Zeichen"}, {"datei": "bilder/c.jpg"}],
        "besonderheit_titel": "Kasten",
        "besonderheit_text": "Text im Kasten",
        "besonderheit_link": "faesser.html",
        "besonderheit_link_text": "Mehr",
        "besonderheit_fotos": [{"datei": "bilder/k.jpg", "titel": "K"}],
        "ueber_titel": "Über mich",
        "ueber_text": "Ich bin **Arnim**.\n\n==Hier ergänzen==",
        "ueber_fotos": [{"datei": "bilder/p.jpg", "titel": "Porträt"}, {"datei": "bilder/b.jpg"}, {"datei": "bilder/zuviel.jpg"}],
        "seo_titel": "  Eigener Titel  ",
        "seo_beschreibung": "Eigene Beschreibung mit \"Zeichen\"",
    },
    "kuechen": {
        "beispieltext": True,
        "untertitel": "Untertitel – mit Gedankenstrich & Zeichen",
        "einleitung": "Erster Absatz.\n\n- a\n- b\n\nLetzter Absatz mit {mobil} und {unbekannt}.",
        "leistungen": ["Eins", "", "Zwei & drei"],
        "bilder": [
            {"datei": "bilder/x.jpg", "titel": "Mit Titel", "beschreibung": "Mit \"Beschreibung\""},
            {"datei": "bilder/y.jpg", "titel": "", "beschreibung": "Nur Beschreibung"},
            {"datei": "bilder/z.jpg"},
            {"datei": ""},
        ],
    },
    "moebel": {"beispieltext": False, "untertitel": "", "einleitung": "", "leistungen": [], "bilder": []},
    "impressum": {
        "titel": "Impressum",
        "hinweis": "",
        "abschnitte": [
            {"ueberschrift": "Ohne Text", "text": ""},
            {"ueberschrift": "", "text": "Nur Text mit {name} und {ort}"},
            {"ueberschrift": "Liste", "text": "- Eins\n- Zwei"},
        ],
        "stand": "Oktober 2026",
    },
}


def main():
    php = php_finden()
    temp = Path(tempfile.mkdtemp(prefix="pruefe_php_"))
    try:
        projekt = temp / "projekt"
        (projekt / "werkzeuge").mkdir(parents=True)
        (projekt / "admin").mkdir()
        shutil.copy(WURZEL / "werkzeuge" / "seiten_erzeugen.py", projekt / "werkzeuge")
        shutil.copy(WURZEL / "admin" / "seiten.php", projekt / "admin")
        shutil.copy(WURZEL / "einstellungen.json", projekt)
        shutil.copytree(WURZEL / "inhalt", projekt / "inhalt")

        # schwierige Inhalte einmischen
        for name, felder in SCHWIERIG.items():
            pfad = projekt / "inhalt" / f"{name}.json"
            d = json.loads(pfad.read_text(encoding="utf-8"))
            d.update(felder)
            pfad.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        # Firmendaten mit Sonderzeichen
        pfad = projekt / "inhalt" / "firma.json"
        f = json.loads(pfad.read_text(encoding="utf-8"))
        f.update({"zusatz": "Meisterbetrieb seit 2004", "name": "Müller & Söhne \"Holzbau\"", "ort": "88690 Uhldingen-Mühlhofen"})
        pfad.write_text(json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")

        py_aus, php_aus = temp / "py", temp / "php"
        py_aus.mkdir()
        php_aus.mkdir()
        subprocess.run([sys.executable, str(projekt / "werkzeuge" / "seiten_erzeugen.py"), "--ziel", str(py_aus)],
                       check=True, capture_output=True)
        # "-f ... --" statt direkter Skriptangabe: unter Windows verweigert Python sonst den Start
        r = subprocess.run([php, "-f", str(projekt / "admin" / "seiten.php"), "--", str(php_aus)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("PHP-Fehler:\n" + r.stdout + r.stderr)

        abweichend = 0
        for datei in sorted(os.listdir(py_aus)):
            a = (py_aus / datei).read_bytes().replace(b"\r\n", b"\n")
            b = (php_aus / datei).read_bytes()
            if a == b:
                print(f"gleich      {datei}")
            else:
                abweichend += 1
                print(f"ABWEICHUNG  {datei}")
                za, zb = a.decode("utf-8").split("\n"), b.decode("utf-8").split("\n")
                n = 0
                for i, (x, y) in enumerate(zip(za, zb), 1):
                    if x != y:
                        print(f"   Zeile {i}\n     py : {x[:200]}\n     php: {y[:200]}")
                        n += 1
                        if n >= 3:
                            break
                if len(za) != len(zb):
                    print(f"   Zeilenzahl: py {len(za)}, php {len(zb)}")
        # Live-Modus (kein noindex, robots erlaubt)
        sys.exit(1 if abweichend else 0)
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
